import requests
from bs4 import BeautifulSoup

from utils.utils import setup_logger
import time, re, datetime
from typing import Optional

logger = setup_logger(__name__)


def get_picture_from_liquipedia(player_name):
    try:
        request_url = "https://liquipedia.net/valorant/{}".format(player_name)
        response = requests.get(request_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, features="html.parser")
        image_url = soup.find("meta", attrs={"property": "og:image"})["content"]
        # もしデフォルトの写真の場合は空文字列を返す
        if "facebook-image.png" in image_url:
            return ""
        return image_url
    except Exception as e:
        # liquipediaにアクセスできない場合・ユーザーが存在しない場合などは空文字列を返す
        logger.debug(e)
        return ""
    finally:
        time.sleep(1)


class LiquipediaScraper:
    LIQUIPEDIA_URL_FORMAT = "https://liquipedia.net/valorant/{}"
    REX_BIRTH_DATE = re.compile(r"[a-zA-Z]+ [0-9]+, [0-9]+")
    REX_AGE = re.compile(r"age.([0-9]+)")

    def __init__(self, player_name):
        # liquipediaからページを取得
        try:
            self.request_url = LiquipediaScraper.LIQUIPEDIA_URL_FORMAT.format(
                player_name
            )
            self.response = requests.get(self.request_url)
            self.response.raise_for_status()
            self.soup = BeautifulSoup(self.response.content, features="html.parser")
        except Exception as e:
            # liquipediaにアクセスできない場合・ユーザーが存在しない場合などは空文字列を返す
            logger.debug(e)
        finally:
            time.sleep(1)

        # プロフィール情報を取得して辞書を作成
        try:
            self._profile = {}
            profile_elements = self.soup.find("div", class_="fo-nttax-infobox")
            for content in profile_elements.contents:
                if len(content.contents) >= 2:
                    self._profile[content.contents[0].get_text()] = content.contents[
                        1
                    ].get_text()
        except Exception as e:
            self._profile = None
            logger.debug(e)
        print(self._profile)
        self._image_url = None
        self._description = None

    def get_image_url(self) -> str:
        if self._image_url is None:
            # パースできなかった場合はNoneが返ってくる
            url = self.soup.find("meta", attrs={"property": "og:image"})["content"]
            if "facebook-image.png" in url:  # 画像がデフォルトの場合
                self._image_url = "https://liquipedia.net/commons/images/a/a4/PlayerImagePlaceholder.png"
            elif url is None:  # リンクが取得できない場合
                self._image_url = "https://liquipedia.net/commons/images/a/a4/PlayerImagePlaceholder.png"
            else:
                self._image_url = url
        return self._image_url

    def get_description(self) -> str:
        if self._description is None:
            self._description = self.soup.find(
                "meta", attrs={"property": "og:description"}
            )["content"]
            if self._description is None:
                self._description = ""
        return self._description

    def get_birth_date(self) -> Optional[datetime.date]:
        if "Born:" in self._profile:
            try:
                return datetime.datetime.strptime(
                    self.REX_BIRTH_DATE.search(self._profile["Born:"]).group(),
                    "%B %d, %Y",
                ).date()
            except Exception as e:
                logger.debug(e)
        return None

    def get_age(self) -> Optional[int]:
        if "Born:" in self._profile:
            try:
                print(self._profile["Born:"])
                return int(self.REX_AGE.search(self._profile["Born:"]).group(1))
            except Exception as e:
                logger.debug(e)
        return None

    def get_status(self) -> Optional[str]:
        if "Status:" in self._profile:
            return self._profile["Status:"]
        else:
            return None

    def get_name(self) -> Optional[str]:
        if "Name:" in self._profile:
            return self._profile["Name:"]
        else:
            return None

    def get_team(self) -> Optional[str]:
        if "Team:" in self._profile:
            return self._profile["Team:"]
        else:
            return None

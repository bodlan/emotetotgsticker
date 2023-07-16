import logging
import requests
import json
import sys
import config
from pathlib import Path
from abc import ABC, abstractmethod
from utils import convert_webp_webm, convert_webp_png, check_directories, progressBar

logger = logging.getLogger("run")


class BaseEmote(ABC):
    def __init__(self, url, all_variants: bool = False):
        self.url: str = url
        self.emote_id: str = ""
        self.name: str = ""
        self.animated: bool = False
        self.api_emote_url: str = ""
        self.cdn_url: str = ""
        self.cdn_file_name = ""
        self.filepath = None
        self.all_variants = all_variants

    @classmethod
    @abstractmethod
    def get_emote_details(cls) -> None:
        pass

    @classmethod
    @abstractmethod
    def download_emote(cls) -> None:
        pass

    @classmethod
    @abstractmethod
    def get_emote_id(cls):
        pass

    def process_emote(self):
        self.get_emote_id()
        self.get_emote_details()
        self.download_emote()
        if self.animated:
            convert_webp_webm(self.filepath, self.name)
        else:
            convert_webp_png(self.filepath, self.name)


class SevenTVEmote(BaseEmote):
    def __init__(self, url):
        super().__init__(url)
        self.api_emote_url = "https://7tv.io/v3/emotes/"
        self.cdn_url = "http://cdn.7tv.app/emote/"
        self.cdn_file_name = "4x.webp"

    def get_emote_id(self):
        self.emote_id = self.url.split("/")[-1]

    def get_emote_details(self):
        url = self.api_emote_url + self.emote_id
        response = requests.get(url)
        if response.status_code == 200:
            response_dict = json.loads(response.content.decode("utf-8"))
            self.name = response_dict["name"]
            self.animated = response_dict["animated"]
        else:
            logger.error(f"Failed to get emote name of id: {self.emote_id}. Status code: {response.status_code}")

    def download_emote(self):
        download_url = self.cdn_url + self.emote_id + "/" + self.cdn_file_name
        self.filepath = Path(config.TEMP_FOLDER + self.name + "_" + self.cdn_file_name)
        response = requests.get(download_url)
        if response.status_code == 200:
            with open(self.filepath, "wb") as file:
                file.write(response.content)
            logger.info(f"Emote file with id {self.emote_id} downloaded successfully.")
        else:
            logger.error(f"Failed to download emote file with id {self.emote_id}. Status code:", response.status_code)


class BetterTTVEmote(BaseEmote):
    def __init__(self, url):
        super().__init__(url)
        self.api_emote_url = "https://api.betterttv.net/3/emotes/"
        self.cdn_url = "https://cdn.betterttv.net/emote/"
        self.cdn_file_name = "3x.webp"

    def get_emote_details(self):
        url = self.api_emote_url + self.emote_id
        response = requests.get(url)
        if response.status_code == 200:
            response_dict = json.loads(response.content.decode("utf-8"))
            self.name = response_dict["code"]
            self.animated = response_dict["animated"]
        else:
            logger.error(f"Failed to get emote name of id: {self.emote_id}. Status code: {response.status_code}")

    def download_emote(self):
        download_url = self.cdn_url + self.emote_id + "/" + self.cdn_file_name
        self.filepath = Path(config.TEMP_FOLDER + self.name + "_" + self.cdn_file_name)
        response = requests.get(download_url)
        if response.status_code == 200:
            with open(self.filepath, "wb") as file:
                file.write(response.content)
            logger.info(f"Emote file with id {self.emote_id} downloaded successfully.")
        else:
            logger.error(f"Failed to download emote file with id {self.emote_id}. Status code:", response.status_code)

    def get_emote_id(self):
        self.emote_id = self.url.split("/")[-1]


class FrankFaseZEmote(BaseEmote):
    def __init__(self, url):
        super().__init__(url)
        self.api_emote_url = "https://api.frankerfacez.com/v2/emote/"
        self.cdn_url = "https://cdn.frankerfacez.com/emote/"
        self.cdn_file_name = ""

    def get_emote_details(self):
        url = self.api_emote_url + self.emote_id
        response = requests.get(url)
        if response.status_code == 200:
            response_dict = json.loads(response.content.decode("utf-8"))
            self.name = response_dict["emote"]["name"]
            self.animated = response_dict["emote"]["animated"]
        else:
            logger.error(f"Failed to get emote name of id: {self.emote_id}. Status code: {response.status_code}")

    def download_emote(self):
        if self.animated:
            download_url = self.cdn_url + self.emote_id + "/animated/4"
        else:
            download_url = self.cdn_url + self.emote_id + "/4"
        self.filepath = Path(config.TEMP_FOLDER + self.name + ".webp")
        response = requests.get(download_url)
        if response.status_code == 200:
            with open(self.filepath, "wb") as file:
                file.write(response.content)
            logger.info(f"Emote file with id {self.emote_id} downloaded successfully.")
        else:
            logger.error(f"Failed to download emote file with id {self.emote_id}. Status code:", response.status_code)

    def get_emote_id(self):
        self.emote_id = self.url.split("/")[-1].split("-")[0]


def main():

    urls = []
    urls_file = "emote_links.txt"
    with open(urls_file, "r") as f:
        urls.extend([line.strip() for line in f.readlines()])

    logger.info(f"Links: {urls}")
    if "--all" in sys.argv:
        config.ALL_VARIANTS = True
    if urls:
        check_directories()
    for url in progressBar(urls, prefix="Progress:", suffix="Complete", length=50):
        try:
            if "7tv.app" in url:
                emote = SevenTVEmote(url)
            elif "betterttv.com" in url:
                emote = BetterTTVEmote(url)
            elif "frankerfacez.com" in url:
                emote = FrankFaseZEmote(url)
            else:
                continue
            emote.process_emote()
        except Exception as e:
            logger.exception(f"Exception caught while processing {url}: {e}")


# TODO: add poetry
# TODO: update calling with args
if __name__ == "__main__":
    if sys.argv:
        logger.info(f"Args: {sys.argv}")
    main()

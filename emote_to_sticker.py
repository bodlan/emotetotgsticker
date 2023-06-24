from pathlib import Path
import requests
import json
import sys
from abc import ABC, abstractmethod
from config import TEMP_FOLDER
from utils import convert_webp_webm, convert_webp_png, check_directories


class BaseEmote(ABC):
    def __init__(self, url, all_variants: bool = False):
        self.url: str = url
        self.emote_id: str = ""
        self.name: str = ""
        self.animated: bool = False
        self.api_base_url: str = ""
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
            convert_webp_webm(self.filepath, self.name, self.all_variants)
        else:
            convert_webp_png(self.filepath, self.name)


class SevenTVEmote(BaseEmote):
    def __init__(self, url, all_variants):
        super().__init__(url, all_variants)
        self.api_base_url = "https://7tv.io/v3/"
        self.api_emote_url = self.api_base_url + "emotes"
        self.cdn_url = "http://cdn.7tv.app/emote/"
        self.cdn_file_name = "4x.webp"

    def get_emote_id(self):
        self.emote_id = self.url.split("/")[-1]

    def get_emote_details(self):
        url = self.api_emote_url + "/" + self.emote_id
        response = requests.get(url)
        if response.status_code == 200:
            response_dict = json.loads(response.content.decode("utf-8"))
            self.name = response_dict["name"]
            self.animated = response_dict["animated"]
        else:
            print(f"Fail to get emote name of id: {self.emote_id}. Status code: {response.status_code}")

    def download_emote(self):
        download_url = self.cdn_url + self.emote_id + "/" + self.cdn_file_name
        self.filepath = Path(TEMP_FOLDER + self.name + "_" + self.cdn_file_name)
        response = requests.get(download_url)
        if response.status_code == 200:
            with open(self.filepath, "wb") as file:
                file.write(response.content)
            print(f"Emote file with id {self.emote_id} downloaded successfully.")
        else:
            print(f"Failed to download emote file with id {self.emote_id}. Status code:", response.status_code)


class BetterTTVEmote(BaseEmote):
    def __init__(self, url, all_variants):
        super().__init__(url, all_variants)

    def get_emote_details(self):
        pass

    def download_emote(self):
        pass

    def get_emote_id(self):
        pass


class FrankFaseZEmote(BaseEmote):
    def __init__(self, url, all_variants):
        super().__init__(url, all_variants)

    def get_emote_details(self):
        pass

    def download_emote(self):
        pass

    def get_emote_id(self):
        pass


def main():
    urls = []
    urls_file = "emote_links.txt"
    with open(urls_file, "r") as f:
        urls.extend([line.strip() for line in f.readlines()])
    # clear_file(urls_file)
    print("Links:", urls)
    if "--all" in sys.argv:
        all_variants = True
    else:
        all_variants = False
    if urls:
        check_directories()
    for url in urls:
        try:
            if "7tv.app" in url:
                emote = SevenTVEmote(url, all_variants)
            elif "betterttv.com" in url:
                emote = BetterTTVEmote(url, all_variants)
            elif "frankerfacez.com" in url:
                emote = FrankFaseZEmote(url, all_variants)
            else:
                continue
            emote.process_emote()
        except Exception as e:
            print(f"Exception caught while processing {url}:", e)


# TODO: update on bttv and ffz emotes
# TODO: update calling with args
if __name__ == "__main__":
    if sys.argv:
        print(sys.argv)
    main()

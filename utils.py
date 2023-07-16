import os
import sys
import logging

import ffmpeg
import requests
import re
import config
from pathlib import Path
from PIL import Image
from contextlib import contextmanager

logger = logging.getLogger("run")


def convert_webp_png(filepath, new_file_name):
    canvas_size = (512, 512)
    canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    im = Image.open(filepath).convert("RGBA")
    im_filepath = config.EMOTE_STATIC_FOLDER + new_file_name + ".png"
    height = 240
    width = int(im.width * (height / im.height))
    im_resized = im.resize((width, height), Image.LANCZOS)
    x = (canvas_size[0] - im_resized.width) // 2  # Center the image horizontally
    y = (canvas_size[1] - im_resized.height) // 2  # Center the image vertically
    canvas.paste(im_resized, (x, y), im_resized)
    canvas.save(im_filepath, "png")


def convert_webp_webm(filepath, new_file_name):
    gif_filepath = config.TEMP_FOLDER + new_file_name + ".gif"
    convert_webp_gif(filepath, gif_filepath)
    webm_filepath = config.EMOTE_ANIMATED_FOLDER + new_file_name + "_default" + ".webm"
    config.DEFAULT_FPS = 30
    config.DEFAULT_SMART_DURATION_LIMIT = "2.9"
    config.DEFAULT_RESIZE_MODE = "scale"
    config.DEFAULT_FALLBACK_PTS = "1.0"
    if not config.ALL_VARIANTS:
        convert_gif_webm(gif_filepath, webm_filepath)
    else:
        convert_gif_webm(gif_filepath, webm_filepath)
        config.DEFAULT_RESIZE_MODE = "pad"
        addition = "_pad"
        webm_filepath = config.EMOTE_ANIMATED_FOLDER + new_file_name + addition + ".webm"
        convert_gif_webm(gif_filepath, webm_filepath)


def convert_webp_gif(filepath, new_file_path):
    logger.info("Starting converting webp to gif")
    url = "https://ezgif.com/webp-to-gif"
    files = {"new-image": open(filepath, "rb")}
    response = requests.post(url=url, files=files, allow_redirects=False)
    logger.info(f"Status code:{response.status_code}")
    if response.status_code == 302:
        url = response.headers["Location"]
        payload = {
            "ajax": "true",
        }
        data = {"file": url.split("/")[-1]}
        logger.debug(f"Data: {data}")
        r = requests.post(url, data=data, params=payload)
        if r.status_code == 200:
            pattern = r"https://ezgif\.com/save/ezgif-\d-\w+\.gif"
            match = re.search(pattern, r.text)
            if match:
                save_url = match.group()
                logger.debug(f"Saving url: {save_url}")
                with requests.get(url=save_url, stream=True) as r:
                    r.raise_for_status()
                    with open(new_file_path, "wb") as file:
                        for chunk in r.iter_content(chunk_size=8192):
                            file.write(chunk)
            else:
                logger.error("Save url not found!")
        logger.info("Finished converting webp to gif")


def convert_gif_webm(filepath, new_file_path):
    logger.info("Starting converting gif to webm")
    job = ffmpeg.input(filepath)
    job = job.filter("fps", fps=config.DEFAULT_FPS)
    info = ffmpeg.probe(filepath)
    logger.debug(f"File probe: {info}")
    stream = info["streams"][0]
    fmt = info["format"]
    if config.DEFAULT_RESIZE_MODE == "scale":
        # Try to scale to 512px
        if stream["width"] >= stream["height"]:
            job = job.filter("scale", 512, -1)
        else:
            job = job.filter("scale", -1, 512)
    elif config.DEFAULT_RESIZE_MODE == "pad":
        if stream["width"] >= stream["height"]:
            job = job.filter("pad", width=512, height="min(ih,512)", x="(ow-iw)/2", y="(oh-ih)/2", color="white@0")
        else:
            job = job.filter("pad", width="min(iw,512)", height=512, x="(ow-iw)/2", y="(oh-ih)/2", color="white@0")
    if "duration" in fmt:
        duration = float(fmt["duration"])
        logger.debug(f"Gif duration:{duration}")
        # Cutting first 3 seconds if over 4.5
        if duration > 4.5:
            job = job.trim(start=0.0, end=3.0)
            new_file_path = new_file_path.replace("_default.", "_trimmed.")
        # Try speed up video if it's over 3 seconds
        elif duration > 3.0:
            job = job.filter("setpts", f"({config.DEFAULT_SMART_DURATION_LIMIT}/{duration})*PTS")
    else:
        # print("No duration in fmt")
        job = job.filter("setpts", f"{config.DEFAULT_FALLBACK_PTS}*PTS")

    job = job.output(
        new_file_path,
        pix_fmt="yuva420p",
        vcodec="libvpx-vp9",
        an=None,  # Remove Audio
        loglevel="quiet",
    ).overwrite_output()
    job.run()


@contextmanager
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout


def progressBar(iterable, prefix="", suffix="", decimals=1, length=100, fill="█", printEnd="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iterable    - Required  : iterable object (Iterable)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    total = len(iterable)

    # Progress Bar Printing Function
    def printProgressBar(iteration):
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + "-" * (length - filledLength)
        print(f"\r{prefix} |{bar}| {percent}% {suffix}", end=printEnd)

    # Initial Call
    printProgressBar(0)
    # Update Progress Bar
    for i, item in enumerate(iterable):
        yield item
        printProgressBar(i + 1)
    # Print New Line on Complete
    print()


def check_directories():
    folders = [config.EMOTE_ANIMATED_FOLDER, config.EMOTE_STATIC_FOLDER, config.TEMP_FOLDER]
    for folder in folders:
        path = Path(folder)
        path.mkdir(parents=True, exist_ok=True)
    logger.info("Directories created/exist.")


def clear_file(filepath):
    path = Path(filepath)
    with path.open(mode="w"):
        pass


def delete_file(filepath):
    path = Path(filepath)
    if path.is_file():
        path.unlink()
        logger.info(f"File {str(path)} deleted!")


if __name__ == "__main__":
    check_directories()

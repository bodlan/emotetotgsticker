import ffmpeg
import requests
import re
from config import *
from pathlib import Path
from PIL import Image


def convert_webp_png(filepath, new_file_name):
    canvas_size = (512, 512)
    canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    im = Image.open(filepath).convert("RGBA")
    im_filepath = EMOTE_STATIC_FOLDER + new_file_name + ".png"
    height = 200
    width = int(im.width * (height / im.height))
    im_resized = im.resize((width, height), Image.LANCZOS)
    x = (canvas_size[0] - im_resized.width) // 2  # Center the image horizontally
    y = (canvas_size[1] - im_resized.height) // 2  # Center the image vertically
    canvas.paste(im_resized, (x, y), im_resized)
    canvas.save(im_filepath, "png")


def convert_webp_webm(filepath, new_file_name):
    # im = Image.open(filepath)
    # im.info.pop('background', None)
    gif_filepath = TEMP_FOLDER + new_file_name + ".gif"
    convert_webp_gif(filepath, gif_filepath)
    # im.save(gif_filepath, 'gif', save_all=True)
    webm_filepath = EMOTE_ANIMATED_FOLDER + new_file_name + ".webm"
    convert_gif_webm(gif_filepath, webm_filepath)


def convert_webp_gif(filepath, new_file_path):
    url = "https://ezgif.com/webp-to-gif"
    files = {'new-image': open(filepath, 'rb')}
    response = requests.post(url=url, files=files, allow_redirects=False)
    print(response.status_code)
    if response.status_code == 302:
        url = response.headers['Location']
        print(url)
        payload = {
            'ajax': 'true',
        }
        data = {'file': url.split("/")[-1]}
        print(data)
        r = requests.post(url, data=data, params=payload)
        print(r.status_code)
        if r.status_code == 200:
            result = r.text
            print(result)
            pattern = r'https://ezgif\.com/save/ezgif-\d-\w+\.gif'
            match = re.search(pattern, result)
            if match:
                save_url = match.group()
                print("Saving url:", save_url)
                with requests.get(url=save_url, stream=True) as r:
                    r.raise_for_status()
                    with open(new_file_path, 'wb') as file:
                        for chunk in r.iter_content(chunk_size=8192):
                            file.write(chunk)
            else:
                print("Save url not found!")


def convert_gif_webm(filepath, new_file_path):
    DEFAULT_FPS = 30
    DEFAULT_SMART_DURATION_LIMIT = '2.9'
    DEFAULT_RESIZE_MODE = 'pad'
    DEFAULT_SPEED_ADJUST_MODE = 'smart'
    DEFAULT_FALLBACK_PTS = '1.0'
    p = Path(filepath)
    job = ffmpeg.input(filepath)
    # 30FPS
    job = job.filter('fps', fps=DEFAULT_FPS)
    info = ffmpeg.probe(filepath)
    print(info)
    stream = info['streams'][0]
    fmt = info['format']
    if DEFAULT_RESIZE_MODE == 'scale':
        # Try to scale to 512px
        if stream['width'] >= stream['height']:
            job = job.filter('scale', 512, -1)
        else:
            job = job.filter('scale', -1, 512)
    elif DEFAULT_RESIZE_MODE == 'pad':
        if stream['width'] >= stream['height']:
            job = job.filter('pad', width=512, height='min(ih*2,512)', x='(ow-iw)/2', y='(oh-ih)/2', color="white@0")
        else:
            job = job.filter('pad', width='min(iw*2,512)', height=512, x='(ow-iw)/2', y='(oh-ih)/2', color="white@0")
    if 'duration' in fmt:
        duration = float(fmt['duration'])
        # Try speed up video if it's over 3 seconds
        if duration > 3.0:
            job = job.filter('setpts', f"({DEFAULT_SMART_DURATION_LIMIT}/{duration})*PTS")
    else:
        job = job.filter('setpts', f"{DEFAULT_FALLBACK_PTS}*PTS")

    job = (
        job
            .output(
            new_file_path,
            pix_fmt='yuva420p',
            vcodec='libvpx-vp9',
            an=None,  # Remove Audio
        )
            .overwrite_output()
    )
    job.run()


def check_directories():
    folders = [EMOTE_ANIMATED_FOLDER, EMOTE_STATIC_FOLDER, TEMP_FOLDER]
    for folder in folders:
        path = Path(folder)
        path.mkdir(parents=True, exist_ok=True)
    print("Directories created/exist.")


def clear_file(filepath):
    path = Path(filepath)
    with path.open(mode="w") as f:
        pass


def delete_file(filepath):
    path = Path(filepath)
    if path.is_file():
        path.unlink()
        print(f"File {str(path)} deleted!")


if __name__ == '__main__':
    convert_webp_gif(TEMP_FOLDER + "docnotL_4x.webp", TEMP_FOLDER + "docnotL.gif")

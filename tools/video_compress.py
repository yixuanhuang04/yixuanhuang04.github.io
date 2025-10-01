import os
import subprocess
from PIL import Image

TARGET_SIZE = 3 * 1024 * 1024  # Target file size: 3MB

def compress_video(file_path):
    """
    Compress an MP4 video using ffmpeg until it meets TARGET_SIZE.
    Uses H.264 codec with adjustable CRF to control quality/file size.
    """
    tmp_path = file_path + ".tmp.mp4"
    crf = 28  # Initial compression parameter
    while True:
        subprocess.run([
            "ffmpeg", "-i", file_path,
            "-vcodec", "libx264", "-crf", str(crf), "-preset", "veryfast",
            "-acodec", "aac", "-b:a", "96k", tmp_path, "-y"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if os.path.getsize(tmp_path) <= TARGET_SIZE or crf >= 40:
            os.replace(tmp_path, file_path)  # Overwrite original file
            print(f"✅ Video compressed: {file_path}, new size: {os.path.getsize(file_path)/1024/1024:.2f} MB")
            break
        else:
            crf += 2  # Increase compression

def compress_gif(file_path):
    """
    Compress a GIF using Pillow until it meets TARGET_SIZE.
    Adjusts quality iteratively to reduce file size.
    """
    tmp_path = file_path + ".tmp.gif"
    quality = 80  # Initial quality
    while True:
        with Image.open(file_path) as im:
            im.save(tmp_path, save_all=True, optimize=True, quality=quality)

        if os.path.getsize(tmp_path) <= TARGET_SIZE or quality <= 10:
            os.replace(tmp_path, file_path)  # Overwrite original file
            print(f"✅ GIF compressed: {file_path}, new size: {os.path.getsize(file_path)/1024/1024:.2f} MB")
            break
        else:
            quality -= 10  # Gradually reduce quality

def scan_and_compress(root_dir):
    """
    Recursively scan the directory for MP4 and GIF files exceeding TARGET_SIZE
    and compress them.
    """
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            if filename.lower().endswith((".mp4", ".gif")):
                size = os.path.getsize(file_path)
                if size > TARGET_SIZE:
                    print(f"Found large file: {file_path}, size: {size/1024/1024:.2f} MB")
                    if filename.lower().endswith(".mp4"):
                        compress_video(file_path)
                    elif filename.lower().endswith(".gif"):
                        compress_gif(file_path)

if __name__ == "__main__":
    scan_and_compress(".")  # Recursively scan current directory

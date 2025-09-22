import os
from io import BytesIO
from PIL import Image

TARGET_SIZE = 1 * 1024 * 512  # Target file size: 1MB
MIN_QUALITY = 20               # Minimum lossy quality
QUALITY_STEP = 5               # Step size for quality reduction
DOWNSCALE_RATIO = 0.9          # Downscale ratio per iteration (90%)
ALLOW_PNG_TO_WEBP = True       # Allow converting PNG (with alpha) to WebP for better compression

def has_alpha(img: Image.Image) -> bool:
    """Check if the image contains an alpha channel (transparency)."""
    return ("A" in img.getbands()) or (img.mode in ("LA", "RGBA", "PA"))

def _try_save_to_bytes(img: Image.Image, fmt: str, **save_kwargs) -> bytes:
    """
    Save the image to an in-memory bytes buffer to check file size
    without writing to disk. Avoids repeated disk writes during compression.
    """
    buf = BytesIO()
    img.save(buf, format=fmt, **save_kwargs)
    return buf.getvalue()

def _progressive_compress(img: Image.Image, fmt: str, quality_first=True, **kwargs) -> bytes:
    """
    Attempt progressive compression: first reduce quality, then downscale if necessary.
    Returns final image bytes without saving to disk.
    
    kwargs are passed directly to PIL's save method (e.g., optimize, lossless, method).
    """
    work = img.copy()
    quality = 95 if quality_first else kwargs.pop("quality", 95)

    while True:
        # Step 1: Reduce quality (only applicable if format supports 'quality')
        q_iter = quality
        while "quality" in Image.SAVE.keys(fmt.upper()) if hasattr(Image, "SAVE") else fmt.lower() in ("jpeg", "webp"):
            data = _try_save_to_bytes(work, fmt, quality=q_iter, **kwargs)
            if len(data) <= TARGET_SIZE or q_iter <= MIN_QUALITY:
                if len(data) <= TARGET_SIZE:
                    return data
                break
            q_iter -= QUALITY_STEP

        # Step 2: Downscale image
        w, h = work.size
        new_size = (max(1, int(w * DOWNSCALE_RATIO)), max(1, int(h * DOWNSCALE_RATIO)))
        if new_size == work.size:
            # Cannot downscale further, return current result
            return _try_save_to_bytes(work, fmt, quality=max(MIN_QUALITY, q_iter), **kwargs)
        work = work.resize(new_size, Image.LANCZOS)
        # Loop back to quality reduction until size requirement is met or image becomes too small

def compress_image(file_path):
    """
    Compress a single image to <= TARGET_SIZE (default 1MB) while preserving aspect ratio.
    Preserve transparency if possible; optionally convert PNG to WebP for better compression.
    """
    try:
        img = Image.open(file_path)
        ext = os.path.splitext(file_path)[1].lower()

        if ext in (".jpg", ".jpeg"):
            # JPEG does not support alpha: apply quality reduction first, then downscale
            data = _progressive_compress(
                img.convert("RGB"),
                fmt="JPEG",
                optimize=True,
            )
            with open(file_path, "wb") as f:
                f.write(data)
            return

        if ext == ".png":
            if has_alpha(img):
                # PNG with alpha: attempt lossless compression first
                # Note: PNG does not support 'quality', rely on optimize and downscaling
                work = img.copy()
                # Try only optimize first, without downscaling
                data = _try_save_to_bytes(work, "PNG", optimize=True, compress_level=9)
                if len(data) <= TARGET_SIZE:
                    with open(file_path, "wb") as f:
                        f.write(data)
                    return

                # Further downscale while preserving transparency
                while True:
                    w, h = work.size
                    new_size = (max(1, int(w * DOWNSCALE_RATIO)), max(1, int(h * DOWNSCALE_RATIO)))
                    if new_size == work.size:
                        break
                    work = work.resize(new_size, Image.LANCZOS)
                    data = _try_save_to_bytes(work, "PNG", optimize=True, compress_level=9)
                    if len(data) <= TARGET_SIZE:
                        with open(file_path, "wb") as f:
                            f.write(data)
                        return

                # If still too large, optionally convert to WebP (supports alpha, higher compression)
                if ALLOW_PNG_TO_WEBP:
                    webp_path = os.path.splitext(file_path)[0] + ".webp"
                    data = _progressive_compress(
                        img,  # keep RGBA
                        fmt="WEBP",
                        quality_first=True,
                        method=6,       # stronger compression
                        lossless=False, # lossy makes it easier to meet target size
                    )
                    with open(webp_path, "wb") as f:
                        f.write(data)
                    os.remove(file_path)
                    print(f"Converted PNG with transparency to WebP: {webp_path}")
                    return
                else:
                    # Do not change format, accept smaller PNG resolution
                    with open(file_path, "wb") as f:
                        f.write(data)  # May still slightly exceed target size
                    return
            else:
                # PNG without alpha: safe to convert to JPEG for smaller size
                data = _progressive_compress(
                    img.convert("RGB"),
                    fmt="JPEG",
                    optimize=True,
                )
                new_path = os.path.splitext(file_path)[0] + ".jpg"
                with open(new_path, "wb") as f:
                    f.write(data)
                os.remove(file_path)
                print(f"Non-transparent PNG converted to JPEG: {new_path}")
                return

        if ext == ".webp":
            # WebP: keep format, apply quality reduction then downscale
            data = _progressive_compress(
                img,
                fmt="WEBP",
                quality_first=True,
                method=6,
            )
            with open(file_path, "wb") as f:
                f.write(data)
            return

        # Other formats: attempt to compress in original format; fallback to JPEG if fails
        try:
            data = _progressive_compress(img, fmt=img.format or "PNG", optimize=True)
            with open(file_path, "wb") as f:
                f.write(data)
        except Exception:
            data = _progressive_compress(img.convert("RGB"), fmt="JPEG", optimize=True)
            with open(os.path.splitext(file_path)[0] + ".jpg", "wb") as f:
                f.write(data)

    except Exception as e:
        print(f"Failed to compress {file_path}: {e}")

def process_folder(folder):
    """Recursively process all jpg/png/webp images in the folder."""
    for root, _, files in os.walk(folder):
        for f in files:
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                file_path = os.path.join(root, f)
                size = os.path.getsize(file_path)
                if size > TARGET_SIZE:
                    print(f"Compressing: {file_path}, original size: {size/1024/1024:.2f} MB")
                    compress_image(file_path)
                    if os.path.exists(file_path):
                        new_size = os.path.getsize(file_path)
                        print(f"Compressed size: {new_size/1024/1024:.2f} MB\n")
                    else:
                        # File may have been converted to .webp or .jpg
                        base = os.path.splitext(file_path)[0]
                        for ext in (".webp", ".jpg", ".jpeg", ".png"):
                            p = base + ext
                            if os.path.exists(p):
                                new_size = os.path.getsize(p)
                                print(f"Compressed file: {p}, size: {new_size/1024/1024:.2f} MB\n")
                                break

if __name__ == "__main__":
    process_folder(".")
import os
from io import BytesIO
from PIL import Image

TARGET_SIZE = 1 * 1024 * 512  # Target file size: 1MB
MIN_QUALITY = 20               # Minimum lossy quality
QUALITY_STEP = 5               # Step size for quality reduction
DOWNSCALE_RATIO = 0.9          # Downscale ratio per iteration (90%)
ALLOW_PNG_TO_WEBP = True       # Allow converting PNG (with alpha) to WebP for better compression

def has_alpha(img: Image.Image) -> bool:
    """Check if the image contains an alpha channel (transparency)."""
    return ("A" in img.getbands()) or (img.mode in ("LA", "RGBA", "PA"))

def _try_save_to_bytes(img: Image.Image, fmt: str, **save_kwargs) -> bytes:
    """
    Save the image to an in-memory bytes buffer to check file size
    without writing to disk. Avoids repeated disk writes during compression.
    """
    buf = BytesIO()
    img.save(buf, format=fmt, **save_kwargs)
    return buf.getvalue()

def _progressive_compress(img: Image.Image, fmt: str, quality_first=True, **kwargs) -> bytes:
    """
    Attempt progressive compression: first reduce quality, then downscale if necessary.
    Returns final image bytes without saving to disk.
    
    kwargs are passed directly to PIL's save method (e.g., optimize, lossless, method).
    """
    work = img.copy()
    quality = 95 if quality_first else kwargs.pop("quality", 95)

    while True:
        # Step 1: Reduce quality (only applicable if format supports 'quality')
        q_iter = quality
        while "quality" in Image.SAVE.keys(fmt.upper()) if hasattr(Image, "SAVE") else fmt.lower() in ("jpeg", "webp"):
            data = _try_save_to_bytes(work, fmt, quality=q_iter, **kwargs)
            if len(data) <= TARGET_SIZE or q_iter <= MIN_QUALITY:
                if len(data) <= TARGET_SIZE:
                    return data
                break
            q_iter -= QUALITY_STEP

        # Step 2: Downscale image
        w, h = work.size
        new_size = (max(1, int(w * DOWNSCALE_RATIO)), max(1, int(h * DOWNSCALE_RATIO)))
        if new_size == work.size:
            # Cannot downscale further, return current result
            return _try_save_to_bytes(work, fmt, quality=max(MIN_QUALITY, q_iter), **kwargs)
        work = work.resize(new_size, Image.LANCZOS)
        # Loop back to quality reduction until size requirement is met or image becomes too small

def compress_image(file_path):
    """
    Compress a single image to <= TARGET_SIZE (default 1MB) while preserving aspect ratio.
    Preserve transparency if possible; optionally convert PNG to WebP for better compression.
    """
    try:
        img = Image.open(file_path)
        ext = os.path.splitext(file_path)[1].lower()

        if ext in (".jpg", ".jpeg"):
            # JPEG does not support alpha: apply quality reduction first, then downscale
            data = _progressive_compress(
                img.convert("RGB"),
                fmt="JPEG",
                optimize=True,
            )
            with open(file_path, "wb") as f:
                f.write(data)
            return

        if ext == ".png":
            if has_alpha(img):
                # PNG with alpha: attempt lossless compression first
                # Note: PNG does not support 'quality', rely on optimize and downscaling
                work = img.copy()
                # Try only optimize first, without downscaling
                data = _try_save_to_bytes(work, "PNG", optimize=True, compress_level=9)
                if len(data) <= TARGET_SIZE:
                    with open(file_path, "wb") as f:
                        f.write(data)
                    return

                # Further downscale while preserving transparency
                while True:
                    w, h = work.size
                    new_size = (max(1, int(w * DOWNSCALE_RATIO)), max(1, int(h * DOWNSCALE_RATIO)))
                    if new_size == work.size:
                        break
                    work = work.resize(new_size, Image.LANCZOS)
                    data = _try_save_to_bytes(work, "PNG", optimize=True, compress_level=9)
                    if len(data) <= TARGET_SIZE:
                        with open(file_path, "wb") as f:
                            f.write(data)
                        return

                # If still too large, optionally convert to WebP (supports alpha, higher compression)
                if ALLOW_PNG_TO_WEBP:
                    webp_path = os.path.splitext(file_path)[0] + ".webp"
                    data = _progressive_compress(
                        img,  # keep RGBA
                        fmt="WEBP",
                        quality_first=True,
                        method=6,       # stronger compression
                        lossless=False, # lossy makes it easier to meet target size
                    )
                    with open(webp_path, "wb") as f:
                        f.write(data)
                    os.remove(file_path)
                    print(f"Converted PNG with transparency to WebP: {webp_path}")
                    return
                else:
                    # Do not change format, accept smaller PNG resolution
                    with open(file_path, "wb") as f:
                        f.write(data)  # May still slightly exceed target size
                    return
            else:
                # PNG without alpha: safe to convert to JPEG for smaller size
                data = _progressive_compress(
                    img.convert("RGB"),
                    fmt="JPEG",
                    optimize=True,
                )
                new_path = os.path.splitext(file_path)[0] + ".jpg"
                with open(new_path, "wb") as f:
                    f.write(data)
                os.remove(file_path)
                print(f"Non-transparent PNG converted to JPEG: {new_path}")
                return

        if ext == ".webp":
            # WebP: keep format, apply quality reduction then downscale
            data = _progressive_compress(
                img,
                fmt="WEBP",
                quality_first=True,
                method=6,
            )
            with open(file_path, "wb") as f:
                f.write(data)
            return

        # Other formats: attempt to compress in original format; fallback to JPEG if fails
        try:
            data = _progressive_compress(img, fmt=img.format or "PNG", optimize=True)
            with open(file_path, "wb") as f:
                f.write(data)
        except Exception:
            data = _progressive_compress(img.convert("RGB"), fmt="JPEG", optimize=True)
            with open(os.path.splitext(file_path)[0] + ".jpg", "wb") as f:
                f.write(data)

    except Exception as e:
        print(f"Failed to compress {file_path}: {e}")

def process_folder(folder):
    """Recursively process all jpg/png/webp images in the folder."""
    for root, _, files in os.walk(folder):
        for f in files:
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                file_path = os.path.join(root, f)
                size = os.path.getsize(file_path)
                if size > TARGET_SIZE:
                    print(f"Compressing: {file_path}, original size: {size/1024/1024:.2f} MB")
                    compress_image(file_path)
                    if os.path.exists(file_path):
                        new_size = os.path.getsize(file_path)
                        print(f"Compressed size: {new_size/1024/1024:.2f} MB\n")
                    else:
                        # File may have been converted to .webp or .jpg
                        base = os.path.splitext(file_path)[0]
                        for ext in (".webp", ".jpg", ".jpeg", ".png"):
                            p = base + ext
                            if os.path.exists(p):
                                new_size = os.path.getsize(p)
                                print(f"Compressed file: {p}, size: {new_size/1024/1024:.2f} MB\n")
                                break

if __name__ == "__main__":
    process_folder(".")
import os
from io import BytesIO
from PIL import Image

TARGET_SIZE = 1 * 1024 * 512  # Target file size: 1MB
MIN_QUALITY = 20               # Minimum lossy quality
QUALITY_STEP = 5               # Step size for quality reduction
DOWNSCALE_RATIO = 0.9          # Downscale ratio per iteration (90%)
ALLOW_PNG_TO_WEBP = True       # Allow converting PNG (with alpha) to WebP for better compression

def has_alpha(img: Image.Image) -> bool:
    """Check if the image contains an alpha channel (transparency)."""
    return ("A" in img.getbands()) or (img.mode in ("LA", "RGBA", "PA"))

def _try_save_to_bytes(img: Image.Image, fmt: str, **save_kwargs) -> bytes:
    """
    Save the image to an in-memory bytes buffer to check file size
    without writing to disk. Avoids repeated disk writes during compression.
    """
    buf = BytesIO()
    img.save(buf, format=fmt, **save_kwargs)
    return buf.getvalue()

def _progressive_compress(img: Image.Image, fmt: str, quality_first=True, **kwargs) -> bytes:
    """
    Attempt progressive compression: first reduce quality, then downscale if necessary.
    Returns final image bytes without saving to disk.
    
    kwargs are passed directly to PIL's save method (e.g., optimize, lossless, method).
    """
    work = img.copy()
    quality = 95 if quality_first else kwargs.pop("quality", 95)

    while True:
        # Step 1: Reduce quality (only applicable if format supports 'quality')
        q_iter = quality
        while "quality" in Image.SAVE.keys(fmt.upper()) if hasattr(Image, "SAVE") else fmt.lower() in ("jpeg", "webp"):
            data = _try_save_to_bytes(work, fmt, quality=q_iter, **kwargs)
            if len(data) <= TARGET_SIZE or q_iter <= MIN_QUALITY:
                if len(data) <= TARGET_SIZE:
                    return data
                break
            q_iter -= QUALITY_STEP

        # Step 2: Downscale image
        w, h = work.size
        new_size = (max(1, int(w * DOWNSCALE_RATIO)), max(1, int(h * DOWNSCALE_RATIO)))
        if new_size == work.size:
            # Cannot downscale further, return current result
            return _try_save_to_bytes(work, fmt, quality=max(MIN_QUALITY, q_iter), **kwargs)
        work = work.resize(new_size, Image.LANCZOS)
        # Loop back to quality reduction until size requirement is met or image becomes too small

def compress_image(file_path):
    """
    Compress a single image to <= TARGET_SIZE (default 1MB) while preserving aspect ratio.
    Preserve transparency if possible; optionally convert PNG to WebP for better compression.
    """
    try:
        img = Image.open(file_path)
        ext = os.path.splitext(file_path)[1].lower()

        if ext in (".jpg", ".jpeg"):
            # JPEG does not support alpha: apply quality reduction first, then downscale
            data = _progressive_compress(
                img.convert("RGB"),
                fmt="JPEG",
                optimize=True,
            )
            with open(file_path, "wb") as f:
                f.write(data)
            return

        if ext == ".png":
            if has_alpha(img):
                # PNG with alpha: attempt lossless compression first
                # Note: PNG does not support 'quality', rely on optimize and downscaling
                work = img.copy()
                # Try only optimize first, without downscaling
                data = _try_save_to_bytes(work, "PNG", optimize=True, compress_level=9)
                if len(data) <= TARGET_SIZE:
                    with open(file_path, "wb") as f:
                        f.write(data)
                    return

                # Further downscale while preserving transparency
                while True:
                    w, h = work.size
                    new_size = (max(1, int(w * DOWNSCALE_RATIO)), max(1, int(h * DOWNSCALE_RATIO)))
                    if new_size == work.size:
                        break
                    work = work.resize(new_size, Image.LANCZOS)
                    data = _try_save_to_bytes(work, "PNG", optimize=True, compress_level=9)
                    if len(data) <= TARGET_SIZE:
                        with open(file_path, "wb") as f:
                            f.write(data)
                        return

                # If still too large, optionally convert to WebP (supports alpha, higher compression)
                if ALLOW_PNG_TO_WEBP:
                    webp_path = os.path.splitext(file_path)[0] + ".webp"
                    data = _progressive_compress(
                        img,  # keep RGBA
                        fmt="WEBP",
                        quality_first=True,
                        method=6,       # stronger compression
                        lossless=False, # lossy makes it easier to meet target size
                    )
                    with open(webp_path, "wb") as f:
                        f.write(data)
                    os.remove(file_path)
                    print(f"Converted PNG with transparency to WebP: {webp_path}")
                    return
                else:
                    # Do not change format, accept smaller PNG resolution
                    with open(file_path, "wb") as f:
                        f.write(data)  # May still slightly exceed target size
                    return
            else:
                # PNG without alpha: safe to convert to JPEG for smaller size
                data = _progressive_compress(
                    img.convert("RGB"),
                    fmt="JPEG",
                    optimize=True,
                )
                new_path = os.path.splitext(file_path)[0] + ".jpg"
                with open(new_path, "wb") as f:
                    f.write(data)
                os.remove(file_path)
                print(f"Non-transparent PNG converted to JPEG: {new_path}")
                return

        if ext == ".webp":
            # WebP: keep format, apply quality reduction then downscale
            data = _progressive_compress(
                img,
                fmt="WEBP",
                quality_first=True,
                method=6,
            )
            with open(file_path, "wb") as f:
                f.write(data)
            return

        # Other formats: attempt to compress in original format; fallback to JPEG if fails
        try:
            data = _progressive_compress(img, fmt=img.format or "PNG", optimize=True)
            with open(file_path, "wb") as f:
                f.write(data)
        except Exception:
            data = _progressive_compress(img.convert("RGB"), fmt="JPEG", optimize=True)
            with open(os.path.splitext(file_path)[0] + ".jpg", "wb") as f:
                f.write(data)

    except Exception as e:
        print(f"Failed to compress {file_path}: {e}")

def process_folder(folder):
    """Recursively process all jpg/png/webp images in the folder."""
    for root, _, files in os.walk(folder):
        for f in files:
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                file_path = os.path.join(root, f)
                size = os.path.getsize(file_path)
                if size > TARGET_SIZE:
                    print(f"Compressing: {file_path}, original size: {size/1024/1024:.2f} MB")
                    compress_image(file_path)
                    if os.path.exists(file_path):
                        new_size = os.path.getsize(file_path)
                        print(f"Compressed size: {new_size/1024/1024:.2f} MB\n")
                    else:
                        # File may have been converted to .webp or .jpg
                        base = os.path.splitext(file_path)[0]
                        for ext in (".webp", ".jpg", ".jpeg", ".png"):
                            p = base + ext
                            if os.path.exists(p):
                                new_size = os.path.getsize(p)
                                print(f"Compressed file: {p}, size: {new_size/1024/1024:.2f} MB\n")
                                break

if __name__ == "__main__":
    process_folder(".")

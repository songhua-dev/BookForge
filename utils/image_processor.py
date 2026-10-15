import io
from PIL import Image, ImageOps

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HAS_HEIF_SUPPORT = True
except ImportError:
    HAS_HEIF_SUPPORT = False


def prepare_for_jpeg(img: Image.Image, bg_color=(255, 255, 255)) -> Image.Image:
    """
    偵測並處理 Alpha 透明通道，合成純白底圖後回傳可安全存為 JPEG 的 RGB 圖片[cite: 11]。
    """
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        img = img.convert("RGBA")
        background = Image.new("RGBA", img.size, bg_color + (255,))
        return Image.alpha_composite(background, img).convert("RGB")
    elif img.mode != "RGB":
        return img.convert("RGB")
    return img


def process_image(img_data: bytes, config: dict) -> tuple[bytes, str]:
    """
    圖像處理管道主入口：依據 config 執行旋轉、sRGB 校正、等比縮放與格式轉碼。
    回傳 (處理後的圖片 bytes, 副檔名)
    """
    # 管道總開關判斷
    if not config.get("IMAGE_PROCESSING_ENABLE", True):
        return img_data, "bin"

    img = Image.open(io.BytesIO(img_data))
    original_format = img.format.lower() if img.format else "jpeg"

    # 1. EXIF 自動轉正
    if config.get("IMAGE_AUTO_ROTATE", True):
        img = ImageOps.exif_transpose(img)

    # 2. 色彩空間校正為 sRGB (RGB)
    if config.get("IMAGE_CONVERT_SRGB", True) and img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")

    # 3. 解析度縮放處理
    if config.get("IMAGE_RESIZE_ENABLE", True):
        max_side = config.get("IMAGE_MAX_SIDE", 1200)
        width, height = img.size
        
        if max(width, height) > max_side:
            if config.get("IMAGE_KEEP_ASPECT_RATIO", True):
                img.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
            else:
                img = img.resize((max_side, max_side), Image.Resampling.LANCZOS)

    # 4. 輸出格式與品質控制
    target_format = config.get("IMAGE_OUTPUT_FORMAT", "JPEG").upper()
    
    if target_format == "KEEP":
        output_format = original_format.upper()
    else:
        output_format = target_format

    # 若輸出為 JPEG，先處理 Alpha 透明通道合成
    if output_format == "JPEG":
        img = prepare_for_jpeg(img)

    # 寫入 Byte 流
    output_io = io.BytesIO()
    save_kwargs = {}
    
    if output_format in ("JPEG", "JPG"):
        save_kwargs["quality"] = config.get("IMAGE_JPEG_QUALITY", 85)
        save_kwargs["optimize"] = True
        ext = "jpg"
        output_format = "JPEG"
    elif output_format == "WEBP":
        save_kwargs["quality"] = config.get("IMAGE_JPEG_QUALITY", 85)
        ext = "webp"
    else:
        ext = output_format.lower()

    img.save(output_io, format=output_format, **save_kwargs)
    return output_io.getvalue(), ext
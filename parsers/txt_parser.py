from pathlib import Path
from utils.text_cleaner import clean_text
from utils.image_processor import process_image

def parse_txt(file_path: str, config: dict, extra_images: list = None) -> dict:
    """
    解析純文字 (.txt) 檔案：
    1. 第一個非空行視為 H1 標題 (優先保留原始字串)
    2. 只有帶中括號 (如 [1.jpg]) 才視為圖片標籤，其餘段落包覆 <p> 並進行 clean_text 清洗
    3. 處理資料夾內獨立圖片檔
    """
    path = Path(file_path)
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    doc_title = path.stem
    html_parts = []
    first_line_found = False

    for line in lines:
        text = line.strip()
        if not text:
            continue

        if not first_line_found:
            doc_title = text
            cleaned = clean_text(text, config) if text else text
            html_parts.append(f"<h1>{cleaned}</h1>")
            first_line_found = True
        else:
            if text.startswith('[') and text.endswith(']'):
                html_parts.append(f"<p>{text}</p>")
            else:
                cleaned = clean_text(text, config)
                html_parts.append(f"<p>{cleaned}</p>")

    processed_images = []
    if extra_images:
        for idx, img_path in enumerate(extra_images, 1):
            with open(img_path, "rb") as f:
                img_bytes = f.read()
            out_bytes, out_ext = process_image(img_bytes, config)
            img_name = f"image_{idx:03d}.{out_ext}"
            processed_images.append({
                "filename": img_name,
                "original_filename": img_path.name,
                "data": out_bytes,
                "bytes_data": out_bytes,
                "ext": out_ext
            })

    # 介面對齊：包成「章節清單」格式，txt 永遠只有一個章節
    return {
        "title": doc_title,
        "chapters": [{"title": doc_title, "html": "\n".join(html_parts).strip()}],
        "embedded_images": [],
        "extra_images": processed_images,
        "images": processed_images
    }
from pathlib import Path
import markdown
from utils.text_cleaner import clean_text
from utils.image_processor import process_image

def parse_md(file_path: str, config: dict, extra_images: list = None) -> dict:
    """
    解析 Markdown (.md) 檔案：
    1. 有中括號 (如 [1.jpg]) 才視為圖片標籤，不進行 clean_text 清洗
    2. 優先保留標題原始文字 (避免特殊符號破壞)
    3. 處理資料夾獨立圖片
    """
    path = Path(file_path)
    with open(path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    lines = raw_text.splitlines()
    doc_title = path.stem
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# ") and doc_title == path.stem:
            raw_title = stripped[2:].strip()
            doc_title = raw_title if raw_title else path.stem
            cleaned_title = clean_text(raw_title, config) if raw_title else raw_title
            cleaned_lines.append(f"# {cleaned_title}")
        else:
            if stripped.startswith('[') and stripped.endswith(']'):
                cleaned_lines.append(line)
            else:
                cleaned_lines.append(clean_text(line, config))

    cleaned_content = "\n".join(cleaned_lines)
    html_content = markdown.markdown(cleaned_content, extensions=['extra'])

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

    # 介面對齊：包成「章節清單」格式，md 永遠只有一個章節
    return {
        "title": doc_title,
        "chapters": [{"title": doc_title, "html": html_content}],
        "embedded_images": [],
        "extra_images": processed_images,
        "images": processed_images
    }
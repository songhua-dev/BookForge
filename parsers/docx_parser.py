import io
from pathlib import Path
from docx import Document
from utils.text_cleaner import clean_text
from utils.image_processor import process_image

def parse_docx(file_path: str, config: dict, extra_images: list = None) -> dict:
    """
    完整支援 DOCX 內文、內嵌圖片與資料夾獨立圖片的解析器
    判定原則：
    1. 必須嚴格帶有中括號 (例如 [1.jpg]) 才是圖片引用，直接保留字串不送 clean_text 清洗。
    2. 若無中括號 (例如 1.jpg)，一律視為一般文字段落送 clean_text 處理。
    3. 優先保留標題原始文字 (full_text)，避免特殊符號（如 ·）導致標題擷取失敗。
    """
    docx_path = Path(file_path)
    doc = Document(docx_path)
    html_parts = []
    embedded_images = []
    img_counter = 1
    doc_title = docx_path.stem  # 預設以檔名作為備援標題

    # 1. 解析 Word 內部文字與實體內嵌圖片 (embedded_images)
    rel_image_map = {}
    for rel in doc.part.rels.values():
        if "image" in rel.target_ref:
            img_part = rel.target_part
            img_bytes = img_part.blob
            
            processed_bytes, out_ext = process_image(img_bytes, config)
            img_name = f"docx_img_{img_counter:03d}.{out_ext}"
            img_counter += 1
            
            embedded_images.append({
                "filename": img_name,
                "data": processed_bytes,
                "bytes_data": processed_bytes,
                "ext": out_ext
            })
            rel_image_map[rel.rId] = img_name

    first_heading_found = False

    for p in doc.paragraphs:
        # 強制將 Word 段落內散落的文字節點組合完整，確保 [1.jpg] 不會被文字切片斷開
        full_text = "".join([run.text for run in p.runs]).strip()
        if not full_text:
            full_text = p.text.strip()
            
        blips = p._element.xpath('.//a:blip')
        
        if not full_text and not blips:
            continue  # 跳過空白段落

        style_name = p.style.name.lower() if p.style else ""

        # 結構判定與 HTML 封裝
        if "heading 1" in style_name or "heading1" in style_name:
            # 優先直接鎖定 full_text 原始字串作為標題（如 "流星·蝴蝶·劍"）
            if not first_heading_found and full_text:
                doc_title = full_text
                first_heading_found = True
                
            cleaned_text = clean_text(full_text, config) if full_text else full_text
            html_parts.append(f"<h1>{cleaned_text}</h1>")
        elif "heading 2" in style_name or "heading2" in style_name:
            cleaned_text = clean_text(full_text, config) if full_text else ""
            html_parts.append(f"<h2>{cleaned_text}</h2>")
        elif "heading 3" in style_name or "heading3" in style_name:
            cleaned_text = clean_text(full_text, config) if full_text else ""
            html_parts.append(f"<h3>{cleaned_text}</h3>")
        else:
            if blips:
                for blip in blips:
                    r_id = blip.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                    if r_id in rel_image_map:
                        img_filename = rel_image_map[r_id]
                        html_parts.append(f'<div class="img-container"><img src="images/{img_filename}" /></div>')
            elif full_text:
                # 【嚴格判定】：必須以 '[' 開頭且以 ']' 結尾才當作圖片引用語法
                if full_text.startswith('[') and full_text.endswith(']'):
                    html_parts.append(f"<p>{full_text}</p>")
                else:
                    # 沒帶中括號（例如純文字 1.jpg），一律當作一般內文做全半形與標點清洗
                    cleaned_text = clean_text(full_text, config)
                    html_parts.append(f"<p>{cleaned_text}</p>")

    # 2. 讀取同資料夾下的獨立圖片檔案 (extra_images)
    folder_images = []
    if extra_images:
        for img_path in extra_images:
            p = Path(img_path)
            ext = p.suffix.lower().replace('.', '')
            try:
                with open(p, "rb") as f:
                    img_bytes = f.read()
                out_bytes, out_ext = process_image(img_bytes, config)
                folder_images.append({
                    "filename": p.name,          # 例如 1.jpg
                    "original_filename": p.name, # 提供 template_engine 比對 [1.jpg]
                    "data": out_bytes,
                    "bytes_data": out_bytes,
                    "ext": out_ext
                })
            except Exception as e:
                print(f"⚠️ 讀取資料夾圖片【{p.name}】失敗：{e}")

    # 3. 合併所有圖片來源
    all_images = embedded_images + folder_images

    return {
        "title": doc_title,
        "content_html": "\n".join(html_parts).strip(),
        "embedded_images": embedded_images,
        "extra_images": folder_images,
        "images": all_images
    }
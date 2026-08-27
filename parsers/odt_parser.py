import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from utils.text_cleaner import clean_text
from utils.image_processor import process_image

def extract_text_from_node(node):
    """專門處理 ODT 特殊 XML 結構的文字提取器"""
    text_pieces = []
    for elem in node.iter():
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag == 's':
            count = int(elem.attrib.get('{urn:oasis:names:tc:opendocument:xmlns:text:1.0}c', 1))
            text_pieces.append(' ' * count)
        elif elem.text:
            text_pieces.append(elem.text)
        if elem.tail:
            text_pieces.append(elem.tail)
    return "".join(text_pieces).strip()

def parse_odt(odt_path: str, config: dict, extra_images: list = None) -> dict:
    """完整支援 ODT 內文、內嵌圖片與資料夾獨立圖片的解析器"""
    odt_path = Path(odt_path)
    html_parts = []
    embedded_images = []
    doc_title = odt_path.stem
    first_heading_found = False

    # 1. 解析 ODT 內部文字與內嵌圖片
    with zipfile.ZipFile(odt_path, 'r') as z:
        content_xml = z.read('content.xml')
        root = ET.fromstring(content_xml)
        img_counter = 1

        for node in root.iter():
            tag = node.tag.split('}')[-1] if '}' in node.tag else node.tag

            if tag == 'h':
                text = extract_text_from_node(node)
                if text:
                    # 與 DOCX/TXT/MD 對齊：優先保留內文第一個標題的原始字串
                    if not first_heading_found:
                        doc_title = text
                        first_heading_found = True
                    cleaned_text = clean_text(text, config) if text else text
                    html_parts.append(f"<h1>{cleaned_text}</h1>")
            elif tag == 'p':
                text = extract_text_from_node(node)
                if text:
                    # 與 DOCX/TXT/MD 對齊：必須以 '[' 開頭且以 ']' 結尾才當作圖片引用語法
                    if text.startswith('[') and text.endswith(']'):
                        html_parts.append(f"<p>{text}</p>")
                    else:
                        cleaned_text = clean_text(text, config)
                        html_parts.append(f"<p>{cleaned_text}</p>")
            elif tag == 'image':
                img_href = None
                for k, v in node.attrib.items():
                    if k.endswith('href'):
                        img_href = v
                        break

                if img_href and img_href in z.namelist():
                    img_bytes = z.read(img_href)
                    # 統一經過 process_image 轉檔與壓縮
                    out_bytes, out_ext = process_image(img_bytes, config)

                    img_name = f"odt_img_{img_counter:03d}.{out_ext}"
                    embedded_images.append({
                        "filename": img_name,
                        "data": out_bytes,
                        "bytes_data": out_bytes,
                        "ext": out_ext
                    })
                    html_parts.append(f'<div class="img-container"><img src="images/{img_name}" /></div>')
                    img_counter += 1

    # 2. 讀取同資料夾下的獨立圖片檔案 (extra_images)
    folder_images = []
    if extra_images:
        for img_path in extra_images:
            p = Path(img_path)
            try:
                with open(p, 'rb') as f:
                    img_bytes = f.read()
                # 統一經過 process_image 轉檔
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
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from utils.text_cleaner import clean_text
from utils.image_processor import process_image


def _local_tag(elem):
    return elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag


def extract_text_from_node(node):
    """
    純文字擷取（不處理圖片）。仍保留給標題/空白判斷、
    以及佔位符（如 [IMG_001]）偵測使用。
    """
    text_pieces = []
    for elem in node.iter():
        tag = _local_tag(elem)
        if tag == 's':
            count = int(elem.attrib.get(
                '{urn:oasis:names:tc:opendocument:xmlns:text:1.0}c', 1))
            text_pieces.append(' ' * count)
        elif elem.text:
            text_pieces.append(elem.text)
        if elem.tail:
            text_pieces.append(elem.tail)
    return "".join(text_pieces).strip()


def _render_block_ordered(node, z, config, counter_state):
    """
    對單一區塊節點（<h> 或 <p>）做「單次」深度優先走訪，
    文字與行內圖片依照原始 XML 出現順序，交錯輸出成同一段 html 片段。

    修正重點：舊版做法是先用 extract_text_from_node() 把整段文字一次抓完
    （圖片節點沒有 .text，擷取文字時直接被跳過），等外層迴圈事後才遞迴
    處理到圖片節點，導致圖片永遠被擠到整段文字結尾。這裡改成同一次遍歷
    同時處理文字與圖片，依照它們在 XML 裡實際出現的順序輸出。

    counter_state 是一個 dict（例如 {"n": 1}），帶著全域共用的圖片流水號，
    確保整份文件的圖片檔名不會因為改成逐段處理而重置或衝突。

    回傳 (html片段, 該段落新增的內嵌圖片清單)。
    """
    parts = []
    block_images = []

    def handle(elem):
        tag = _local_tag(elem)

        if tag == 's':
            count = int(elem.attrib.get(
                '{urn:oasis:names:tc:opendocument:xmlns:text:1.0}c', 1))
            parts.append(' ' * count)
            return

        if tag == 'image':
            img_href = None
            for k, v in elem.attrib.items():
                if k.endswith('href'):
                    img_href = v
                    break
            if img_href and img_href in z.namelist():
                img_bytes = z.read(img_href)
                out_bytes, out_ext = process_image(img_bytes, config)
                img_name = f"odt_img_{counter_state['n']:03d}.{out_ext}"
                counter_state['n'] += 1
                block_images.append({
                    "filename": img_name,
                    "data": out_bytes,
                    "bytes_data": out_bytes,
                    "ext": out_ext
                })
                parts.append(f'<img src="images/{img_name}" />')
            return

        # 一般節點（例如 text:span、draw:frame）：先輸出自己的文字，再依序遞迴子節點
        if elem.text:
            parts.append(clean_text(elem.text, config))
        for child in list(elem):
            handle(child)
            if child.tail:
                parts.append(clean_text(child.tail, config))

    if node.text:
        parts.append(clean_text(node.text, config))
    for child in list(node):
        handle(child)
        if child.tail:
            parts.append(clean_text(child.tail, config))

    return "".join(parts).strip(), block_images


def parse_odt(odt_path: str, config: dict, extra_images: list = None) -> dict:
    """ODT 解析器（章節清單格式；圖文混排已修正為同一次遍歷、依原始順序輸出）"""
    odt_path = Path(odt_path)
    html_parts = []
    embedded_images = []
    doc_title = odt_path.stem
    first_heading_found = False
    counter_state = {"n": 1}

    with zipfile.ZipFile(odt_path, 'r') as z:
        content_xml = z.read('content.xml')
        root = ET.fromstring(content_xml)

        for node in root.iter():
            tag = _local_tag(node)
            if tag not in ('h', 'p'):
                continue  # 只在區塊層級（標題／段落）處理；圖片改成在同一次遍歷內處理，不再由外層另外抓 image 節點，避免重複輸出

            plain_text = extract_text_from_node(node)

            # 佔位符段落（例如 combine.py 產生的 [IMG_003]）：原樣保留，不清洗
            if plain_text.startswith('[') and plain_text.endswith(']'):
                if tag == 'h':
                    html_parts.append(f"<h1>{plain_text}</h1>")
                else:
                    html_parts.append(f"<p>{plain_text}</p>")
                continue

            fragment_html, block_images = _render_block_ordered(node, z, config, counter_state)

            if not fragment_html.strip():
                continue  # 真正空白的段落跳過

            if tag == 'h':
                if not first_heading_found:
                    doc_title = plain_text if plain_text else doc_title
                    first_heading_found = True
                html_parts.append(f"<h1>{fragment_html}</h1>")
            else:
                if not plain_text and block_images:
                    # 純圖片段落：維持既有 img-container 包裹，與 docx_parser.py 的處理方式一致
                    html_parts.append(f'<div class="img-container">{fragment_html}</div>')
                else:
                    html_parts.append(f"<p>{fragment_html}</p>")

            embedded_images.extend(block_images)

    # 2. 讀取同資料夾下的獨立圖片檔案 (extra_images)
    folder_images = []
    if extra_images:
        for img_path in extra_images:
            p = Path(img_path)
            try:
                with open(p, 'rb') as f:
                    img_bytes = f.read()
                out_bytes, out_ext = process_image(img_bytes, config)
                folder_images.append({
                    "filename": p.name,
                    "original_filename": p.name,
                    "data": out_bytes,
                    "bytes_data": out_bytes,
                    "ext": out_ext
                })
            except Exception as e:
                print(f"⚠️ 讀取資料夾圖片【{p.name}】失敗：{e}")

    all_images = embedded_images + folder_images

    return {
        "title": doc_title,
        "chapters": [{"title": doc_title, "html": "\n".join(html_parts).strip()}],
        "embedded_images": embedded_images,
        "extra_images": folder_images,
        "images": all_images
    }
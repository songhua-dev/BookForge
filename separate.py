"""
純函式庫，供 app.py（電子書校對面板）呼叫，依標題 1 或標題 2 拆分 .docx，
抽取內嵌圖片為 img_XXX.ext 獨立檔案，文中以 [IMG_XXX] 佔位符標記圖片原始位置。
"""
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn

VALID_SPLIT_LEVELS = ("heading 1", "heading 2")


def _get_style_tag(paragraph):
    """回傳段落樣式名稱的小寫字串，方便判斷 heading 1/2。"""
    return paragraph.style.name.lower() if paragraph.style else ""


def _is_boundary(style_tag: str, split_level: str) -> bool:
    """
    依 split_level 判斷這個段落是不是新章節的分界。

    依標題2分割時，標題1段落（例如書名/章名）視為一般內容段落，
    原樣複製進所屬檔案裡（仍保留 Heading 1 樣式，只是不觸發新檔案）——
    只有標題2才會換檔。
    """
    if split_level == "heading 2":
        return "heading 2" in style_tag or "heading2" in style_tag
    return "heading 1" in style_tag or "heading1" in style_tag


def _extract_image_from_run(run, doc, img_counter: int, target_dir: Path):
    """
    偵測 run 裡是否含有內嵌圖片 (a:blip)。若有，抽取圖片二進位資料存檔到
    target_dir，回傳 (是否為圖片, 佔位符文字或 None, 下一個可用的 img_counter)。
    """
    blips = run._element.xpath('.//a:blip')
    if not blips:
        return False, None, img_counter

    blip = blips[0]
    r_id = blip.get(qn('r:embed'))
    if not r_id or r_id not in doc.part.rels:
        return False, None, img_counter

    image_part = doc.part.rels[r_id].target_part
    image_bytes = image_part.blob

    # 依 content_type 判斷副檔名，抓不到則預設 png
    content_type = image_part.content_type
    ext = content_type.split('/')[-1].lower()
    if ext == 'jpeg':
        ext = 'jpg'
    if ext not in ('jpg', 'png', 'webp', 'gif', 'bmp'):
        ext = 'png'

    img_filename = f"img_{img_counter:03d}.{ext}"
    (target_dir / img_filename).write_bytes(image_bytes)

    placeholder = f"[IMG_{img_counter:03d}]"
    return True, placeholder, img_counter + 1


def separate_docx(
    source_path: str,
    target_dir: str,
    split_level: str = "heading 1",
    delete_source: bool = True,
) -> dict:
    """
    將來源 .docx 依 split_level 拆分成 01.docx, 02.docx... 存到 target_dir，
    並把內嵌圖片抽取成 img_XXX.ext 獨立檔案，文中以 [IMG_XXX] 佔位符標記原始位置。

    參數:
        source_path: 待拆分的來源 .docx 完整路徑
        target_dir: 拆分結果輸出資料夾（對應 config["PROOFREAD_DIR"]）
        split_level: "heading 1" 或 "heading 2"，決定用哪一層標題當章節分界
        delete_source: 拆分成功後是否刪除來源檔

    回傳:
        {"doc_count": int, "image_count": int}
    """
    if split_level not in VALID_SPLIT_LEVELS:
        raise ValueError(f"split_level 必須是 {VALID_SPLIT_LEVELS} 其中之一，收到：{split_level}")

    source_file = Path(source_path)
    if not source_file.exists():
        raise FileNotFoundError(f"找不到來源檔案：{source_path}")

    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)

    doc = Document(str(source_file))

    img_counter = 1
    doc_counter = 0
    current_doc = None

    for p in doc.paragraphs:
        style_tag = _get_style_tag(p)
        is_boundary = _is_boundary(style_tag, split_level)

        # 若遇到分界層級的標題，或是第一個段落，建立新文件
        if is_boundary or current_doc is None:
            if current_doc is not None:
                output_file = target_path / f"{doc_counter:02d}.docx"
                current_doc.save(str(output_file))

            doc_counter += 1
            current_doc = Document()

        # 建立段落並維持原始樣式（標題1/標題2樣式一律照樣複製過去，
        # 即使該層級本身不是這次分割的分界依據，視覺樣式仍要保留）
        if "heading 1" in style_tag or "heading1" in style_tag:
            new_p = current_doc.add_paragraph(style="Heading 1")
        elif "heading 2" in style_tag or "heading2" in style_tag:
            new_p = current_doc.add_paragraph(style="Heading 2")
        else:
            new_p = current_doc.add_paragraph()

        # 處理 run 裡面的文字與圖片
        for run in p.runs:
            is_image, placeholder, img_counter = _extract_image_from_run(
                run, doc, img_counter, target_path
            )
            if is_image:
                new_p.add_run(placeholder)
            elif run.text:
                new_run = new_p.add_run(run.text)
                new_run.bold = run.bold
                new_run.italic = run.italic
                new_run.underline = run.underline

    # 儲存最後一份文件
    if current_doc is not None:
        output_file = target_path / f"{doc_counter:02d}.docx"
        current_doc.save(str(output_file))

    total_images = img_counter - 1

    if delete_source:
        source_file.unlink()

    return {"doc_count": doc_counter, "image_count": total_images}
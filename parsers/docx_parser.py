import io
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
from utils.text_cleaner import clean_text
from utils.image_processor import process_image


def _extract_short_title(full_text: str, config: dict) -> str:
    if not config.get("CHAPTER_TITLE_TRUNCATE", True):
        return full_text.strip()

    split_char = config.get("chapter_title_split_char")
    if split_char and split_char in full_text:
        return full_text.split(split_char, 1)[0].strip()
    return full_text.strip()


def _get_usable_width_emu(doc):
    """
    取得文件版面「可用寬度」(EMU 單位) = 頁面寬度 - 左邊界 - 右邊界。
    用來把 Word 裡圖片的實際顯示寬度換算成佔版面的百分比。
    """
    try:
        section = doc.sections[0]
        usable = section.page_width - section.left_margin - section.right_margin
        return int(usable) if usable and usable > 0 else None
    except Exception:
        return None


def _get_display_width_percent(blip, usable_width_emu):
    """
    依圖片所在的 <wp:extent>（Word 裡使用者實際調整過後的顯示尺寸，
    不是圖片檔案本身的原始像素尺寸），對照版面可用寬度，
    算出這張圖片在原稿裡佔了多少比例的版面寬度。
    """
    if not usable_width_emu:
        return None

    # blip 在 pic:blipFill 內部，往上層層找到 wp:inline（或 wp:anchor）
    # 底下的 wp:extent 節點。往上最多找 8 層，避免理論上的無窮迴圈。
    ancestor = blip
    extent = None
    for _ in range(8):
        ancestor = ancestor.getparent()
        if ancestor is None:
            break
        found = ancestor.find(qn('wp:extent'))
        if found is not None:
            extent = found
            break

    if extent is None:
        return None

    cx = extent.get('cx')
    if not cx:
        return None

    try:
        percent = (int(cx) / usable_width_emu) * 100
    except (ValueError, ZeroDivisionError):
        return None

    # 夾在 1~100 之間，避免版面資訊異常時算出離譜的數字撐爆畫面
    return max(1, min(100, round(percent)))


def _is_run_bold(run, paragraph, inherit_style_bold=True):
    """
    判斷一個 run 在 Word 裡「實際顯示」是不是粗體。
    """
    if run.bold is not None:
        return bool(run.bold)
    if not inherit_style_bold:
        return False

    try:
        char_style = run.style
        while char_style is not None:
            if char_style.font.bold is not None:
                return bool(char_style.font.bold)
            char_style = char_style.base_style
    except Exception:
        pass

    try:
        para_style = paragraph.style
        while para_style is not None:
            if para_style.font.bold is not None:
                return bool(para_style.font.bold)
            para_style = para_style.base_style
    except Exception:
        pass

    return False


def _render_paragraph_mixed(p, rel_image_map, config, usable_width_emu, inherit_style_bold=True):
    """
    依照 Word 原始 run 順序，混合輸出文字（含粗體 <strong>）與行內圖片（<img>）。
    這是修正「同一段落內文字+圖片混排時，文字被整段丟棄」bug 的核心：
    不再對整個段落做 blip 優先判斷，而是逐一走訪 run，圖片跟文字各自依原始順序輸出。
    """
    parts = []
    has_text = False
    has_non_bold_text = False

    for run in p.runs:
        # 每個 run 自己的 XML 範圍內找圖片，確保跟文字的先後順序不會亂掉
        run_blips = run._element.xpath('.//a:blip')
        for blip in run_blips:
            r_id = blip.attrib.get(
                '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed'
            )
            if r_id in rel_image_map:
                percent = _get_display_width_percent(blip, usable_width_emu)
                style_attr = f' style="width:{percent}%;"' if percent else ""
                parts.append(f'<img src="images/{rel_image_map[r_id]}"{style_attr} />')

        run_text = run.text
        if not run_text:
            continue

        has_text = True
        if _is_run_bold(run, p, inherit_style_bold):
            piece = clean_text(run_text, config)
            parts.append(f"<strong>{piece}</strong>")
        else:
            has_non_bold_text = True
            parts.append(clean_text(run_text, config))

    is_all_bold = has_text and not has_non_bold_text
    return "".join(parts), is_all_bold


def parse_docx(file_path: str, config: dict, extra_images: list = None) -> dict:
    """
    DOCX 解析器（章節化版本）。

    回傳格式改為「章節清單」：
        {
            "title": <整份文件/書籍標題>,
            "chapters": [{"title": <章節短標題>, "html": <該章節 html>}, ...],
            "embedded_images": [...],
            "extra_images": [...],
            "images": [...]
        }
    """
    docx_path = Path(file_path)
    doc = Document(docx_path)

    # 版面可用寬度（EMU），用來把圖片顯示尺寸換算成百分比。
    # 抓不到時 usable_width_emu 為 None，圖片會 fallback 成不設定寬度（既有行為）。
    usable_width_emu = _get_usable_width_emu(doc)

    # 1. 解析內嵌圖片（rId -> 檔名 對照表）
    embedded_images = []
    img_counter = 1
    rel_image_map = {}
    for rel in doc.part.rels.values():
        if "image" in rel.target_ref:
            img_bytes = rel.target_part.blob
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

    chapters = []
    current_chapter_title = None
    current_html_parts = []

    for p in doc.paragraphs:
        full_text_concat = "".join(run.text for run in p.runs).strip()
        if not full_text_concat:
            full_text_concat = p.text.strip()
        blips_in_para = p._element.xpath('.//a:blip')

        if not full_text_concat and not blips_in_para:
            continue  # 空白段落跳過

        style_name = p.style.name.lower() if p.style else ""
        is_h1 = "heading 1" in style_name or "heading1" in style_name
        is_h2 = "heading 2" in style_name or "heading2" in style_name
        is_h3 = "heading 3" in style_name or "heading3" in style_name

        if is_h1:
            # 換章節：先把前一章存檔
            if current_chapter_title is not None:
                chapters.append({
                    "title": current_chapter_title,
                    "html": "\n".join(current_html_parts).strip()
                })

            short_title = _extract_short_title(full_text_concat, config)
            short_title = clean_text(short_title, config) if short_title else short_title
            if not short_title:
                short_title = f"第 {len(chapters) + 1} 章"

            current_chapter_title = short_title
            current_html_parts = [f"<h1>{short_title}</h1>"]

            # 如果標題1含圖片，為了正常顯示圖片，可以取消註解，但該段文字會重複一次
            #full_line_html, _ = _render_paragraph_mixed(p, rel_image_map, config, usable_width_emu)
            #if full_line_html.strip():
            #    current_html_parts.append(f"<p>{full_line_html}</p>")

        elif is_h2:
            fragment_html, _ = _render_paragraph_mixed(
                p, rel_image_map, config, usable_width_emu, inherit_style_bold=False
            )
            current_html_parts.append(f"<h2>{fragment_html}</h2>")

        elif is_h3:
            fragment_html, _ = _render_paragraph_mixed(
                p, rel_image_map, config, usable_width_emu, inherit_style_bold=False
            )
            current_html_parts.append(f"<h3>{fragment_html}</h3>")

        else:
            # 佔位符段落（例如 separate.py 產生的 [IMG_003]）：原樣保留，不清洗、不拆 run
            is_placeholder_only = (
                full_text_concat.startswith('[') and full_text_concat.endswith(']')
                and not blips_in_para
            )
            if is_placeholder_only:
                current_html_parts.append(f"<p>{full_text_concat}</p>")
                continue

            if full_text_concat and not blips_in_para:
                # 純文字段落：逐 run 混排，處理部分/整段粗體
                fragment_html, is_all_bold = _render_paragraph_mixed(p, rel_image_map, config, usable_width_emu)
                css_class = ' class="bold-block"' if is_all_bold else ""
                current_html_parts.append(f"<p{css_class}>{fragment_html}</p>")

            elif not full_text_concat and blips_in_para:
                # 純圖片段落：維持既有 img-container 包裹（相容既有樣式邏輯），
                # 同樣依原稿顯示尺寸算出百分比寬度
                for blip in blips_in_para:
                    r_id = blip.attrib.get(
                        '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed'
                    )
                    if r_id in rel_image_map:
                        img_filename = rel_image_map[r_id]
                        percent = _get_display_width_percent(blip, usable_width_emu)
                        style_attr = f' style="width:{percent}%;"' if percent else ""
                        current_html_parts.append(
                            f'<div class="img-container"><img src="images/{img_filename}"{style_attr} /></div>'
                        )
            else:
                # 文字＋圖片混排在同一段（原本會把文字整段丟掉的 bug，這裡修正）
                fragment_html, is_all_bold = _render_paragraph_mixed(p, rel_image_map, config, usable_width_emu)
                css_class = ' class="bold-block"' if is_all_bold else ""
                current_html_parts.append(f"<p{css_class}>{fragment_html}</p>")

    # 收尾：存檔最後一章；若全文從頭到尾沒有標題1，整份文件視為單一章節
    if current_chapter_title is not None:
        chapters.append({
            "title": current_chapter_title,
            "html": "\n".join(current_html_parts).strip()
        })
    elif current_html_parts:
        chapters.append({
            "title": docx_path.stem,
            "html": "\n".join(current_html_parts).strip()
        })

    # 整份文件（書籍）標題：單一章節時沿用舊行為（用該章節標題）；
    # 多章節時（書籍情境）標題交由封面/設定檔決定，這裡先用檔名頂替
    if len(chapters) == 1:
        doc_title = chapters[0]["title"]
    else:
        doc_title = docx_path.stem

    # 2. 讀取同資料夾下的獨立圖片檔案 (extra_images)
    folder_images = []
    if extra_images:
        for img_path in extra_images:
            p_img = Path(img_path)
            try:
                with open(p_img, "rb") as f:
                    img_bytes = f.read()
                out_bytes, out_ext = process_image(img_bytes, config)
                # 檔名要用「轉檔後的實際副檔名」重建，不能沿用原始檔名EPUBCheck 會直接判定錯誤（OPF-029），擋下整個發行流程。
                img_filename = f"{p_img.stem}.{out_ext}"
                folder_images.append({
                    "filename": img_filename,
                    "original_filename": p_img.name,
                    "data": out_bytes,
                    "bytes_data": out_bytes,
                    "ext": out_ext
                })
            except Exception as e:
                print(f"⚠️ 讀取資料夾圖片【{p_img.name}】失敗：{e}")

    all_images = embedded_images + folder_images

    return {
        "title": doc_title,
        "chapters": chapters,
        "embedded_images": embedded_images,
        "extra_images": folder_images,
        "images": all_images
    }
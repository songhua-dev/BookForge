"""
純函式庫，供 app.py呼叫，將 target_dir 內符合「純數字檔名」
規則的章節檔（例如 01.docx, 02.docx...）依序合併為一份完整文件，
[IMG_XXX] 佔位符還原為對應的圖片。

跟 separate.py 一樣，這裡不保留 CLI 進入點、不寫死路徑，例外一律往外拋，
交給呼叫端（app.py 路由）決定怎麼呈現給使用者。

只合併檔名符合「純數字.docx」規則的章節檔；資料夾內其他檔名一律不參與合併

目前僅支援 .docx 格式；若偵測到章節檔案格式不一致，或章節檔案不是 .docx
（例如未來要支援的 .odt/.md/.txt），一律中止並拋出例外，不執行合併。
"""
import re
from pathlib import Path
from docx import Document

# 章節檔命名規則：純數字檔名 + 副檔名。副檔名清單先列出未來可能支援的格式，
# 但目前只有 .docx 會真的被處理（見 SUPPORTED_EXTENSIONS）——這樣之後要
# 擴充 .odt/.md/.txt 時，命名規則不用重寫，只需要放開 SUPPORTED_EXTENSIONS。
CHAPTER_PATTERN = re.compile(r'^\d{2,}\.(docx|odt|md|markdown|txt)$', re.IGNORECASE)
IMAGE_PATTERN = re.compile(r'^img_\d{3,}\.\w+$', re.IGNORECASE)
PLACEHOLDER_PATTERN = re.compile(r'\[IMG_(\d{3,})\]')

SUPPORTED_EXTENSIONS = (".docx",)  # 目前僅支援 docx；odt/md/txt 屬於未來擴充範圍，先擋掉


def _get_style_tag(paragraph):
    return paragraph.style.name.lower() if paragraph.style else ""


def _find_chapter_files(target_dir: Path):
    """
    掃描 target_dir，找出符合「純數字檔名」規則的章節檔（例如 01.docx）。
    偵測到章節檔案副檔名不一致（例如同時有 01.docx 跟 02.odt），
    或章節檔案格式不是目前支援的 .docx，一律中止並拋出例外，不執行合併。
    回傳依數字順序排序好的章節檔案清單。
    """
    matched = [f for f in target_dir.iterdir() if f.is_file() and CHAPTER_PATTERN.match(f.name)]

    if not matched:
        raise FileNotFoundError(f"{target_dir} 內找不到任何符合命名規則的章節檔（例如 01.docx, 02.docx）")

    extensions_found = {f.suffix.lower() for f in matched}
    if len(extensions_found) > 1:
        raise ValueError(
            f"資料夾內偵測到章節檔案格式不一致（{sorted(extensions_found)}），請確認後再試一次，不執行合併。"
        )

    ext = next(iter(extensions_found))
    if ext not in SUPPORTED_EXTENSIONS:
        raise NotImplementedError(f"目前僅支援 .docx 格式的合併，尚未支援 {ext} 格式的章節檔。")

    return sorted(matched, key=lambda f: int(f.stem))


def _find_excluded_files(target_dir: Path, chapter_files: list):
    """
    回傳資料夾內「既不是章節檔、也不是圖片檔」的其他檔案名稱清單，
    用於提示使用者這些檔案未被合併。
    """
    chapter_names = {f.name for f in chapter_files}
    excluded = []
    for f in target_dir.iterdir():
        if not f.is_file():
            continue
        if f.name in chapter_names:
            continue
        if IMAGE_PATTERN.match(f.name):
            continue
        excluded.append(f.name)
    return excluded


def _find_image_file(target_dir: Path, img_num: int):
    """依編號在 target_dir 內找對應的圖片檔（副檔名不固定）。"""
    matches = list(target_dir.glob(f"img_{img_num:03d}.*"))
    return matches[0] if matches else None


def _collect_all_placeholders(chapter_files, target_dir: Path):
    """
    第一輪掃描：只讀取、不寫入。收集所有章節裡出現的佔位符編號，
    並逐一核對對應圖片檔是否存在。有任何一個對不上，直接中止，
    不產生任何輸出檔案。
    """
    all_placeholder_nums = set()

    for f in chapter_files:
        doc = Document(str(f))
        for p in doc.paragraphs:
            for match in PLACEHOLDER_PATTERN.finditer(p.text):
                all_placeholder_nums.add(int(match.group(1)))

    missing = [n for n in sorted(all_placeholder_nums) if _find_image_file(target_dir, n) is None]
    if missing:
        missing_str = ", ".join(f"IMG_{n:03d}" for n in missing)
        raise RuntimeError(
            f"偵測到 {len(missing)} 個佔位符找不到對應圖片檔，已中止，未產生任何輸出：{missing_str}"
        )

    return all_placeholder_nums


def _copy_paragraph_run_level(source_p, target_doc, target_dir: Path):
    """
    優先做法：逐一檢查每個 run 的文字是否『完整等於』一個佔位符，精準抽換成
    圖片，同時保留其他文字 run 各自的粗體/斜體/底線格式。
    """
    style_tag = _get_style_tag(source_p)
    if "heading 1" in style_tag or "heading1" in style_tag:
        target_p = target_doc.add_paragraph(style="Heading 1")
    elif "heading 2" in style_tag or "heading2" in style_tag:
        target_p = target_doc.add_paragraph(style="Heading 2")
    else:
        target_p = target_doc.add_paragraph()

    for run in source_p.runs:
        stripped = run.text.strip()
        full_match = PLACEHOLDER_PATTERN.fullmatch(stripped)

        if full_match:
            img_num = int(full_match.group(1))
            img_path = _find_image_file(target_dir, img_num)
            target_p.add_run().add_picture(str(img_path))
        elif run.text:
            new_run = target_p.add_run(run.text)
            new_run.bold = run.bold
            new_run.italic = run.italic
            new_run.underline = run.underline

    return target_p


def _paragraph_needs_text_fallback(source_p):
    """
    若段落整體文字含有佔位符，但沒有任何一個『單一 run』完整等於該佔位符
    （例如貼上校對後文字時整段被壓成同一個 run），改用文字層級的 fallback
    處理（會犧牲該段落內文字的逐字粗體資訊）。
    """
    has_pattern_in_text = bool(PLACEHOLDER_PATTERN.search(source_p.text))
    has_pattern_as_whole_run = any(
        PLACEHOLDER_PATTERN.fullmatch(r.text.strip()) for r in source_p.runs
    )
    return has_pattern_in_text and not has_pattern_as_whole_run


def _copy_paragraph_text_fallback(source_p, target_doc, target_dir: Path):
    """Fallback：整段文字直接用正則切開，文字片段變成一般 run（格式不保留），
    佔位符片段換成圖片。用於段落被扁平化成單一 run 的情況。"""
    style_tag = _get_style_tag(source_p)
    if "heading 1" in style_tag or "heading1" in style_tag:
        target_p = target_doc.add_paragraph(style="Heading 1")
    elif "heading 2" in style_tag or "heading2" in style_tag:
        target_p = target_doc.add_paragraph(style="Heading 2")
    else:
        target_p = target_doc.add_paragraph()

    last_end = 0
    text = source_p.text
    for match in PLACEHOLDER_PATTERN.finditer(text):
        before = text[last_end:match.start()]
        if before:
            target_p.add_run(before)
        img_num = int(match.group(1))
        img_path = _find_image_file(target_dir, img_num)
        target_p.add_run().add_picture(str(img_path))
        last_end = match.end()

    remaining = text[last_end:]
    if remaining:
        target_p.add_run(remaining)

    return target_p


def _normalize_docx_filename(filename: str) -> str:
    """確保檔名有 .docx 副檔名（合併輸出的格式固定跟章節檔一致，目前只支援 docx）。"""
    filename = filename.strip()
    if not filename.lower().endswith(".docx"):
        filename += ".docx"
    return filename


def combine_docx(target_dir: str, output_filename: str, confirmed: bool = False) -> dict:
    """
    將 target_dir 內符合 NN.docx 命名規則的章節檔依序合併為一份完整文件，
    [IMG_XXX] 佔位符還原為對應圖片，輸出到同一個 target_dir 底下。

    這是一個「有去無回」的操作：合併成功後會刪除所有參與合併的章節檔與圖片檔。
    """
    if not confirmed:
        raise PermissionError("合併操作會刪除所有章節檔與圖片檔，必須經過明確確認（confirmed=True）才能執行。")

    target_path = Path(target_dir)
    if not target_path.exists() or not target_path.is_dir():
        raise FileNotFoundError(f"找不到校對資料夾：{target_dir}")

    # 第一步：找出實際參與合併的章節檔（格式一致性檢查也在這裡做）
    chapter_files = _find_chapter_files(target_path)
    excluded_files = _find_excluded_files(target_path, chapter_files)

    # 第二步：純檢查，任何佔位符對不上圖片就直接中止，不寫檔
    placeholder_nums = _collect_all_placeholders(chapter_files, target_path)

    # 第三步：實際合併
    combined_doc = Document()
    for f in chapter_files:
        source_doc = Document(str(f))
        for p in source_doc.paragraphs:
            if _paragraph_needs_text_fallback(p):
                _copy_paragraph_text_fallback(p, combined_doc, target_path)
            else:
                _copy_paragraph_run_level(p, combined_doc, target_path)

    output_name = _normalize_docx_filename(output_filename)
    output_path = target_path / output_name
    combined_doc.save(str(output_path))

    # 第四步：清理中繼檔案（只刪參與合併的章節檔跟被引用到的圖片檔，excluded_files 不動）
    for f in chapter_files:
        f.unlink()
    for num in placeholder_nums:
        img_path = _find_image_file(target_path, num)
        if img_path:
            img_path.unlink()

    return {"output_path": str(output_path), "excluded_files": excluded_files}
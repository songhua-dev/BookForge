from pathlib import Path

from .docx_parser import parse_docx
from .odt_parser import parse_odt
from .md_parser import parse_md
from .txt_parser import parse_txt

TEXT_EXTENSIONS = {".docx", ".md", ".markdown", ".txt", ".odt"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}

def parse_folder(folder_path: str, config: dict) -> dict:
    dir_path = Path(folder_path)
    if not dir_path.exists() or not dir_path.is_dir():
        raise FileNotFoundError(f"找不到指定的輸入資料夾：{folder_path}")

    text_files = [f for f in dir_path.iterdir() if f.is_file() and f.suffix.lower() in TEXT_EXTENSIONS]

    if len(text_files) == 0:
        raise FileNotFoundError(f"資料夾【{folder_path}】內找不到任何 .docx, .md, .txt 或 .odt 檔案！")
    elif len(text_files) > 1:
        file_names = [f.name for f in text_files]
        raise ValueError(f"資料夾【{folder_path}】內包含多個文字檔 ({file_names})，請保持資料夾內只有一份主稿。")

    folder_images = [f for f in dir_path.iterdir() if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS]
    target_file = text_files[0]
    ext = target_file.suffix.lower()

    # 簡化分流：直接呼叫頂層已匯入的解析器
    if ext == ".docx":
        return parse_docx(str(target_file), config, extra_images=folder_images)
    elif ext == ".odt":
        return parse_odt(str(target_file), config, extra_images=folder_images)
    elif ext in (".md", ".markdown"):
        return parse_md(str(target_file), config, extra_images=folder_images)
    elif ext == ".txt":
        return parse_txt(str(target_file), config, extra_images=folder_images)

    raise ValueError(f"不支援的檔案格式：{ext}")
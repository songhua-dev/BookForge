"""
輸出資料夾與檔名相關的工具函式。
輸出資料夾寫死在桌面的「電子書output」，不存在則自動建立。
"""
from pathlib import Path

OUTPUT_DIR = Path.home() / "Desktop" / "電子書output"


def get_output_dir() -> Path:
    """取得輸出資料夾路徑，不存在則自動建立。"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def normalize_epub_filename(filename: str) -> str:
    """確保檔名有 .epub 副檔名。"""
    filename = filename.strip()
    if not filename.lower().endswith(".epub"):
        filename += ".epub"
    return filename


def is_filename_available(filename: str) -> bool:
    """檢查輸出資料夾內是否已存在同名檔案。"""
    filename = normalize_epub_filename(filename)
    return not (get_output_dir() / filename).exists()
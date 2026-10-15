import sys
import argparse
from pathlib import Path

from config import CONFIG
from parsers import parse_folder
from epub_templates import apply_template
from builder.epub_builder import build_epub


def parse_args():
    """解析 CLI 命令列引數並動態覆寫 config.py"""
    parser = argparse.ArgumentParser(description="EPUB 自動化排版與電子書打包系統 v3.3")

    # 輸入與輸出路徑引數
    parser.add_argument("-i", "--input", type=str, default=CONFIG["DEFAULT_INPUT_DIR"], help="輸入資料夾路徑")
    parser.add_argument("-o", "--output", type=str, default=str(Path(CONFIG["DEFAULT_OUTPUT_DIR"]) / CONFIG.get("DEFAULT_OUTPUT_FILENAME", "output.epub")), help="輸出 EPUB 檔案路徑")

    # --- 所有「開關/覆寫值」型引數集中放在這裡，方便一次看完，避免之後漏改忘記 ---
    # 規格書：使用 BooleanOptionalAction 支援 --feature / --no-feature 雙向開關
    parser.add_argument("--IMAGE_PROCESSING_ENABLE", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--TEXT_PUNCTUATION_CONVERT", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--TEXT_CONVERT_COMMA", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--TEXT_CONVERT_PERIOD", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--TEXT_CONVERT_QUOTES", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--TEXT_SMART_NUMERIC_EXEMPT", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--book_title", type=str, default=None, help="書名（僅書籍路徑/多章節有效，測試用）")
    parser.add_argument("--cover", type=str, default=None, help="封面圖片路徑（僅書籍路徑有效，測試用）")

    args = parser.parse_args()

    # 將 CLI 傳入的非 None 引數動態覆寫至 runtime_config
    runtime_config = CONFIG.copy()
    for key, value in vars(args).items():
        if value is not None and key in runtime_config:
            runtime_config[key] = value

    if args.book_title:
        runtime_config["book_title"] = args.book_title
    if args.cover:
        runtime_config["cover_image_path"] = args.cover

    return args.input, args.output, runtime_config


def run_pipeline(input_dir: str, output_file: str, config: dict) -> str:
    """
    共用 pipeline 核心：parse_folder() → apply_template() → build_epub()。

    參數：
        input_dir: 待轉檔資料夾路徑（內含一份主稿 + 可選的獨立圖片檔）
        output_file: 輸出 EPUB 完整路徑（含檔名）
        config: 完整 config dict

    回傳：
        最終寫出的 EPUB 檔案路徑（字串）
    """
    # Step 1: 解析輸入資料夾（主稿文字檔 + 資料夾內獨立圖片）
    parsed_data = parse_folder(input_dir, config)

    # Step 2: 依章節數量自動選版型（單篇文章 vs 書籍），套用排版
    templated_data = apply_template(parsed_data, config)

    # Step 3: 打包成 EPUB（單篇文章/書籍兩條路徑分岔邏輯在 epub_builder.py 內部）
    final_path = build_epub(templated_data, output_file, config)

    return final_path


def main():
    """
    CLI 專屬進入點：負責讀取命令列引數、印進度訊息、統一處理例外並設定 exit code。
    """
    input_dir, output_file, config = parse_args()

    print("========================================")
    print(" 🚀 啟動 EPUB 自動化排版轉檔系統")
    print("========================================")
    print(f"📂 輸入資料夾：{input_dir}")
    print(f"📦 預計輸出檔：{output_file}")
    if config.get("book_title"):
        print(f"📖 書名（CLI 指定）：{config['book_title']}")
    print("----------------------------------------")

    try:
        print("🔍 [1/3] 正在解析輸入資料夾與圖像資產...")
        print("🎨 [2/3] 正在進行版型選擇與圖片交錯排版...")
        print("📦 [3/3] 正在編譯與打包 EPUB 電子書...")
        # 三步驟的實際執行與細節 log 全部收斂到 run_pipeline() 內部，
        # main() 只保留「現在跑到第幾步」這種粗粒度進度提示
        final_path = run_pipeline(input_dir, output_file, config)

        print("----------------------------------------")
        print(f"🎉 轉檔成功！檔案已輸出至：{final_path}")
        print("========================================")

    except Exception as e:
        print(f"\n❌ 轉檔過程發生錯誤：{str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
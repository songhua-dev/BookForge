import sys
import argparse
from pathlib import Path

from config import CONFIG
from parsers import parse_folder
from templates import apply_template
from builder.epub_builder import build_epub

def parse_args():
    """解析 CLI 命令列引數並動態覆寫 config.py"""
    parser = argparse.ArgumentParser(description="EPUB 自動化排版與電子書打包系統 v3.3")
    
    # 輸入與輸出路徑引數
    parser.add_argument("-i", "--input", type=str, default=CONFIG["DEFAULT_INPUT_DIR"], help="輸入資料夾路徑")
    parser.add_argument("-o", "--output", type=str, default=str(Path(CONFIG["DEFAULT_OUTPUT_DIR"]) / CONFIG.get("DEFAULT_OUTPUT_FILENAME", "output.epub")), help="輸出 EPUB 檔案路徑")
        
    # 規格書：使用 BooleanOptionalAction 支援 --feature / --no-feature 雙向開關
    parser.add_argument("--IMAGE_PROCESSING_ENABLE", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--TEXT_PUNCTUATION_CONVERT", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--TEXT_CONVERT_COMMA", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--TEXT_CONVERT_PERIOD", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--TEXT_CONVERT_QUOTES", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--TEXT_SMART_NUMERIC_EXEMPT", action=argparse.BooleanOptionalAction, default=None)
    
    # 版型引數
    parser.add_argument("--LAYOUT_TEMPLATE", type=str, choices=["auto", "minimal", "interleaved", "rich", "quote"], default=None)

    args = parser.parse_args()

    # 將 CLI 傳入的非 None 引數動態覆寫至 runtime_config
    runtime_config = CONFIG.copy()
    for key, value in vars(args).items():
        if value is not None and key in runtime_config:
            runtime_config[key] = value

    return args.input, args.output, runtime_config

def main():
    input_dir, output_file, config = parse_args()

    print("========================================")
    print(" 🚀 啟動 EPUB 自動化排版轉檔系統")
    print("========================================")
    print(f"📂 輸入資料夾：{input_dir}")
    print(f"📦 預計輸出檔：{output_file}")
    print(f"🎨 版型模式  ：{config['LAYOUT_TEMPLATE']}")
    print("----------------------------------------")

    try:
        # Step 1: 解析資料夾 (文字檔與獨立圖片)
        print("🔍 [1/3] 正在解析輸入資料夾與圖像資產...")
        parsed_data = parse_folder(input_dir, config)
        
        # 【關鍵修正】：避免重複計算圖片數量 (images 已包含 embedded + extra)
        images = parsed_data.get("images", [])
        if not images:
            images = parsed_data.get("embedded_images", []) + parsed_data.get("extra_images", [])
        img_count = len(images)
        
        print(f"   ✓ 成功抓取文章標題：《{parsed_data['title']}》")
        print(f"   ✓ 載入圖片資產數量：{img_count} 張")

        # Step 2: 套用智慧版型與排版注入
        print("🎨 [2/3] 正在進行版型選擇與圖片交錯排版...")
        templated_data = apply_template(parsed_data, config)
        print(f"   ✓ 已匹配版型款式：【{templated_data['template_used']}】")

        # Step 3: 打包 EPUB 檔案
        print("📦 [3/3] 正在編譯與打包 EPUB 電子書...")
        final_path = build_epub(templated_data, output_file, config)
        print("----------------------------------------")
        print(f"🎉 轉檔成功！檔案已輸出至：{final_path}")
        print("========================================")

    except Exception as e:
        print(f"\n❌ 轉檔過程發生錯誤：{str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
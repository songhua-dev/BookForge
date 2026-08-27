# BookForge — 文章轉 EPUB 自動化排版工具

一套模組化、高自訂性的 Python 工具，將單篇 `.docx` / `.md` / `.txt` / `.odt` 文章自動轉換為一份標準 EPUB 電子書檔案。所有轉換行為皆可透過 `config.py` 或 CLI 參數靈活控制。

## 功能特色

- **多格式輸入**：支援單篇 `.docx`、`.md`、`.txt`、`.odt` 文章
- **圖片自動編排**：依內文標記（`[1.jpg]`）精準置入，未標記圖片依數字順序自動勻稱插入
- **動態圖像處理管線**：格式轉換（JPEG / PNG / WEBP）、壓縮、縮放、sRGB 校正、HEIC 轉檔、EXIF 自動轉正、Alpha 透明通道白底合成
- **智慧標點清洗**：半形轉全形（逗號、句號、引號），並以「保護 → 轉換 → 還原」機制豁免小數與千分位數字（如 `3.14`、`1,000`）
- **5 種版型**：`auto`（智慧選擇）、`minimal`、`interleaved`、`rich`、`quote`，並內建雙頁閱讀器防爆頁 CSS 規範
- **標準 EPUB 產出**：自動生成 Metadata、OPF、Navigation 文件，產出單一 EPUB 檔案
- **CLI 覆寫設定**：僅覆寫使用者明確指定的參數，其餘沿用 `config.py`

## 系統需求

- Python 3.9+（使用 `argparse.BooleanOptionalAction`）
- 相依套件請見 [`requirements.txt`](./requirements.txt)

## 安裝

```bash
git clone <your-repo-url>
cd BookForge
pip install -r requirements.txt
```

## 快速開始

1. **設定輸入／輸出路徑**：開啟 `config.py`，設定 `DEFAULT_INPUT_DIR`、`DEFAULT_OUTPUT_DIR`、`DEFAULT_OUTPUT_FILENAME` 為你想要的資料夾與檔名，例如：

   ```python
   "DEFAULT_INPUT_DIR": r"C:\Users\ljls2\Desktop\input",
   "DEFAULT_OUTPUT_DIR": r"C:\Users\ljls2\Desktop\output",
   "DEFAULT_OUTPUT_FILENAME": "my_book.epub",
   ```

2. **放入檔案**：於輸入資料夾中放入
   - 1 份文字檔（`.docx` / `.md` / `.txt`），即該篇要轉換的文章
   - 該篇文章欲置入的所有圖片檔（`.jpg`、`.png`、`.webp` 等）
3. **圖片命名**：將圖片統一重新命名為純數字，如 `1.jpg`、`2.jpg`、`3.jpg`
   - 若文字檔內已嵌入圖片，優先保留原位置
   - 若內文寫有 `[1.jpg]` 標記，系統會自動將該圖片準確替換至該段落
   - 未標記的圖片將依數字順序自動勻稱插入內文段落之間
4. **執行轉檔**：

   ```bash
   python main.py
   ```

5. **取得產出**：轉檔完成後至輸出資料夾領取產出的單一 EPUB 檔案

## 設定參數（`config.py`）

| 分類 | 主要參數 | 說明 |
| --- | --- | --- |
| 路徑與檔名 | `DEFAULT_INPUT_DIR` / `DEFAULT_OUTPUT_DIR` / `DEFAULT_OUTPUT_FILENAME` / `AUTO_FILENAME_BY_TITLE` | 預設輸入輸出資料夾與輸出檔名；`AUTO_FILENAME_BY_TITLE` 開啟時自動以文章標題命名 |
| Metadata | `BOOK_TITLE` / `BOOK_AUTHOR` / `BOOK_LANGUAGE` / `BOOK_PUBLISHER` / `BOOK_COVER_IMAGE` | EPUB 書籍元數據 |
| 圖像處理 | `IMAGE_PROCESSING_ENABLE` / `IMAGE_OUTPUT_FORMAT` / `IMAGE_JPEG_QUALITY` / `IMAGE_RESIZE_ENABLE` / `IMAGE_MAX_SIDE` / `IMAGE_KEEP_ASPECT_RATIO` / `IMAGE_CONVERT_SRGB` / `IMAGE_HEIC_CONVERT` / `IMAGE_AUTO_ROTATE` | 圖片壓縮、轉檔、縮放與色彩空間處理開關 |
| 文字清洗 | `TEXT_PUNCTUATION_CONVERT` / `TEXT_CONVERT_COMMA` / `TEXT_CONVERT_PERIOD` / `TEXT_CONVERT_QUOTES` / `TEXT_SMART_NUMERIC_EXEMPT` | 標點符號全形化與數字防呆豁免 |
| 版型 | `LAYOUT_TEMPLATE` / `CHAPTER_SPLIT_BY_H1` | 版型選擇（`auto`/`minimal`/`interleaved`/`rich`/`quote`）與章節拆分規則 |

> 也支援 CLI 參數（如 `-i`、`-o`、`--image-processing-enable`）臨時覆寫 `config.py` 設定，適合單次轉檔不想改設定檔的情況；日常使用直接改 `config.py` 即可。

## 專案架構

```text
BookForge/
├── main.py                  # 主入口，CLI 解析與流程啟動
├── config.py                # 中央設定，全功能開關與 Metadata
├── parsers/                 # 各格式解析器（txt / docx / md / odt）
├── utils/
│   ├── text_cleaner.py      # 標點清洗（保護 → 轉換 → 還原）
│   └── image_processor.py   # 圖像處理管線
├── templates/                # 版型引擎與 CSS（minimal / interleaved / rich / quote）
└── builder/
    └── epub_builder.py      # 注入 XHTML、CSS、圖片資產，產出單一 EPUB 檔案
```

## 授權

本專案採用 MIT License，詳見 [LICENSE](./LICENSE)。
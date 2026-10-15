# BookForge

**BookForge** is a config-driven EPUB authoring pipeline that turns a single Word/ODT/Markdown/plain-text manuscript into a polished `.epub` file — either a single-article EPUB or a full multi-chapter book with an auto-generated table of contents and cover. It also ships a small Flask web UI so the whole workflow (including a docx split/merge proofreading helper) can be run without touching the command line.

> 這是一套以 config 設定檔驅動的 EPUB 製作工具，可以把一份 Word / ODT / Markdown / 純文字手稿，轉成排版完整的 `.epub` 電子書——不管是單篇文章，還是需要自動產生目錄、封面的多章節書籍都支援。專案裡也附了一個簡單的 Flask 網頁介面，讓你不用打指令就能操作整套流程（包含一個給人工校對用的 docx 分割／合併小工具）。

---

## Screenshot

![BookForge screenshot](sample/sample.png)

> 上面是網頁介面的截圖，實際檔案放在 `sample/sample.png`。

---

## Features

- **Two output modes, auto-detected**: a manuscript with no `Heading 1` styles is packaged as a minimal single-page EPUB (no TOC); a manuscript with multiple `Heading 1` sections is automatically packaged as a full book — auto-generated TOC, multi-chapter spine, and optional cover — with zero manual mode switching.
- **Faithful image handling for `.docx` sources**: inline images are parsed in their original run order (fixing a common bug where text sharing a paragraph with an image gets silently dropped), and each image's on-page display width is calculated from the manuscript's actual page layout, so a full-page image or a half-page image in Word keeps roughly the same visual proportion in the EPUB — instead of always rendering at native pixel size.
- **Configurable chapter title extraction**: chapter titles used in the table of contents can be the full heading text, everything before a chosen split character (useful for headings like "乾卦第一　乾上乾下" → "乾卦"), or the first N characters — controlled entirely from `config.py`, no code changes needed.
- **Text cleanup pipeline**: optional half-width → full-width punctuation conversion, with a numeric-safe mode so things like `3.14` or `1,000` aren't mangled.
- **Image processing pipeline**: optional format conversion, JPEG quality control, max-side resizing, sRGB correction, HEIC conversion, and EXIF auto-rotation — applied consistently to embedded images, folder images, and the cover.
- **Front & back matter generation**: optional auto-generated title page, copyright page (with bilingual zh/en templates, edition number, English ordinal conversion), and about-the-author page — each independently toggleable, placed correctly in reading order (cover → title page → copyright page → chapters → author bio), and excluded from the table of contents. All user-supplied text is HTML-escaped before being embedded, so stray `&`/`<`/`>` characters in a title or bio can't produce an invalid EPUB.
- **Configurable book language**: `config["BOOK_LANGUAGE"]` drives both the EPUB's language metadata and every page's `lang` attribute — default `zh-TW`, overridable per book (e.g. `en`) without touching any code.
- **A small Flask web app** (`app.py`) with two panels:
  - **eBook Builder** — upload a manuscript (+ optional cover), set a book title and output filename, optionally fill in front/back matter fields, and produce a finished `.epub` on your desktop.
  - **Proofreading helper** — split a `.docx` into per-chapter files (by Heading 1 or Heading 2) for manual proofreading (e.g. pasting into an AI chat), then merge the proofread files back into one `.docx`.
- **Multiple source formats**: `.docx` has full support (see Known Limitations for the other three).
- **EPUBCheck-clean output**: validated against real-world distributor requirements (Apple Books, B&N, Kobo, OverDrive, etc. via Draft2Digital) — notably avoids the CSS `:has()` selector, which EPUBCheck's CSS validator rejects outright even though it renders fine in modern browsers/readers.

> 主要功能：（1）自動判斷單篇文章或多章節書籍，不用手動切換模式；（2）針對 docx 圖片做了保序解析跟顯示比例還原，讓整頁大圖或局部圖片在電子書裡維持接近原稿的視覺比例；（3）章節標題擷取規則（完整標題／依字元截斷／取前 N 字）完全由 config 控制；（4）文字標點符號全半形轉換、圖片格式/畫質/尺寸處理都是可開關的管道；（5）選填的書名頁／版權頁／作者介紹頁，各自獨立開關、排序正確、不會出現在目錄裡，使用者輸入的文字都會做 HTML 跳脫處理；（6）書籍語言可由 config 設定，不寫死；（7）附一個 Flask 網頁介面，包含「電子書製作器」跟給人工校對用的「分割／合併」小工具；（8）輸出的 EPUB 已經過 EPUBCheck 驗證可以正常上架。目前只有 `.docx` 是完整支援，其餘三種格式的限制請見下方「Known Limitations」。

---

## Project Structure

```
BookForge/
├── app.py                  # Flask web app entry point
├── main.py                 # CLI entry point + shared run_pipeline() core
├── config.py                # All tunable settings live here
├── output_utils.py          # Output folder / filename helpers
├── separate.py               # Splits a .docx into per-chapter files
├── combine.py                # Merges per-chapter .docx files back into one
├── requirements.txt
├── LICENSE
├── README.md
├── sample/
│   └── sample.png            # Screenshot used above
├── templates/                # Flask HTML templates (web UI)
│   └── index.html
├── epub_templates/           # EPUB layout templates + CSS (unrelated to templates/ above)
│   ├── __init__.py
│   ├── template_engine.py    # Auto image layout logic for the single-article templates below
│   ├── raw.css                # Used for the book path (multi-chapter)
│   ├── minimal.css            # Single-article template: no images
│   ├── quote.css               # Single-article template: 1 image
│   ├── interleaved.css         # Single-article template: 2–3 images
│   └── rich.css                 # Single-article template: 4+ images
├── parsers/
│   ├── __init__.py           # Dispatches by file extension
│   ├── docx_parser.py        # Full support
│   ├── odt_parser.py         # Partial support
│   ├── md_parser.py          # Partial support
│   └── txt_parser.py         # Partial support
├── builder/
│   ├── __init__.py
│   └── epub_builder.py       # Assembles the final .epub
└── utils/
    ├── __init__.py
    ├── text_cleaner.py
    └── image_processor.py
```

> 這是目前整個專案預期的資料夾結構。`templates/`（Flask 網頁樣板）跟 `epub_templates/`（EPUB 排版樣式）是兩個完全不同用途、刻意分開命名的資料夾，不要搞混。`epub_templates/` 裡的四個版型 CSS（`minimal`/`quote`/`interleaved`/`rich`）跟 `template_engine.py` 是單篇文章路徑專用的自動圖片排版邏輯，依圖片數量自動選版型；書籍路徑（多章節）一律走 `raw.css`，不會用到這四個檔案。目前都是能動的功能，予以保留，不因為近期主要在做書籍轉檔就刪除。

---

## Requirements

- Python 3.10+
- See `requirements.txt`: Flask, python-docx, markdown, beautifulsoup4, ebooklib, Pillow

> 需要 Python 3.10 以上版本，套件清單都寫在 `requirements.txt` 裡。

---

## Installation

```bash
git clone <your-repo-url>
cd BookForge
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

> 標準的 clone → 建虛擬環境 → 安裝套件流程，Windows 跟 macOS/Linux 的啟用指令不同，照你的系統選一行執行。

---

## Usage

### Web app (recommended)

```bash
python app.py
```

Then open `http://127.0.0.1:5000` in your browser. Use the **eBook Builder** panel to upload a manuscript and produce an `.epub`, or the **Proofreading** panel to split/merge `.docx` chapter files. Output files are written to `~/Desktop/電子書output/` (configurable in `config.py`).

> 執行 `python app.py` 後，用瀏覽器打開網址即可操作。「電子書製作器」面板用來上傳手稿產出 EPUB，「電子書校對」面板用來分割/合併 docx 章節檔。輸出資料夾寫在 `config.py` 裡，預設是桌面的「電子書output」資料夾。

### Command line

```bash
python main.py -i <input_folder> -o <output_file.epub>
```

The input folder should contain exactly one manuscript file (`.docx`/`.odt`/`.md`/`.txt`) plus, optionally, loose image files to be laid out alongside the text. Run `python main.py --help` for the full list of override flags (image processing toggles, text-cleanup toggles, `--book_title`, `--cover`).

> CLI 模式的輸入資料夾裡只能放一份手稿檔案，可以額外放獨立的圖片檔案一起排版。`python main.py --help` 可以看到所有可用的命令列參數（圖片處理開關、文字清洗開關、`--book_title`、`--cover` 等）。

---

## Configuration (`config.py`)

All behavior is controlled from a single `CONFIG` dictionary — no need to touch parser/builder code for routine adjustments:

| Key | Purpose |
|---|---|
| `IMAGE_PROCESSING_ENABLE`, `IMAGE_OUTPUT_FORMAT`, `IMAGE_JPEG_QUALITY`, `IMAGE_RESIZE_ENABLE`, `IMAGE_MAX_SIDE`, `IMAGE_CONVERT_SRGB`, `IMAGE_HEIC_CONVERT`, `IMAGE_AUTO_ROTATE` | Image processing pipeline toggles/parameters |
| `TEXT_PUNCTUATION_CONVERT` and related `TEXT_CONVERT_*` keys | Half-width → full-width punctuation conversion rules |
| `CHAPTER_TITLE_EXTRACT_MODE` (`FULL` / `BEFORE_SPLIT_CHAR` / `FIRST_N_CHARS`), `CHAPTER_TITLE_SPLIT_CHAR`, `CHAPTER_TITLE_MAX_LENGTH` | How chapter titles are derived from `Heading 1` text for the table of contents |
| `CHAPTER_SPLIT_BY_H1` | Reserved for a future `separate.py` config-driven mode; not currently read by any code |
| `DEFAULT_INPUT_DIR`, `DEFAULT_OUTPUT_DIR`, `DEFAULT_OUTPUT_FILENAME`, `PROOFREAD_DIR` | Default folder paths (CLI + the proofreading helper) |

> `config.py` 是整個專案唯一的設定入口，日常調整幾乎都不用碰程式邏輯。表格列出目前所有的設定 key 跟用途，其中 `CHAPTER_SPLIT_BY_H1` 目前是保留欄位，還沒有任何程式碼讀取它。

---

## Known Limitations

- **`.docx` is the only fully-supported format.** `.odt` only ever produces a single chapter (no chapter splitting, no image-width-ratio calculation). `.md` and `.txt` are also always single-chapter, with no heading hierarchy beyond a single title line.
- **No table-based layout support.** Content inside Word tables is not read at all — if a manuscript uses a table to lay out an image next to a caption, that entire table is silently skipped.
- **Text-wrapped ("floating") images are not reliably supported.** Only inline images (anchored directly in the text flow) parse correctly with guaranteed order; floating/anchored images may parse out of their intended visual position.
- **Single page-layout assumption.** Image display-width calculation assumes the whole document uses one consistent page/margin setup; a manuscript that switches page orientation or margins mid-document will produce inaccurate image sizing for the affected sections.
- **The split/merge proofreading tool only supports `.docx`.** Files of any other extension in the proofreading folder will abort the merge with an error rather than being processed.
- **Cover page may be followed by a near-blank page on some readers at narrow/small screen sizes.** This is a known, accepted limitation, not a bug in the stylesheet: it traces back to the well-documented "100vh lies on mobile" CSS quirk (the viewport-height unit can report more space than is actually visible once a reader's own UI chrome is accounted for), and the usual modern fixes (`svh`/`dvh` units, the `:has()` selector) are not usable here because EPUBCheck's CSS validator — required to pass for Apple Books/B&N/Kobo/OverDrive distribution — rejects them as parse errors. `raw.css` uses a `96vh` safety margin as a partial mitigation; a worse-but-safe value can be tuned further if needed, but a small residual risk on some readers is accepted rather than invested in further.

> 目前只有 `.docx` 是完整支援的格式；`.odt`/`.md`/`.txt` 都只能產出單一章節，功能明顯陽春。完全不支援 Word 表格排版（表格內容會被整段忽略，不是排錯是直接消失），文繞圖也無法保證正確順序。圖片比例計算假設全文只有一種版面設定。分割/合併校對工具目前只吃 `.docx`。封面在部分閱讀器的小螢幕模式下，後面可能會多出一頁幾乎空白的頁面——這是已知且接受的限制，根源是行動裝置上知名的「100vh 計算偏差」問題，而業界標準解法（`svh`/`dvh` 單位、`:has()` 選擇器）這裡都用不了，因為 EPUBCheck（上架 Apple/B&N/Kobo/OverDrive 必須通過的驗證工具）會直接判定這些較新的 CSS 語法錯誤。目前用 `96vh` 留一點安全邊界做部分緩解，數值還可以再調整，但已經決定不再為了這個小問題繼續投入。

---

## Roadmap

- Table-based layout support (read `doc.tables`, not just `doc.paragraphs`)
- `.odt` chapter-splitting + image-ratio support (likely via a LibreOffice headless docx round-trip rather than hand-rolled ODF writing)

> 未來可能的擴充方向：支援表格排版、補齊 `.odt` 的章節切分跟圖片比例功能（規劃走 LibreOffice headless 轉檔的路線）。書籍語言／國際化已經完成，不再列在這裡。

---

## License

Released under the MIT License — see `LICENSE`. You're welcome to use, modify, and redistribute this project.

> 採用 MIT 授權（詳見 `LICENSE`），歡迎自由引用、修改、轉發。
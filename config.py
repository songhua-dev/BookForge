# BookForge - Centralized Config v3.3

CONFIG = {
    # --- 1. 資料夾路徑預設值 ---
    "DEFAULT_INPUT_DIR": r"C:\Users\ljls2\Desktop\input",    # 預設放置待轉檔 (.md / .docx / .txt) 的資料夾
    "DEFAULT_OUTPUT_DIR": r"C:\Users\ljls2\Desktop\output",  # 預設產出 EPUB 的資料夾
    "DEFAULT_OUTPUT_FILENAME": "my_book.epub",    # 預設產出 EPUB 的檔名
    "PROOFREAD_DIR": r"C:\Users\ljls2\Desktop\電子書校對",
    "cc_output_dir": r"C:\Users\ljls2\Desktop\簡繁轉換output", # [新增] 簡繁體轉換專用輸出資料夾

    # --- 2. 簡繁體轉換設定 (OpenCC) ---
    "convert_chinese_enable": False, # [新增/開關] 是否啟用簡繁體轉換
    "convert_chinese_mode": "t2s",   # [新增/參數] "t2s" (繁轉簡) / "s2t" (簡轉繁) / "t2tw" (繁轉台灣正體)

    # --- 3. 圖像處理管道開關與參數 ---
    "IMAGE_PROCESSING_ENABLE": True,   # [開關] 是否啟用圖像處理管道（False 則原檔直出）
    "IMAGE_OUTPUT_FORMAT": "JPEG",     # [參數] "JPEG" / "PNG" / "WEBP" / "KEEP"（保持原格式）
    "IMAGE_JPEG_QUALITY": 85,          # [參數] JPEG 壓縮品質 (1-100)，100 為無損輸出
    "IMAGE_RESIZE_ENABLE": True,       # [開關] 是否啟用解析度自動縮放
    "IMAGE_MAX_SIDE": 1200,            # [參數] 長邊最大像素值 (px)
    "IMAGE_KEEP_ASPECT_RATIO": True,   # [開關] 縮放時是否保持原圖長寬比例
    "IMAGE_CONVERT_SRGB": True,        # [開關] 是否將 Display P3 / RGBA 校正為 sRGB
    "IMAGE_HEIC_CONVERT": True,        # [開關] 是否將 Apple HEIC/HEIF 轉為標準格式
    "IMAGE_AUTO_ROTATE": True,         # [開關] 是否依 EXIF 自動轉正圖片方向

    # --- 4. 文字清洗與標點符號全型轉換開關 ---
    "TEXT_PUNCTUATION_CONVERT": True,  # [開關] 是否啟用標點符號半型轉全型
    "TEXT_CONVERT_COMMA": True,        # [開關] , -> ，
    "TEXT_CONVERT_PERIOD": True,       # [開關] . -> 。
    "TEXT_CONVERT_QUOTES": True,       # [開關] "..." -> 「...」
    "TEXT_SMART_NUMERIC_EXEMPT": True, # [開關] 1,000 / 3.14 等數字格式防呆豁免

    # --- 5. 章節切分與目錄標題設定 ---
    # [separate.py 專用開關] 是否依 H1 將文件/HTML 拆成獨立章節。
    # docx_parser.py 不使用此設定決定「標題要擷取多少內容」。
    "CHAPTER_SPLIT_BY_H1": True,
    # [docx_parser.py] H1 擷取為章節/目錄標題時的規則。
    # "CHAPTER_TITLE_SPLIT_CHAR"：取指定字元前的文字，例如「乾卦第一」→「乾卦」
    # "FULL"：使用完整 H1
    "CHAPTER_TITLE_EXTRACT_MODE": "FULL",
    "CHAPTER_TITLE_SPLIT_CHAR": "第",
    "CHAPTER_TITLE_MAX_LENGTH": 20,

    # --- 6. 語系與前置/後置頁面（Front/Back Matter）設定 ---
    "BOOK_LANGUAGE": "zh-TW",   # [參數] 書籍語言標籤（EPUB metadata + 每頁 lang 屬性）

    # [書名頁 (Title Page)]
    "enable_title_page": True,         # [開關] 是否生成書名頁（預設：啟用）
    "book_author": "",                 # [參數] 作者或整理者姓名
    "book_publisher": "",              # [參數] 出版社或發行單位名稱（選填）
    "book_publish_year": "2026",       # [參數] 出版年份（預設當前西元年）

    # [版權頁 (Copyright Page)]
    "enable_copyright_page": True,     # [開關] 是否生成版權頁（預設：啟用）
    "copyright_holder": "",            # [參數] 著作權持有者名稱（預設帶入 book_author）
    "copyright_publish_date": "",      # [參數] 具體出版日期（對應日曆選擇框格式，例：2026-10-05）
    "copyright_edition_number": 1,     # [參數] 刷次（正整數，預設：1）
    "copyright_language": "zh",        # [參數] 版權頁語系範本："zh"（中文） / "en"（英文）

    # [作者介紹頁 (About the Author)]
    "enable_author_page": False,       # [開關] 是否生成作者介紹頁（預設：停用/選填）
    "author_bio_text": "",             # [參數] 作者簡介內文（多段落文字）
}
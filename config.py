# BookForge - Centralized Config v3.2

CONFIG = {
    # --- 1. 圖像處理管道開關與參數 ---
    "IMAGE_PROCESSING_ENABLE": True,   # [開關] 是否啟用圖像處理管道（False 則原檔直出）
    "IMAGE_OUTPUT_FORMAT": "JPEG",     # [參數] "JPEG" / "PNG" / "WEBP" / "KEEP"（保持原格式）
    "IMAGE_JPEG_QUALITY": 85,          # [參數] JPEG 壓縮品質 (1-100)，100 為無損輸出
    "IMAGE_RESIZE_ENABLE": True,       # [開關] 是否啟用解析度自動縮放
    "IMAGE_MAX_SIDE": 1200,            # [參數] 長邊最大像素值 (px)
    "IMAGE_KEEP_ASPECT_RATIO": True,   # [開關] 縮放時是否保持原圖長寬比例
    "IMAGE_CONVERT_SRGB": True,        # [開關] 是否將 Display P3 / RGBA 校正為 sRGB
    "IMAGE_HEIC_CONVERT": True,        # [開關] 是否將 Apple HEIC/HEIF 轉為標準格式
    "IMAGE_AUTO_ROTATE": True,         # [開關] 是否依 EXIF 自動轉正圖片方向

    # --- 2. 文字清洗與標點符號全型轉換開關 ---
    "TEXT_PUNCTUATION_CONVERT": True,  # [開關] 是否啟用標點符號半型轉全型
    "TEXT_CONVERT_COMMA": True,        # [開關] , -> ，
    "TEXT_CONVERT_PERIOD": True,       # [開關] . -> 。
    "TEXT_CONVERT_QUOTES": True,       # [開關] "..." -> 「...」
    "TEXT_SMART_NUMERIC_EXEMPT": True, # [開關] 1,000 / 3.14 等數字格式防呆豁免

    # --- 3. 版型與打包開關 ---
    "LAYOUT_TEMPLATE": "auto",         # [參數] "auto" / "minimal" / "interleaved" / "rich" / "quote"
    "CHAPTER_SPLIT_BY_H1": True,       # [開關] 是否以 H1 標題強制拆分 HTML 頁面

    # --- 4. 資料夾路徑預設值 ---
    "DEFAULT_INPUT_DIR": r"C:\Users\ljls2\Desktop\input",    # 預設放置待轉檔 (.md / .docx / .txt) 的資料夾
    "DEFAULT_OUTPUT_DIR": r"C:\Users\ljls2\Desktop\output",  # 預設產出 EPUB 的資料夾
    "DEFAULT_OUTPUT_FILENAME": "my_book.epub",    # 預設產出 EPUB 的檔名
}

# BookForge - Centralized Config v3.4

CONFIG = {
    # --- 1. 資料夾路徑預設值 ---
    "DEFAULT_INPUT_DIR": r"C:\Users\ljls2\Desktop\input",    # 預設放置待轉檔 (.md / .docx / .txt) 的資料夾
    "DEFAULT_OUTPUT_DIR": r"C:\Users\ljls2\Desktop\output",  # 預設產出 EPUB 的資料夾
    "DEFAULT_OUTPUT_FILENAME": "my_book.epub",    # 預設產出 EPUB 的檔名
    "PROOFREAD_DIR": r"C:\Users\ljls2\Desktop\電子書校對",
    "cc_output_dir": r"C:\Users\ljls2\Desktop\簡繁轉換output", # [新增] 簡繁體轉換專用輸出資料夾（app.py 的簡繁互換路由已改為讀取此設定）

    # --- 2. 簡繁體轉換設定 (OpenCC) ---
    "convert_chinese_enable": False, # [新增/開關] 是否啟用簡繁體轉換
    "convert_chinese_mode": "t2s",   # [新增/參數] "t2s" (繁轉簡) / "s2t" (簡轉繁) / "t2tw" (繁轉台灣正體)；也是簡繁互換面板的後端預設模式

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
    "TEXT_CONVERT_QUOTES": True,       # [開關] "..." -> 「...」（注意：簡體中文習慣用 “…”，目前尚未依語言分流）
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

# --- 6. 語系與多語言 Profiles 設定 (MVP: zh-TW / zh-CN) ---
    "BOOK_LANGUAGE": "zh-TW",   # [預設參數] 書籍語言代碼，必須是下方 LANGUAGE_PROFILES 的 key（下拉選單與後端白名單都由 LANGUAGE_PROFILES 產生）

    # 語言 Profile 設定表：統一管理前後文文字範本
    # 新增語言只要在這裡加一筆，不用動 app.py / index.html / epub_builder.py。
    # epub_builder.py 會以 zh-TW 為底、再用選定語言的值覆蓋，缺 key 時自動降級回 zh-TW。
    # 含 {大括號} 的值是格式字串，佔位符名稱不可改動。
    "LANGUAGE_PROFILES": {
        "zh-TW": {
            "name": "繁體中文",
            # 書名頁
            "title_page_title": "書名頁",                                        # 書名頁的頁面標題（<title> 與閱讀器顯示用）
            "title_page_publisher_year_format": "{publisher} 出版，{year} 年。",  # 有出版者且有年份
            "title_page_publisher_format": "{publisher} 出版。",                 # 只有出版者
            "title_page_year_format": "{year} 年。",                             # 只有年份
            # 版權頁
            "copyright_page_title": "版權頁",
            "copyright_disclaimer": "本著作受著作權法保護。未經著作權人書面許可，不得以任何形式或手段進行翻印、轉載、錄製或傳播。",
            "book_title_format": "《{title}》",
            "copyright_edition_format": "第 {edition} 版",
            "copyright_edition_line_format": "{edition}：{date}",                
            "copyright_statement": "© {year} {holder}. 保留所有權利。",
            "copyright_statement_no_year": "© {holder}",                         
            "copyright_author_line_format": "作者：{author}",
            # 作者介紹頁
            "author_page_title": "關於作者",                                     
            "author_page_item_title": "作者介紹",                                
            # 備用文字
            "chapter_fallback_title": "第 {n} 章",                              
            "empty_chapter_text": "內文無文字內容。",                           
            "single_fallback_title": "正文",                                    
            # 日期
            "date_format": "{year} 年 {month} 月 {day} 日",
        },
        "zh-CN": {
            "name": "简体中文",
            # 书名页
            "title_page_title": "书名页",
            "title_page_publisher_year_format": "{publisher} 出版，{year} 年。",
            "title_page_publisher_format": "{publisher} 出版。",
            "title_page_year_format": "{year} 年。",
            # 版权页
            "copyright_page_title": "版权页",
            "copyright_disclaimer": "本著作受版权法保护。未经版权人书面许可，不得以任何形式或手段进行翻印、转载、录制或传播。",
            "book_title_format": "《{title}》",
            "copyright_edition_format": "第 {edition} 版",
            "copyright_edition_line_format": "{edition}：{date}",
            "copyright_statement": "© {year} {holder}. 保留所有权利。",
            "copyright_statement_no_year": "© {holder}",
            "copyright_author_line_format": "作者：{author}",
            # 作者介绍页
            "author_page_title": "关于作者",
            "author_page_item_title": "作者介绍",
            # 备用文字
            "chapter_fallback_title": "第 {n} 章",
            "empty_chapter_text": "正文无文字内容。",
            "single_fallback_title": "正文",
            # 日期
            "date_format": "{year} 年 {month} 月 {day} 日",
        },
    },

    # [書名頁 (Title Page)]
    "enable_title_page": True,         # [開關] 是否生成書名頁（預設：啟用）
    "book_author": "",                 # [參數] 作者或整理者姓名（書名頁、版權頁共用；任一啟用時必填）
    "book_publisher": "",              # [參數] 出版社或發行單位名稱（選填）
    "book_publish_year": "2026",       # [參數] 出版年份（預設當前西元年）

    # [版權頁 (Copyright Page)]
    "enable_copyright_page": True,     # [開關] 是否生成版權頁（預設：啟用）
    "copyright_holder": "",            # [參數] 著作權持有者名稱（預設帶入 book_author）
    "copyright_publish_date": "",      # [參數] 具體出版日期（對應日曆選擇框格式，例：2026-10-05）
    "copyright_edition_number": 1,     # [參數] 刷次（正整數，預設：1）

    # [作者介紹頁 (About the Author)]
    "enable_author_page": False,       # [開關] 是否生成作者介紹頁（預設：停用/選填）
    "author_bio_text": "",             # [參數] 作者簡介內文（多段落文字）
}
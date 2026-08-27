from pathlib import Path
import ebooklib
from ebooklib import epub

def build_epub(templated_data: dict, output_path: str, config: dict) -> str:
    """
    EPUB 打包模組：
    完全不生成書名 Metadata 與目錄 (TOC / NCX / Nav)
    只輸出純粹的內文頁面與圖片資源
    """
    book = epub.EpubBook()

    # 1. 不設定書名 Metadata（設為空白）
    book.set_identifier(f"epub_builder_{Path(output_path).stem}")
    book.set_title("")
    book.set_language("zh-TW")

    # 2. 寫入 CSS 樣式檔
    css_content = templated_data.get("css_content", "")
    nav_css = epub.EpubItem(
        uid="style_default",
        file_name="style/default.css",
        media_type="text/css",
        content=css_content.encode("utf-8")
    )
    book.add_item(nav_css)

    # 3. 寫入實體圖片檔案至 EPUB (OEBPS/images/)
    images = templated_data.get("images", [])
    for img in images:
        filename = img.get("filename", "image.jpg")
        ext = filename.split(".")[-1].lower()
        
        # 相容兩種二進位資料 key (bytes_data 或 data)
        bytes_data = img.get("bytes_data") or img.get("data")
        if not bytes_data:
            continue

        img_item = epub.EpubItem(
            uid=f"img_{filename}",
            file_name=f"images/{filename}",
            media_type=f"image/{'jpeg' if ext in ('jpg', 'jpeg') else ext}",
            content=bytes_data
        )
        book.add_item(img_item)

    # 4. 建立文章主頁面 (Chapter)
    html_body = templated_data.get("final_html") or templated_data.get("content_html", "")
    
    if not html_body or not html_body.strip():
        html_body = "<p>內文無文字內容。</p>"

    # XHTML head title 保持空白
    full_html = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="zh-TW">
<head>
    <meta charset="utf-8"/>
    <title></title>
    <link rel="stylesheet" href="style/default.css" type="text/css"/>
</head>
<body>
    {html_body}
</body>
</html>"""

    chapter = epub.EpubHtml(
        title="",
        file_name="chap_01.xhtml",
        lang="zh-TW"
    )
    chapter.content = full_html.encode("utf-8")
    chapter.add_item(nav_css)
    book.add_item(chapter)

    # 5. 完全移除目錄 (TOC / NCX / Nav)，Spine 僅保留純內文
    book.spine = [chapter]

    # 6. 打包輸出檔案
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    epub.write_epub(str(out_file), book, {})

    return str(out_file)
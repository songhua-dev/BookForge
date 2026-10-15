from html import escape
from pathlib import Path
import ebooklib
from ebooklib import epub
from utils.image_processor import process_image


def _make_chapter_filename(index: int) -> str:
    return f"chap_{index:02d}.xhtml"


def _to_english_ordinal(n: int) -> str:
    """將阿拉伯數字轉換為英文序數（1=>First, 21=>21st）。"""
    ordinals_map = {
        1: "First", 2: "Second", 3: "Third", 4: "Fourth", 5: "Fifth",
        6: "Sixth", 7: "Seventh", 8: "Eighth", 9: "Ninth", 10: "Tenth",
        11: "Eleventh", 12: "Twelfth", 13: "Thirteenth", 14: "Fourteenth",
        15: "Fifteenth", 16: "Sixteenth", 17: "Seventeenth", 18: "Eighteenth",
        19: "Nineteenth", 20: "Twentieth"
    }
    if n in ordinals_map:
        return ordinals_map[n]

    # 處理大於 20 的數字後綴（如 21st, 22nd, 23rd, 24th...）
    suffix = "th"
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        remainder = n % 10
        if remainder == 1:
            suffix = "st"
        elif remainder == 2:
            suffix = "nd"
        elif remainder == 3:
            suffix = "rd"

    return f"{n}{suffix}"


def _build_title_page_html(config: dict, book_language: str) -> str:
    """
    生成「書名頁 (Title Page)」HTML。
    """
    title = escape(config.get("book_title", ""))
    author = escape(config.get("book_author", ""))
    publisher = escape(config.get("book_publisher", ""))
    year = escape(str(config.get("book_publish_year", "")))

    publisher_html = ""
    if publisher:
        lang = config.get("copyright_language", "zh")
        if lang == "en":
            pub_str = f"Published by {publisher}"
            if year:
                pub_str += f", {year}."
            else:
                pub_str += "."
        else:
            pub_str = f"{publisher} 出版"
            if year:
                pub_str += f"，{year} 年。"
            else:
                pub_str += "。"
        publisher_html = f'<p class="title-page-publisher">{pub_str}</p>'

    return f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="{book_language}">
<head>
    <meta charset="utf-8"/>
    <title>書名頁</title>
    <link rel="stylesheet" href="style/default.css" type="text/css"/>
</head>
<body>
    <div class="title-page">
        <h1 class="title-page-title">{title}</h1>
        <p class="title-page-author">{author}</p>
        {publisher_html}
    </div>
</body>
</html>"""


def _build_copyright_page_html(config: dict, book_language: str) -> str:
    """生成「版權頁 (Copyright Page)」HTML。"""
    lang = config.get("copyright_language", "zh")
    title = escape(config.get("book_title", ""))
    author = escape(config.get("book_author", ""))
    holder = escape(config.get("copyright_holder") or config.get("book_author", ""))
    pub_date = escape(config.get("copyright_publish_date", ""))
    year = escape(str(config.get("book_publish_year", "")))
    edition_num = config.get("copyright_edition_number", 1)

    if lang == "en":
        disclaimer = "While every precaution has been taken in the preparation of this book, the publisher assumes no responsibility for errors or omissions, or for damages resulting from the use of the information contained herein."
        title_line = f'<p class="copyright-book-title">{title}</p>'
        ordinal_str = _to_english_ordinal(edition_num)
        edition_line = f'<p class="copyright-edition">{ordinal_str} edition. {pub_date}.</p>'
        copy_line = f'<p class="copyright-notice">Copyright © {year} {holder}.</p>' if year else f'<p class="copyright-notice">Copyright © {holder}.</p>'
        author_line = f'<p class="copyright-author">Written by {author}.</p>'
    else:
        disclaimer = "本書編製過程已採取一切預防措施，若仍有疏漏或錯誤，出版者與作者對於因使用本書資訊所導致之損害概不負責。"
        title_line = f'<p class="copyright-book-title">《{title}》</p>'
        edition_line = f'<p class="copyright-edition">第 {edition_num} 版：{pub_date}.</p>'
        copy_line = f'<p class="copyright-notice">版權所有 © {year} {holder}</p>' if year else f'<p class="copyright-notice">版權所有 © {holder}</p>'
        author_line = f'<p class="copyright-author">作者：{author}</p>'

    return f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="{book_language}">
<head>
    <meta charset="utf-8"/>
    <title>版權頁</title>
    <link rel="stylesheet" href="style/default.css" type="text/css"/>
</head>
<body>
    <div class="copyright-page">
        <p class="copyright-disclaimer">{disclaimer}</p>
        {title_line}
        {edition_line}
        {copy_line}
        {author_line}
    </div>
</body>
</html>"""


def _build_author_page_html(config: dict, book_language: str) -> str:
    """生成「作者介紹頁 (About the Author)」HTML。

    使用者最可能在這裡打英文書名、網址、& 符號這類內容，風險最高，逐段 escape 之後才包成 <p>。"""
    lang = config.get("copyright_language", "zh")
    page_title = "About the Author" if lang == "en" else "關於作者"
    bio_text = config.get("author_bio_text", "")

    # 解析多段落換行符，每一段先 escape 再包裹為 <p class="author-bio-p">
    paragraphs = bio_text.splitlines()
    bio_html_list = []
    for p in paragraphs:
        p_str = p.strip()
        if p_str:
            bio_html_list.append(f'<p class="author-bio-p">{escape(p_str)}</p>')
    bio_html = "\n        ".join(bio_html_list)

    return f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="{book_language}">
<head>
    <meta charset="utf-8"/>
    <title>{page_title}</title>
    <link rel="stylesheet" href="style/default.css" type="text/css"/>
</head>
<body>
    <div class="author-page">
        <h2 class="author-page-title">{page_title}</h2>
        {bio_html}
    </div>
</body>
</html>"""


def build_epub(templated_data: dict, output_path: str, config: dict) -> str:
    # 書籍語言：預設維持 "zh-TW"（相容既有行為），未來 Flask 上若加了
    # 「書籍語系」選單，使用者選英文時把 config["BOOK_LANGUAGE"] 設成
    # "en" 之類的值即可。這個值同時也決定每個章節 XHTML的 lang 屬性，確保整本書的語言標籤前後一致。
    book_language = config.get("BOOK_LANGUAGE", "zh-TW")

    book = epub.EpubBook()
    book.set_identifier(f"epub_builder_{Path(output_path).stem}")
    book.set_language(book_language)

    # 1. 寫入 CSS
    css_content = templated_data.get("css_content", "")
    style_css = epub.EpubItem(
        uid="style_default",
        file_name="style/default.css",
        media_type="text/css",
        content=css_content.encode("utf-8")
    )
    book.add_item(style_css)

    # 2. 寫入圖片
    images = templated_data.get("images", [])
    for img in images:
        filename = img.get("filename", "image.jpg")
        ext = filename.split(".")[-1].lower()
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

    # 3. 取得章節資料
    chapters_data = templated_data.get("chapters", [])
    if not chapters_data:
        html_body = templated_data.get("final_html") or templated_data.get("content_html", "")
        chapters_data = [{"title": templated_data.get("title", "正文"), "html": html_body}]

    is_single_article = len(chapters_data) <= 1

    # 4. 書名
    if is_single_article:
        book.set_title("")
    else:
        book_title = config.get("book_title") or templated_data.get("title") or Path(output_path).stem
        book.set_title(book_title)

    epub_chapters = []
    toc_structure = [] 

    # 5. 建立章節
    for i, chapter_data in enumerate(chapters_data, 1):
        chapter_title = "" if is_single_article else (chapter_data.get("title") or f"第 {i} 章")
        html_body = chapter_data.get("html", "").strip()
        if not html_body:
            html_body = "<p>內文無文字內容。</p>"

        file_name = _make_chapter_filename(i)

        full_html = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="{book_language}">
<head>
    <meta charset="utf-8"/>
    <title>{chapter_title}</title>
    <link rel="stylesheet" href="style/default.css" type="text/css"/>
</head>
<body>
    {html_body}
</body>
</html>"""

        chapter = epub.EpubHtml(
            title=chapter_title,
            file_name=file_name,
            lang=book_language
        )
        chapter.content = full_html.encode("utf-8")
        chapter.add_item(style_css)

        book.add_item(chapter)
        epub_chapters.append(chapter)

        # 明確將 Link 物件存入 toc_structure，確保 ebooklib 生成正確的檔名連結
        toc_structure.append(epub.Link(file_name, chapter_title, f"toc_{i:02d}"))

    # 5.5 建立前置/後置頁面（Front & Back Matter）
    # 這些獨立頁面僅加入 spine 排序，不放入 toc_structure，確保目錄不包含前置/後置頁面
    title_page_item = None
    copyright_page_item = None
    author_page_item = None

    if not is_single_article:
        # 1. 書名頁 (Title Page)
        if config.get("enable_title_page"):
            t_html = _build_title_page_html(config, book_language)
            title_page_item = epub.EpubHtml(
                title="書名頁",
                file_name="title_page.xhtml",
                lang=book_language
            )
            title_page_item.content = t_html.encode("utf-8")
            title_page_item.add_item(style_css)
            book.add_item(title_page_item)

        # 2. 版權頁 (Copyright Page)
        if config.get("enable_copyright_page"):
            c_html = _build_copyright_page_html(config, book_language)
            copyright_page_item = epub.EpubHtml(
                title="版權頁",
                file_name="copyright_page.xhtml",
                lang=book_language
            )
            copyright_page_item.content = c_html.encode("utf-8")
            copyright_page_item.add_item(style_css)
            book.add_item(copyright_page_item)

        # 3. 作者介紹頁 (About the Author Page)
        if config.get("enable_author_page"):
            a_html = _build_author_page_html(config, book_language)
            author_page_item = epub.EpubHtml(
                title="作者介紹",
                file_name="author_page.xhtml",
                lang=book_language
            )
            author_page_item.content = a_html.encode("utf-8")
            author_page_item.add_item(style_css)
            book.add_item(author_page_item)
    elif config.get("enable_title_page") or config.get("enable_copyright_page") or config.get("enable_author_page"):
        print("⚠️ 單篇文章（無標題1章節）不會產生書名頁/版權頁/作者介紹頁，"
              "這些設定已被忽略。")

    # 6. 封面處理
    cover_added = False
    if not is_single_article:
        cover_path = config.get("cover_image_path")
        if cover_path:
            cover_file = Path(cover_path)
            if cover_file.exists():
                with open(cover_file, "rb") as f:
                    raw_cover_bytes = f.read()

                cover_bytes, cover_ext = process_image(raw_cover_bytes, config)
                cover_filename = f"cover.{cover_ext}"

                book.set_cover(cover_filename, cover_bytes)
                cover_added = True

                cover_item = book.get_item_with_id("cover")
                if cover_item is not None:
                    cover_item.add_item(style_css)
                    cover_item.is_linear = True
            else:
                print(f"⚠️ 找不到封面圖片：{cover_path}，將略過封面掛載。")

    # 7. 目錄與 Spine
    if is_single_article:
        book.spine = epub_chapters
    else:
        book.toc = tuple(toc_structure)
        book.add_item(epub.EpubNcx())

        nav = epub.EpubNav()
        nav.add_item(style_css)
        book.add_item(nav)

        # 組合 Spine 閱讀順序：
        # 封面 -> 書名頁 -> 版權頁 -> 正文章節 -> 作者介紹頁
        spine = ["cover"] if cover_added else []
        if title_page_item:
            spine.append(title_page_item)
        if copyright_page_item:
            spine.append(copyright_page_item)

        spine.extend(epub_chapters)

        if author_page_item:
            spine.append(author_page_item)

        book.spine = spine

    # 8. 輸出
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    epub.write_epub(str(out_file), book, {"epub3_pages": False})

    return str(out_file)
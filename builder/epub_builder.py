from html import escape
from pathlib import Path
import ebooklib
from ebooklib import epub
from utils.image_processor import process_image


def _make_chapter_filename(index: int) -> str:
    return f"chap_{index:02d}.xhtml"


def _get_profile(config: dict, book_language: str) -> dict:
    """
    取得語言 Profile：以 zh-TW 為底，再用選定語言的值覆蓋。
    選定語言缺少某個 key 時，自動降級使用 zh-TW 的值。
    """
    profiles = config.get("LANGUAGE_PROFILES", {})
    merged = dict(profiles.get("zh-TW", {}))
    merged.update(profiles.get(book_language, {}))
    return merged


def _build_title_page_html(config: dict, book_language: str) -> str:
    """
    生成「書名頁 (Title Page)」HTML（由 LANGUAGE_PROFILES 驅動）。
    """
    title = escape(config.get("book_title", ""))
    author = escape(config.get("book_author", ""))
    publisher = escape(config.get("book_publisher", ""))
    year = escape(str(config.get("book_publish_year", "")))

    profile = _get_profile(config, book_language)
    page_title = escape(profile.get("title_page_title", "書名頁"))

    # 出版者與年份各自獨立：只填其中一個時，另一個不會連帶消失
    publisher_text = ""
    if publisher and year:
        publisher_text = profile.get("title_page_publisher_year_format", "{publisher} 出版，{year} 年。").format(
            publisher=publisher, year=year)
    elif publisher:
        publisher_text = profile.get("title_page_publisher_format", "{publisher} 出版。").format(
            publisher=publisher)
    elif year:
        publisher_text = profile.get("title_page_year_format", "{year} 年。").format(year=year)

    publisher_html = ""
    if publisher_text:
        publisher_html = f'<p class="title-page-publisher">{publisher_text}</p>'

    return f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="{book_language}">
<head>
    <meta charset="utf-8"/>
    <title>{page_title}</title>
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
    """生成「版權頁 (Copyright Page)」HTML（由 LANGUAGE_PROFILES 驅動）。"""
    profile = _get_profile(config, book_language)

    title = escape(config.get("book_title", ""))
    author = escape(config.get("book_author", ""))
    holder = escape(config.get("copyright_holder") or config.get("book_author", ""))
    pub_date = escape(config.get("copyright_publish_date", ""))
    year = escape(str(config.get("book_publish_year", "")))
    edition_num = config.get("copyright_edition_number", 1)

    disclaimer = escape(profile.get("copyright_disclaimer", ""))
    page_title = escape(profile.get("copyright_page_title", "版權頁"))
    title_format = profile.get("book_title_format", "《{title}》")
    edition_format = profile.get("copyright_edition_format", "第 {edition} 版")
    edition_line_format = profile.get("copyright_edition_line_format", "{edition}：{date}")
    statement_format = profile.get("copyright_statement", "© {year} {holder}. 保留所有權利。")
    statement_no_year_format = profile.get("copyright_statement_no_year", "© {holder}")
    author_line_format = profile.get("copyright_author_line_format", "作者：{author}")

    title_line = f'<p class="copyright-book-title">{title_format.format(title=title)}</p>'
    edition_str = edition_format.format(edition=edition_num)
    edition_line = (
        f'<p class="copyright-edition">'
        f'{edition_line_format.format(edition=edition_str, date=pub_date)}</p>'
    )

    if year:
        copy_text = statement_format.format(year=year, holder=holder)
    else:
        copy_text = statement_no_year_format.format(holder=holder)
    copy_line = f'<p class="copyright-notice">{copy_text}</p>'
    author_line = f'<p class="copyright-author">{author_line_format.format(author=author)}</p>'

    return f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="{book_language}">
<head>
    <meta charset="utf-8"/>
    <title>{page_title}</title>
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
    """生成「作者介紹頁 (About the Author)」HTML（由 LANGUAGE_PROFILES 驅動）。"""
    profile = _get_profile(config, book_language)
    page_title = escape(profile.get("author_page_title", "關於作者"))
    bio_text = config.get("author_bio_text", "")

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
    # 讀取執行時的書籍語言代碼（預設 zh-TW）
    book_language = config.get("BOOK_LANGUAGE", "zh-TW")
    profile = _get_profile(config, book_language)

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
        chapters_data = [{
            "title": templated_data.get("title", profile.get("single_fallback_title", "正文")),
            "html": html_body,
        }]

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
    chapter_fallback_format = profile.get("chapter_fallback_title", "第 {n} 章")
    empty_chapter_text = escape(profile.get("empty_chapter_text", "內文無文字內容。"))

    for i, chapter_data in enumerate(chapters_data, 1):
        chapter_title = "" if is_single_article else (
            chapter_data.get("title") or chapter_fallback_format.format(n=i)
        )
        html_body = chapter_data.get("html", "").strip()
        if not html_body:
            html_body = f"<p>{empty_chapter_text}</p>"

        file_name = _make_chapter_filename(i)

        # <title> 內的章節標題必須 escape，否則標題含 & < > 會產生無效 XHTML
        full_html = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="{book_language}">
<head>
    <meta charset="utf-8"/>
    <title>{escape(chapter_title)}</title>
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

        toc_structure.append(epub.Link(file_name, chapter_title, f"toc_{i:02d}"))

    # 5.5 建立前置/後置頁面（Front & Back Matter）
    title_page_item = None
    copyright_page_item = None
    author_page_item = None

    if not is_single_article:
        if config.get("enable_title_page"):
            t_html = _build_title_page_html(config, book_language)
            title_page_item = epub.EpubHtml(
                title=profile.get("title_page_title", "書名頁"),
                file_name="title_page.xhtml",
                lang=book_language
            )
            title_page_item.content = t_html.encode("utf-8")
            title_page_item.add_item(style_css)
            book.add_item(title_page_item)

        if config.get("enable_copyright_page"):
            c_html = _build_copyright_page_html(config, book_language)
            copyright_page_item = epub.EpubHtml(
                title=profile.get("copyright_page_title", "版權頁"),
                file_name="copyright_page.xhtml",
                lang=book_language
            )
            copyright_page_item.content = c_html.encode("utf-8")
            copyright_page_item.add_item(style_css)
            book.add_item(copyright_page_item)

        if config.get("enable_author_page"):
            a_html = _build_author_page_html(config, book_language)
            author_page_item = epub.EpubHtml(
                title=profile.get("author_page_item_title", "作者介紹"),
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
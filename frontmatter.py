import html
from datetime import datetime

def _to_english_ordinal(n: int) -> str:
    """
    將正整數轉換為英文序數字串（例：1 -> First, 2 -> Second, 21 -> 21st）
    """
    special_cases = {
        1: "First", 2: "Second", 3: "Third", 4: "Fourth", 5: "Fifth",
        6: "Sixth", 7: "Seventh", 8: "Eighth", 9: "Ninth", 10: "Tenth",
        11: "Eleventh", 12: "Twelfth", 13: "Thirteenth", 14: "Fourteenth",
        15: "Fifteenth", 16: "Sixteenth", 17: "Seventeenth", 18: "Eighteenth",
        19: "Nineteenth", 20: "Twentieth"
    }
    if n in special_cases:
        return special_cases[n]
    
    # 處理 21 以上的數字 (21st, 22nd, 23rd, 24th...)
    if n % 100 in (11, 12, 13):
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    
    return f"{n}{suffix}"


def generate_title_page_xhtml(form_data: dict) -> str:
    """
    生成書名頁 (Title Page) XHTML 內容
    """
    title = html.escape(form_data.get('title', '').strip())
    author = html.escape(form_data.get('author', '').strip())
    publisher = html.escape(form_data.get('publisher', '').strip())
    
    current_year = str(datetime.now().year)
    publish_year = html.escape(form_data.get('publish_year', '').strip() or current_year)
    
    copyright_lang = form_data.get('copyright_lang', 'zh')

    publisher_html = ""
    if publisher:
        if copyright_lang == 'en':
            publisher_text = f"Published by {publisher}, {publish_year}."
        else:
            publisher_text = f"{publisher} 出版，{publish_year} 年。"
        publisher_html = f'<p class="book-publisher">{publisher_text}</p>'

    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{copyright_lang}">
<head>
    <title>{title}</title>
    <link rel="stylesheet" type="text/css" href="frontmatter.css" />
</head>
<body class="title-page">
    <div class="title-container">
        <h1 class="book-title">{title}</h1>
        <p class="book-author">{author}</p>
        {publisher_html}
    </div>
</body>
</html>"""


def generate_copyright_page_xhtml(form_data: dict) -> str:
    """
    生成版權頁 (Copyright Page) XHTML 內容
    """
    title = html.escape(form_data.get('title', '').strip())
    author = html.escape(form_data.get('author', '').strip())
    copyright_owner = html.escape(form_data.get('copyright_owner', '').strip() or author)
    publish_date = html.escape(form_data.get('publish_date', '').strip())
    copyright_lang = form_data.get('copyright_lang', 'zh')
    
    current_year = str(datetime.now().year)
    publish_year = html.escape(form_data.get('publish_year', '').strip() or current_year)

    # 防錯機制：刷次轉型為正整數
    raw_edition = form_data.get('edition', '1')
    try:
        edition_num = int(raw_edition)
        if edition_num < 1:
            edition_num = 1
    except (ValueError, TypeError):
        edition_num = 1

    if copyright_lang == 'en':
        disclaimer = "While every precaution has been taken in the preparation of this book, the publisher assumes no responsibility for errors or omissions, or for damages resulting from the use of the information contained herein."
        edition_str = f"{_to_english_ordinal(edition_num)} edition. {publish_date}."
        copyright_line = f"Copyright © {publish_year} {copyright_owner}."
        author_line = f"Written by {author}."
        book_title_display = title
    else:
        disclaimer = "本書編製過程已採取一切預防措施，若仍有疏漏或錯誤，出版者與作者對於因使用本書資訊所導致之損害概不負責。"
        edition_str = f"第 {edition_num} 版：{publish_date}."
        copyright_line = f"版權所有 © {publish_year} {copyright_owner}"
        author_line = f"作者：{author}"
        book_title_display = f"《{title}》"

    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{copyright_lang}">
<head>
    <title>Copyright</title>
    <link rel="stylesheet" type="text/css" href="frontmatter.css" />
</head>
<body class="copyright-page">
    <p class="disclaimer">{disclaimer}</p>
    <p class="book-title-copyright">{book_title_display}</p>
    <p class="edition-info"><strong>{edition_str}</strong></p>
    <p class="copyright-line">{copyright_line}</p>
    <p class="author-line">{author_line}</p>
</body>
</html>"""


def generate_author_page_xhtml(form_data: dict) -> str:
    """
    生成作者介紹頁 (About the Author) XHTML 內容
    """
    copyright_lang = form_data.get('copyright_lang', 'zh')
    author_bio = form_data.get('author_bio', '').strip()

    heading = "About the Author" if copyright_lang == 'en' else "關於作者"

    # 多段落解析
    paragraphs = [p.strip() for p in author_bio.splitlines() if p.strip()]
    bio_html = "\n".join([f'    <p class="author-bio-p">{html.escape(p)}</p>' for p in paragraphs])

    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{copyright_lang}">
<head>
    <title>{heading}</title>
    <link rel="stylesheet" type="text/css" href="frontmatter.css" />
</head>
<body class="author-page">
    <h2 class="author-heading">{heading}</h2>
{bio_html}
</body>
</html>"""


def build_frontmatter_files(form_data: dict) -> dict:
    """
    對外主接口：傳入 Flask 的 request.form (dict)
    回傳字典格式：{'檔名.xhtml': 'xhtml內容', ...}
    
    使用範例：
        files = build_frontmatter_files(request.form)
        for filename, content in files.items():
            # 寫入 EPUB 打包目錄或 zip 檔案中
    """
    result_files = {}

    if 'enable_title_page' in form_data:
        result_files['title_page.xhtml'] = generate_title_page_xhtml(form_data)

    if 'enable_copyright_page' in form_data:
        result_files['copyright_page.xhtml'] = generate_copyright_page_xhtml(form_data)

    if 'enable_author_page' in form_data and form_data.get('author_bio', '').strip():
        result_files['author_page.xhtml'] = generate_author_page_xhtml(form_data)

    return result_files
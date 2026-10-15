from pathlib import Path
from .template_engine import inject_images_into_html

TEMPLATES_DIR = Path(__file__).parent

VALID_TEMPLATES = ("minimal", "interleaved", "rich", "quote", "raw")


def apply_template(parsed_data: dict, config: dict) -> dict:
    """
    版型選擇器與套用
    回傳：
    {
        "title": str,
        "chapters": [{"title": str, "html": str}, ...],   # 已套用版型後的每章內容
        "css_content": str,
        "template_used": str,
        "images": list
    }
    """
    images = parsed_data.get("images", [])
    num_images = len(images)

    chapters = parsed_data.get("chapters")
    if chapters is None:
        # 舊格式相容：单一字串包成單章節清單
        raw_html = parsed_data.get("content_html") or parsed_data.get("html_content", "")
        chapters = [{"title": parsed_data.get("title", "Untitled"), "html": raw_html}]

    user_template = config.get("LAYOUT_TEMPLATE", "auto").lower()
    is_multi_chapter = len(chapters) > 1

    # --- 版型選擇邏輯 ---
    if user_template == "raw":
        selected_template = "raw"
    elif user_template == "auto":
        if is_multi_chapter:
            # 多章節（整本書）：不套用智慧選版型，直接視為自訂排版
            selected_template = "raw"
        elif num_images == 0:
            selected_template = "minimal"
        elif num_images == 1:
            selected_template = "quote"
        elif 2 <= num_images <= 3:
            selected_template = "interleaved"
        else:
            selected_template = "rich"
    else:
        selected_template = user_template if user_template in VALID_TEMPLATES else "minimal"

    # 1. 依版型逐章節產生最終 html
    rendered_chapters = []
    if selected_template == "raw":
        for chapter in chapters:
            rendered_chapters.append({
                "title": chapter.get("title", ""),
                "html": chapter.get("html", "")
            })
    else:
        for chapter in chapters:
            final_html = inject_images_into_html(
                chapter.get("html", ""), images, selected_template
            )
            rendered_chapters.append({
                "title": chapter.get("title", ""),
                "html": final_html
            })

    # 2. 讀取對應的 CSS 檔案
    css_file = TEMPLATES_DIR / f"{selected_template}.css"
    if css_file.exists():
        with open(css_file, "r", encoding="utf-8") as f:
            css_content = f.read()
    else:
        css_content = "/* Default fallback css */"

    return {
        "title": parsed_data.get("title", "Untitled"),
        "chapters": rendered_chapters,
        "css_content": css_content,
        "template_used": selected_template,
        "images": images
    }
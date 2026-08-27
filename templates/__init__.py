from pathlib import Path
from .template_engine import inject_images_into_html

TEMPLATES_DIR = Path(__file__).parent

def apply_template(parsed_data: dict, config: dict) -> dict:
    """
    版型選擇器與套用進入點：
    根據 config["LAYOUT_TEMPLATE"] 決定版型；若為 "auto"，則進行智慧選擇。

    回傳：
    {
        "title": str,
        "final_html": str,
        "css_content": str,
        "template_used": str,
        "images": list
    }
    """
    images = parsed_data.get("images", [])
    
    # 【關鍵修正】：支援雙 Key 容錯，優先取 content_html，不存在則取 html_content
    raw_html = parsed_data.get("content_html") or parsed_data.get("html_content", "")
    num_images = len(images)

    user_template = config.get("LAYOUT_TEMPLATE", "auto").lower()

    # --- auto 智慧選擇器邏輯 ---
    if user_template == "auto":
        if num_images == 0:
            selected_template = "minimal"
        elif num_images == 1:
            selected_template = "quote"
        elif 2 <= num_images <= 3:
            selected_template = "interleaved"
        else:
            selected_template = "rich"
    else:
        # 若使用者指定 minimal/interleaved/rich/quote 則直接採用
        selected_template = user_template if user_template in ("minimal", "interleaved", "rich", "quote") else "minimal"

    # 1. 執行圖片動態注入排版
    final_html = inject_images_into_html(raw_html, images, selected_template)

    # 2. 讀取對應的 CSS 檔案
    css_file = TEMPLATES_DIR / f"{selected_template}.css"
    if css_file.exists():
        with open(css_file, "r", encoding="utf-8") as f:
            css_content = f.read()
    else:
        css_content = "/* Default fallback css */"

    return {
        "title": parsed_data.get("title", "Untitled"),
        "final_html": final_html,
        "css_content": css_content,
        "template_used": selected_template,
        "images": images
    }
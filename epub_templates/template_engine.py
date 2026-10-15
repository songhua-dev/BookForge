import re
from bs4 import BeautifulSoup

def inject_images_into_html(html_content: str, images: list, template_name: str) -> str:
    """
    動態圖片排版引擎（優先順序：2 Word內嵌 > 3 內文檔名標記 > 1 剩餘圖片自動排版）
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # 建立圖片檔名與圖片資料的對照表 (Key: 原始檔名/檔名主體)
    img_map = {}
    for img in images:
        raw_name = img.get("original_filename", img["filename"]).lower()
        stem_name = raw_name.split('.')[0]
        img_map[raw_name] = img
        img_map[stem_name] = img

    used_images = set()

    # -----------------------------------------------------------------
    # 處理【情況 2】：偵測 html_content 中已經內嵌好的圖片
    # （docx_parser / odt_parser 在解析階段就已經把 <img> 標籤插入正確位置，
    #  這類圖片不該再被下面的「剩餘圖片自動排版」邏輯重複插入一次）
    # -----------------------------------------------------------------
    filename_lookup = {img["filename"].lower(): img["filename"] for img in images}
    for existing_img in soup.find_all("img"):
        src = existing_img.get("src", "")
        existing_filename = src.rsplit("/", 1)[-1].lower()
        if existing_filename in filename_lookup:
            used_images.add(filename_lookup[existing_filename])

    # -----------------------------------------------------------------
    # 處理【情況 3】：掃描內文中的 [1.jpg] 或 [圖片: 1] 等標記
    # -----------------------------------------------------------------
    pattern = re.compile(r'\[(?:圖片\s*:\s*)?([a-zA-Z0-9_\-\.]+)]')

    for element in soup.find_all(text=pattern):
        text = str(element)
        matches = pattern.findall(text)

        for match in matches:
            match_key = match.lower().strip()
            target_img = img_map.get(match_key) or img_map.get(match_key.split('.')[0])

            if target_img:
                used_images.add(target_img["filename"])
                # 建立替換用的 img 標籤
                img_div = soup.new_tag("div", **{"class": "img-container"})
                img_tag = soup.new_tag("img", src=f"images/{target_img['filename']}", alt=target_img['filename'])
                img_div.append(img_tag)

                # 若標記為獨立段落，替換整個段落；否則插入於父層之後
                parent = element.parent
                if parent and parent.name == "p" and parent.get_text().strip() == f"[{match}]":
                    parent.replace_with(img_div)
                else:
                    new_text = text.replace(f"[{match}]", "")
                    element.replace_with(new_text)
                    parent.insert_after(img_div)

    # -----------------------------------------------------------------
    # 處理【情況 1】：剩餘未被標記、也未內嵌的圖片（按編號 1, 2, 3 順序自動排版）
    # -----------------------------------------------------------------
    remaining_images = [img for img in images if img["filename"] not in used_images]

    # 依照檔名中的數字順序自然排序 (如 1.jpg < 2.jpg < 10.jpg)
    def natural_sort_key(img):
        name = img.get("original_filename", img["filename"])
        numbers = re.findall(r'\d+', name)
        return int(numbers[0]) if numbers else 999

    remaining_images.sort(key=natural_sort_key)

    # 若還有剩餘圖片，執行自動交錯插入
    if remaining_images:
        paragraphs = soup.find_all("p")
        if not paragraphs:
            for img in remaining_images:
                img_div = soup.new_tag("div", **{"class": "img-container"})
                img_tag = soup.new_tag("img", src=f"images/{img['filename']}", alt=img['filename'])
                img_div.append(img_tag)
                soup.append(img_div)
            return str(soup)

        num_p = len(paragraphs)

        # quote 版型首圖保護
        if template_name == "quote":
            first_img = remaining_images[0]
            img_div = soup.new_tag("div", **{"class": "quote-hero-img"})
            img_tag = soup.new_tag("img", src=f"images/{first_img['filename']}", alt=first_img['filename'])
            img_div.append(img_tag)
            paragraphs[0].insert_before(img_div)
            to_interleave = remaining_images[1:]
        else:
            to_interleave = remaining_images

        # 剩餘圖片均勻交錯插入
        if to_interleave and num_p > 0:
            step = max(1, num_p // (len(to_interleave) + 1))
            for idx, img in enumerate(to_interleave):
                target_p_idx = min((idx + 1) * step, num_p - 1)
                img_div = soup.new_tag("div", **{"class": "img-container"})
                img_tag = soup.new_tag("img", src=f"images/{img['filename']}", alt=img['filename'])
                img_div.append(img_tag)
                paragraphs[target_p_idx].insert_after(img_div)

    return str(soup)
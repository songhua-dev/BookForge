import re
from opencc import OpenCC


def convert_chinese_variant(text: str, mode: str = "t2s") -> str:
    """
    簡繁體轉換工具函式
    """
    if not text:
        return text
    converter = OpenCC(mode)
    return converter.convert(text)


def clean_text(text: str, config: dict) -> str:
    """
    文字清洗主入口：
    依據 config 執行「保護 -> 轉換 -> 還原」三階段標點符號全型化與數字防呆。
    """
    # 0. 簡繁體轉換檢查：若開啟簡繁轉換，先執行 OpenCC 轉換
    if config.get("convert_chinese_enable", False):
        mode = config.get("convert_chinese_mode", "t2s")
        text = convert_chinese_variant(text, mode=mode)

    # 總開關檢查：若關閉標點轉換，直接返回原文字
    if not config.get("TEXT_PUNCTUATION_CONVERT", True):
        return text

    placeholders = {}

    # -----------------------------------------------------------------
    # 第一階段（保護）：抓出小數與千分位數字，暫存為佔位符
    # -----------------------------------------------------------------
    if config.get("TEXT_SMART_NUMERIC_EXEMPT", True):
        def repl(match):
            key = f"__NUM_EXEMPT_{len(placeholders)}__"
            placeholders[key] = match.group(0)
            return key

        # 正規表達式匹配：小數點 (如 3.14) 或 千分位 (如 1,000 或 10,000,000)
        numeric_pattern = r'\d+\.\d+|\d{1,3}(?:,\d{3})+'
        text = re.sub(numeric_pattern, repl, text)

    # -----------------------------------------------------------------
    # 第二階段（轉換）：依開關執行標點全型化
    # -----------------------------------------------------------------
    # 1. 逗號轉換 , -> ，
    if config.get("TEXT_CONVERT_COMMA", True):
        text = text.replace(',', '，')

    # 2. 句號轉換 . -> 。
    if config.get("TEXT_CONVERT_PERIOD", True):
        text = text.replace('.', '。')

    # 3. 引號轉換 "..." -> 「...」
    if config.get("TEXT_CONVERT_QUOTES", True):
        # 使用正規表達式配對雙引號並替換為中式直角引號
        text = re.sub(r'"([^"]*)"', r'「\1」', text)

    # -----------------------------------------------------------------
    # 第三階段（還原）：將暫存的數字正確放回
    # -----------------------------------------------------------------
    for key, val in placeholders.items():
        text = text.replace(key, val)

    return text
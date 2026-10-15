"""
app.py

BookForge 的 Flask 進入點：
- run_pipeline()（main.py）：電子書製作器面板，parse_folder → apply_template → build_epub
- separate_docx()（separate.py）：電子書校對面板，分割檔案
- combine_docx()（combine.py）：電子書校對面板，合併檔案

這裡的每個路由各自 try/except、把錯誤轉成 JSON 訊息回傳給前端彈窗顯示，
跟 main.py CLI 的錯誤呈現方式（印 stderr + sys.exit）各自獨立、不共用邏輯。
"""
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, jsonify

from config import CONFIG
from main import run_pipeline
from separate import separate_docx, VALID_SPLIT_LEVELS
from combine import combine_docx
from output_utils import get_output_dir, is_filename_available, normalize_epub_filename

app = Flask(__name__)

ALLOWED_CONTENT_EXTENSIONS = {".docx", ".odt", ".md", ".markdown", ".txt"}
ALLOWED_COVER_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/check_filename")
def check_filename():
    """電子書製作器面板：生成檔名欄位時，即時檢查是否與桌面
    輸出資料夾內既有檔案重複。這只是即時提示，執行時 build_epub_route()
    還會再檢查一次（防止兩次檢查之間被其他請求搶先用掉同一個檔名）。"""
    filename = request.args.get("filename", "")
    if not filename.strip():
        return jsonify({"available": False, "message": "檔名不可為空"})
    return jsonify({"available": is_filename_available(filename)})


def _save_upload(file_storage, dest_dir: Path, allowed_extensions: set) -> Path:
    """
    儲存上傳檔案到 dest_dir，副檔名不在允許清單內就拒絕，回傳完整路徑。
    """
    original_filename = file_storage.filename or ""
    ext = Path(original_filename).suffix.lower()
    if ext not in allowed_extensions:
        raise ValueError(f"不支援的檔案格式：{ext or '（無副檔名）'}")
    dest_path = dest_dir / f"upload{ext}"
    file_storage.save(str(dest_path))
    return dest_path


@app.route("/api/build_epub", methods=["POST"])
def build_epub_route():
    """
    電子書製作器面板的執行按鈕。

    接收上傳的內文檔案（必填）、封面檔案（選填）、書名（必填）、
    輸出檔名（必填），存進一個暫存資料夾後交給 run_pipeline() 跑完整流程，。
    """
    book_title = (request.form.get("book_title") or "").strip()
    output_filename = (request.form.get("output_filename") or "").strip()
    content_file = request.files.get("content_file")
    cover_file = request.files.get("cover_file")

    # 讀取前置/後置頁面（Front/Back Matter）開關與表單欄位
    enable_title_page = request.form.get("enable_title_page") is not None
    book_author = (request.form.get("book_author") or "").strip()
    book_publisher = (request.form.get("book_publisher") or "").strip()
    book_publish_year = (request.form.get("book_publish_year") or "").strip()

    enable_copyright_page = request.form.get("enable_copyright_page") is not None
    copyright_holder = (request.form.get("copyright_holder") or "").strip()
    raw_copyright_date = (request.form.get("copyright_publish_date") or "").strip()
    copyright_edition_raw = request.form.get("copyright_edition_number")
    copyright_language = (request.form.get("copyright_language") or "zh").strip().lower()

    enable_author_page = request.form.get("enable_author_page") is not None
    author_bio_text = (request.form.get("author_bio_text") or "").strip()

    # 後端必填驗證：不能只信前端的 required，避免有人繞過前端直接打 API
    if not book_title:
        return jsonify({"success": False, "message": "書名為必填欄位"}), 400
    if not output_filename:
        return jsonify({"success": False, "message": "輸出檔名為必填欄位"}), 400
    if not content_file or not content_file.filename:
        return jsonify({"success": False, "message": "請上傳電子書內文檔案"}), 400

    # 前置/後置頁面開啟時的後端必填與防錯驗證
    if enable_title_page and not book_author:
        return jsonify({"success": False, "message": "啟用書名頁時，作者為必填欄位"}), 400

    if enable_copyright_page:
        if not copyright_holder:
            return jsonify({"success": False, "message": "啟用版權頁時，版權所有人為必填欄位"}), 400
        if not raw_copyright_date:
            return jsonify({"success": False, "message": "啟用版權頁時，出版時間為必填欄位"}), 400

    if enable_author_page and not author_bio_text:
        return jsonify({"success": False, "message": "啟用作者介紹頁時，作者簡介內文為必填欄位"}), 400

    # 刷次 (Edition Number) 後端防錯：轉 int，非數字或 < 1 強制帶回 1
    try:
        copyright_edition_number = int(copyright_edition_raw)
        if copyright_edition_number < 1:
            copyright_edition_number = 1
    except (ValueError, TypeError):
        copyright_edition_number = 1

    # 版權頁語系防呆
    if copyright_language not in {"zh", "en"}:
        copyright_language = "zh"

    # 日期選擇框 (YYYY-MM-DD) 格式化處理
    formatted_publish_date = raw_copyright_date
    if raw_copyright_date:
        try:
            dt = datetime.strptime(raw_copyright_date, "%Y-%m-%d")
            if copyright_language == "en":
                # 轉為 October 5, 2026 格式
                formatted_publish_date = dt.strftime("%B %d, %Y")
            else:
                # 轉為 2026 年 10 月 5 日 格式
                formatted_publish_date = f"{dt.year} 年 {dt.month} 月 {dt.day} 日"
        except ValueError:
            # 解析失敗時直接維持原樣
            formatted_publish_date = raw_copyright_date

    # 執行時二次檢查檔名是否重複
    if not is_filename_available(output_filename):
        normalized = normalize_epub_filename(output_filename)
        return jsonify({"success": False, "message": f"檔名「{normalized}」已存在，請換一個檔名"}), 400

    # 內文跟封面必須存進「兩個不同」的暫存資料夾，不能共用一個：
    # 分成兩個資料夾，讓 parse_folder() 完全看不到封面檔案，才能從根本
    # 避免 EPUBCheck 噴 OPF-029（宣告格式跟實際內容不符）這個問題，不是靠後續再去過濾排除。
    temp_dir = Path(tempfile.mkdtemp(prefix="bookforge_build_"))
    cover_temp_dir = None
    try:
        _save_upload(content_file, temp_dir, ALLOWED_CONTENT_EXTENSIONS)

        runtime_config = CONFIG.copy()
        runtime_config["book_title"] = book_title

        # 前置 / 後置頁面設定值注入 runtime_config
        runtime_config["enable_title_page"] = enable_title_page
        runtime_config["book_author"] = book_author
        runtime_config["book_publisher"] = book_publisher
        runtime_config["book_publish_year"] = book_publish_year

        runtime_config["enable_copyright_page"] = enable_copyright_page
        runtime_config["copyright_holder"] = copyright_holder
        runtime_config["copyright_publish_date"] = formatted_publish_date
        runtime_config["copyright_edition_number"] = copyright_edition_number
        runtime_config["copyright_language"] = copyright_language

        runtime_config["enable_author_page"] = enable_author_page
        runtime_config["author_bio_text"] = author_bio_text

        if cover_file and cover_file.filename:
            cover_temp_dir = Path(tempfile.mkdtemp(prefix="bookforge_cover_"))
            cover_path = _save_upload(cover_file, cover_temp_dir, ALLOWED_COVER_EXTENSIONS)
            runtime_config["cover_image_path"] = str(cover_path)

        output_path = get_output_dir() / normalize_epub_filename(output_filename)
        final_path = run_pipeline(str(temp_dir), str(output_path), runtime_config)

        shutil.rmtree(temp_dir, ignore_errors=True)
        if cover_temp_dir is not None:
            shutil.rmtree(cover_temp_dir, ignore_errors=True)
        return jsonify({"success": True, "message": f"轉檔成功！檔案已輸出至：\n{final_path}"})

    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        if cover_temp_dir is not None:
            shutil.rmtree(cover_temp_dir, ignore_errors=True)
        # 印出錯誤與追蹤資訊供後端日誌記錄
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"轉檔失敗：{str(e)}"}), 400


@app.route("/api/separate", methods=["POST"])
def separate_route():
    """電子書校對面板：分割檔案。上傳的來源檔存進暫存資料夾，
    separate_docx() 執行完會自動刪除這份暫存來源檔（delete_source=True），
    輸出的章節檔直接寫進 config["PROOFREAD_DIR"]。"""
    split_level = (request.form.get("split_level") or "").strip()
    source_file = request.files.get("source_file")

    if split_level not in VALID_SPLIT_LEVELS:
        return jsonify({"success": False, "message": "請選擇要依標題1或標題2分割"}), 400
    if not source_file or not source_file.filename:
        return jsonify({"success": False, "message": "請上傳要分割的檔案"}), 400

    temp_dir = Path(tempfile.mkdtemp(prefix="bookforge_split_"))
    try:
        source_path = _save_upload(source_file, temp_dir, {".docx"})
        output_dir = CONFIG["PROOFREAD_DIR"]
        result = separate_docx(
            str(source_path),
            output_dir,
            split_level=split_level,
            delete_source=True,
        )
        message = (
            f"分割完成，共產生 {result['doc_count']} 個章節檔、抽取 {result['image_count']} 張圖片。\n"
            f"檔案已輸出至資料夾：\n{output_dir}"
        )
        return jsonify({"success": True, "message": message})

    except Exception as e:
        return jsonify({"success": False, "message": f"分割失敗：{str(e)}"}), 400

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.route("/api/combine", methods=["POST"])
def combine_route():
    """
    電子書校對面板：合併檔案。

    前端必須先跳出二次確認，使用者按下確定後才會在表單裡
    帶上 confirmed=true 送出；後端這裡仍然明確檢查這個值，沒有收到
    confirmed=true 一律拒絕執行。
    """
    output_filename = (request.form.get("output_filename") or "").strip()
    confirmed = request.form.get("confirmed") == "true"

    if not output_filename:
        return jsonify({"success": False, "message": "生成檔案名稱為必填欄位"}), 400
    if not confirmed:
        return jsonify({"success": False, "message": "合併操作需要二次確認"}), 400

    try:
        result = combine_docx(CONFIG["PROOFREAD_DIR"], output_filename, confirmed=True)
        message = f"合併完成，已輸出至：\n{result['output_path']}"
        if result["excluded_files"]:
            excluded_str = "、".join(result["excluded_files"])
            message += f"\n\n以下檔案未被合併：{excluded_str}"
        return jsonify({"success": True, "message": message})

    except Exception as e:
        return jsonify({"success": False, "message": f"合併失敗：{str(e)}"}), 400


@app.route("/api/convert_chinese", methods=["POST"])
def convert_chinese_route():
    """簡繁互換面板：上傳檔案執行 OpenCC 轉換（支援 .docx 與純文字檔）。"""
    convert_mode = (request.form.get("convert_chinese_mode") or "s2tw").strip().lower()
    convert_file = request.files.get("convert_file")

    if not convert_file or not convert_file.filename:
        return jsonify({"success": False, "message": "請上傳要轉換的檔案"}), 400

    temp_dir = Path(tempfile.mkdtemp(prefix="bookforge_convert_"))
    try:
        source_path = _save_upload(convert_file, temp_dir, ALLOWED_CONTENT_EXTENSIONS)
        output_dir = get_output_dir()
        original_stem = Path(convert_file.filename).stem
        ext = source_path.suffix.lower()
        output_path = output_dir / f"{original_stem}_{convert_mode}{ext}"

        import opencc
        # 修正：傳入 convert_mode 即可，不可加 .json
        converter = opencc.OpenCC(convert_mode)

        if ext == ".docx":
            import docx
            doc = docx.Document(source_path)
            
            # 轉換內文段落
            for p in doc.paragraphs:
                if p.text:
                    p.text = converter.convert(p.text)
                    
            # 轉換表格內容
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for p in cell.paragraphs:
                            if p.text:
                                p.text = converter.convert(p.text)
                                
            doc.save(output_path)
        else:
            # 純文字檔案處理 (.txt, .md, .markdown)
            with open(source_path, "r", encoding="utf-8") as rf:
                content = rf.read()

            converted_content = converter.convert(content)

            with open(output_path, "w", encoding="utf-8") as wf:
                wf.write(converted_content)

        message = f"轉換完成！檔案已輸出至：\n{output_path}"
        return jsonify({"success": True, "message": message})

    except Exception as e:
        return jsonify({"success": False, "message": f"轉換失敗：{str(e)}"}), 400

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    app.run(debug=True)
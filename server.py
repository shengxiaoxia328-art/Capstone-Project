"""
照片故事 API 服务
供前端调用：选模式、上传分析、访谈、生成故事
"""
import os
import sys
import uuid
import tempfile
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

from main import PhotoStorySystem

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173"])

# 每会话一个系统实例，保持对话状态
sessions = {}
UPLOAD_DIR = tempfile.mkdtemp(prefix="photo_story_")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_session(session_id: str):
    if session_id not in sessions:
        return None
    return sessions[session_id]


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/init", methods=["POST"])
def init_session():
    """创建会话，选择模式 single | multi"""
    data = request.get_json() or {}
    mode = data.get("mode", "single")
    if mode not in ("single", "multi"):
        return jsonify({"error": "mode 须为 single 或 multi"}), 400
    session_id = str(uuid.uuid4())
    system = PhotoStorySystem()
    if mode == "multi":
        system.context_manager.clear()
    sessions[session_id] = {
        "mode": mode,
        "system": system,
        "current_photo_id": None,
        "current_analysis": None,
        "current_qa": [],
        "all_photo_records": [],
    }
    return jsonify({"session_id": session_id, "mode": mode})


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """上传图片并分析，返回分析结果与初始问题列表"""
    session_id = request.headers.get("X-Session-Id") or request.form.get("session_id")
    if not session_id or not get_session(session_id):
        return jsonify({"error": "缺少或无效的 session_id"}), 400
    if "image" not in request.files and "file" not in request.files:
        return jsonify({"error": "请上传图片 (image 或 file)"}), 400
    file = request.files.get("image") or request.files.get("file")
    if not file or file.filename == "":
        return jsonify({"error": "未选择文件"}), 400
    try:
        ext = os.path.splitext(secure_filename(file.filename) or "img")[1] or ".jpg"
        path = os.path.join(UPLOAD_DIR, f"{session_id}_{uuid.uuid4().hex}{ext}")
        file.save(path)
        sess = get_session(session_id)
        system = sess["system"]
        analysis_result = system.analyzer.analyze_image(image_path=path)
        photo_id = os.path.basename(file.filename) or os.path.basename(path)
        sess["current_photo_id"] = photo_id
        sess["current_analysis"] = analysis_result
        sess["current_qa"] = []
        if sess["mode"] == "multi" and sess["all_photo_records"]:
            cross_q = system.context_manager.generate_cross_photo_question(analysis_result)
            system.dialogue_manager.start_dialogue(
                photo_id=photo_id, analysis_result=analysis_result
            )
            questions = [cross_q] if (cross_q and cross_q.strip()) else system.dialogue_manager.start_dialogue(
                photo_id=photo_id, analysis_result=analysis_result
            )
        else:
            questions = system.dialogue_manager.start_dialogue(
                photo_id=photo_id, analysis_result=analysis_result
            )
        try:
            os.remove(path)
        except Exception:
            pass
        return jsonify({
            "photo_id": photo_id,
            "analysis_result": analysis_result,
            "questions": questions,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/answer", methods=["POST"])
def answer():
    """提交一个回答，返回下一问（若有）及当前 qa 列表"""
    session_id = request.headers.get("X-Session-Id") or (request.get_json() or {}).get("session_id")
    if not session_id or not get_session(session_id):
        return jsonify({"error": "缺少或无效的 session_id"}), 400
    data = request.get_json() or {}
    question = data.get("question", "").strip()
    answer_text = data.get("answer", "").strip()
    if not question or not answer_text:
        return jsonify({"error": "question 和 answer 不能为空"}), 400
    try:
        sess = get_session(session_id)
        system = sess["system"]
        next_q = system.dialogue_manager.add_answer(question, answer_text)
        summary = system.dialogue_manager.get_dialogue_summary()
        qa = summary.get("qa_history", [])
        sess["current_qa"] = qa
        return jsonify({
            "next_question": next_q,
            "qa_history": qa,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/finish_photo", methods=["POST"])
def finish_photo():
    """多图模式：当前照片访谈结束，加入叙事链，准备下一张"""
    session_id = request.headers.get("X-Session-Id") or (request.get_json() or {}).get("session_id")
    if not session_id or not get_session(session_id):
        return jsonify({"error": "缺少或无效的 session_id"}), 400
    sess = get_session(session_id)
    if sess["mode"] != "multi":
        return jsonify({"error": "仅多图模式可调用 finish_photo"}), 400
    try:
        system = sess["system"]
        summary = system.dialogue_manager.get_dialogue_summary()
        qa = summary.get("qa_history", sess["current_qa"])
        system.context_manager.add_photo_dialogue(
            photo_id=sess["current_photo_id"],
            analysis_result=sess["current_analysis"],
            qa_history=qa,
        )
        sess["all_photo_records"].append({
            "photo_id": sess["current_photo_id"],
            "analysis": sess["current_analysis"],
            "qa_history": qa,
        })
        sess["current_photo_id"] = None
        sess["current_analysis"] = None
        sess["current_qa"] = []
        return jsonify({
            "photo_count": len(sess["all_photo_records"]),
            "all_photo_ids": [r["photo_id"] for r in sess["all_photo_records"]],
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/generate_story", methods=["POST"])
def generate_story():
    """根据当前会话生成故事（单图用当前分析+qa，多图用 all_photo_records）"""
    session_id = request.headers.get("X-Session-Id") or (request.get_json() or {}).get("session_id")
    if not session_id or not get_session(session_id):
        return jsonify({"error": "缺少或无效的 session_id"}), 400
    sess = get_session(session_id)
    system = sess["system"]
    try:
        if sess["mode"] == "single":
            summary = system.dialogue_manager.get_dialogue_summary()
            qa = summary.get("qa_history", sess["current_qa"])
            story = system.story_generator.generate_single_photo_story(
                photo_id=sess["current_photo_id"],
                analysis_result=sess["current_analysis"],
                qa_history=qa,
                narrative_style="personal",
            )
        else:
            if len(sess["all_photo_records"]) == 0:
                summary = system.dialogue_manager.get_dialogue_summary()
                qa = summary.get("qa_history", sess["current_qa"])
                sess["all_photo_records"].append({
                    "photo_id": sess["current_photo_id"],
                    "analysis": sess["current_analysis"],
                    "qa_history": qa,
                })
            story = system.story_generator.generate_multi_photo_story(
                sess["all_photo_records"]
            )
        return jsonify({"story": story})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

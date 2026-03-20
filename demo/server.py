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

import json
import queue
import threading
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from werkzeug.utils import secure_filename

import config
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


def _log(msg: str):
    """在运行 server 的终端打印后台活动，便于调试"""
    print(f"[后端] {msg}", flush=True)


@app.route("/")
def index():
    """根路径说明：前端请访问前端开发服务器（如 http://localhost:5173），本服务仅提供 API"""
    return jsonify({
        "message": "照片故事 API 服务",
        "docs": "本端口仅提供 API，请先启动前端（frontend 目录下 npm run dev），在浏览器打开 http://localhost:5173 使用应用。",
        "api_health": "/api/health",
    })


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
    _log(f"新建会话: mode={mode}, session_id={session_id[:8]}...")
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
    return jsonify({
        "session_id": session_id,
        "mode": mode,
        "max_dialogue_rounds": getattr(config, "MAX_DIALOGUE_ROUNDS", 10),
    })


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
        _log("收到分析请求，保存图片中...")
        ext = os.path.splitext(secure_filename(file.filename) or "img")[1] or ".jpg"
        path = os.path.join(UPLOAD_DIR, f"{session_id}_{uuid.uuid4().hex}{ext}")
        file.save(path)
        sess = get_session(session_id)
        system = sess["system"]
        _log("开始调用视觉模型分析图片（可能需 10–30 秒）...")
        analysis_result = system.analyzer.analyze_image(image_path=path)
        _log("图片分析完成，正在生成访谈问题...")
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
        _log("分析流程结束，已返回结果。")
        return jsonify({
            "photo_id": photo_id,
            "analysis_result": analysis_result,
            "questions": questions,
        })
    except Exception as e:
        _log(f"分析出错: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


def _sse_message(event: str, data: dict) -> str:
    """生成一条 SSE 消息"""
    return f"data: {json.dumps({'event': event, **data}, ensure_ascii=False)}\n\n"


def _split_text_for_stream(text: str, max_chunk=80):
    """将长文本按句号、换行拆成若干段，用于流式展示「解析/思考」过程"""
    if not (text or "").strip():
        return []
    parts = []
    for sep in ("。", "！", "？", "\n", "；"):
        text = text.replace(sep, sep + "\n")
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if len(line) <= max_chunk:
            parts.append(line + ("。" if not line.endswith(("。", "！", "？")) else ""))
        else:
            for i in range(0, len(line), max_chunk):
                parts.append(line[i : i + max_chunk])
    return parts


@app.route("/api/analyze/stream", methods=["POST"])
def analyze_stream():
    """上传图片并分析（SSE 流式返回思考过程与结果）"""
    session_id = request.headers.get("X-Session-Id") or request.form.get("session_id")
    if not session_id or not get_session(session_id):
        return jsonify({"error": "缺少或无效的 session_id"}), 400
    if "image" not in request.files and "file" not in request.files:
        return jsonify({"error": "请上传图片 (image 或 file)"}), 400
    file = request.files.get("image") or request.files.get("file")
    if not file or file.filename == "":
        return jsonify({"error": "未选择文件"}), 400
    # 必须在进入生成器之前保存文件：生成器运行时请求体可能已关闭，会导致 read of closed file
    ext = os.path.splitext(secure_filename(file.filename) or "img")[1] or ".jpg"
    path = os.path.join(UPLOAD_DIR, f"{session_id}_{uuid.uuid4().hex}{ext}")
    file.save(path)
    photo_id_from_file = os.path.basename(file.filename) or os.path.basename(path)

    def generate():
        try:
            yield _sse_message("thinking", {"text": "正在保存图片…"})
            sess = get_session(session_id)
            if not sess:
                yield _sse_message("error", {"error": "会话已失效"})
                return
            system = sess["system"]
            yield _sse_message("thinking", {"text": "正在调用视觉模型分析图片（约 10–30 秒）…"})
            analysis_result = system.analyzer.analyze_image(image_path=path)
            yield _sse_message("thinking", {"text": "图片分析完成，正在解析分析结果…"})
            yield _sse_message("thinking", {"text": "正在生成访谈问题…"})
            photo_id = photo_id_from_file
            sess["current_photo_id"] = photo_id
            sess["current_analysis"] = analysis_result
            sess["current_qa"] = []
            q_queue = queue.Queue()

            def run_questions():
                try:
                    if sess["mode"] == "multi" and sess["all_photo_records"]:
                        cross_q = system.context_manager.generate_cross_photo_question(
                            analysis_result
                        )
                        system.dialogue_manager.start_dialogue(
                            photo_id=photo_id, analysis_result=analysis_result
                        )
                        if not (cross_q and cross_q.strip()):
                            q_queue.put(("error", "无法生成跨照片关联问题，请重试或重新上传。"))
                            return
                        questions = [cross_q]
                    else:
                        questions = system.dialogue_manager.start_dialogue(
                            photo_id=photo_id,
                            analysis_result=analysis_result,
                            on_stream_chunk=lambda t: q_queue.put(("chunk", t)),
                        )
                    if not questions:
                        q_queue.put(("error", "无法生成访谈问题，请重试或重新上传照片。"))
                        return
                    q_queue.put(("done", questions))
                except ValueError as e:
                    q_queue.put(("error", str(e)))
                except Exception as e:
                    traceback.print_exc()
                    q_queue.put(("error", str(e)))

            thread = threading.Thread(target=run_questions)
            thread.start()
            while True:
                item = q_queue.get()
                if item[0] == "chunk":
                    # 不再把问题生成的逐字输出推到思考过程，只保留简短状态行
                    pass
                elif item[0] == "done":
                    questions = item[1] or []
                    if not questions:
                        yield _sse_message("error", {"error": "无法生成访谈问题，请重试或重新上传照片。"})
                        return
                    break
                elif item[0] == "error":
                    yield _sse_message("error", {"error": item[1]})
                    return
            try:
                os.remove(path)
            except Exception:
                pass
            yield _sse_message("thinking", {"text": "分析完成。"})
            yield _sse_message("result", {
                "photo_id": photo_id,
                "analysis_result": analysis_result,
                "questions": questions,
            })
        except Exception as e:
            _log(f"分析出错: {e}")
            traceback.print_exc()
            yield _sse_message("error", {"error": str(e)})

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/api/answer", methods=["POST"])
def answer():
    """提交一个回答，返回下一问（若有）及当前 qa 列表"""
    _log("收到一条回答 (POST /api/answer)")
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


@app.route("/api/answer/stream", methods=["POST"])
def answer_stream():
    """提交回答（SSE 流式返回：思考过程 + 生成下一问的实时输出 + 结果）"""
    session_id = request.headers.get("X-Session-Id") or (request.get_json() or {}).get("session_id")
    if not session_id or not get_session(session_id):
        return jsonify({"error": "缺少或无效的 session_id"}), 400
    data = request.get_json() or {}
    question = data.get("question", "").strip()
    answer_text = data.get("answer", "").strip()
    if not question or not answer_text:
        return jsonify({"error": "question 和 answer 不能为空"}), 400

    q_queue = queue.Queue()

    def run_answer():
        try:
            sess = get_session(session_id)
            system = sess["system"]
            next_q = system.dialogue_manager.add_answer(
                question,
                answer_text,
                on_stream_chunk=lambda t: q_queue.put(("chunk", t)),
            )
            summary = system.dialogue_manager.get_dialogue_summary()
            qa = summary.get("qa_history", [])
            sess["current_qa"] = qa
            q_queue.put(("done", (next_q, qa)))
        except Exception as e:
            traceback.print_exc()
            q_queue.put(("error", str(e)))

    def generate():
        try:
            yield _sse_message("thinking", {"text": "正在根据您的回答生成下一个问题…"})
            thread = threading.Thread(target=run_answer)
            thread.start()
            while True:
                item = q_queue.get()
                if item[0] == "chunk":
                    yield _sse_message("stream", {"text": item[1]})
                elif item[0] == "done":
                    next_q, qa = item[1]
                    break
                elif item[0] == "error":
                    yield _sse_message("error", {"error": item[1]})
                    return
            yield _sse_message("result", {"next_question": next_q, "qa_history": qa})
        except Exception as e:
            traceback.print_exc()
            yield _sse_message("error", {"error": str(e)})

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


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
    _log("收到生成故事请求，正在生成（可能较久）...")
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
        _log("故事生成完成，已返回。")
        return jsonify({"story": story})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/generate_story/stream", methods=["POST"])
def generate_story_stream():
    """生成故事（SSE 流式返回：阶段提示 + 模型逐字/逐段输出 + 最终结果）"""
    session_id = request.headers.get("X-Session-Id") or (request.get_json() or {}).get("session_id")
    if not session_id or not get_session(session_id):
        return jsonify({"error": "缺少或无效的 session_id"}), 400
    sess = get_session(session_id)
    system = sess["system"]
    chunk_queue = queue.Queue()

    def run_story():
        try:
            if sess["mode"] == "single":
                summary = system.dialogue_manager.get_dialogue_summary()
                qa = summary.get("qa_history", sess["current_qa"])
                story = system.story_generator.generate_single_photo_story(
                    photo_id=sess["current_photo_id"],
                    analysis_result=sess["current_analysis"],
                    qa_history=qa,
                    narrative_style="personal",
                    on_stream_chunk=lambda t: chunk_queue.put(("chunk", t)),
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
            chunk_queue.put(("done", story))
        except Exception as e:
            traceback.print_exc()
            chunk_queue.put(("error", str(e)))

    def generate():
        try:
            yield _sse_message("thinking", {"text": "正在根据照片与访谈内容生成故事（将实时显示生成过程）…"})
            thread = threading.Thread(target=run_story)
            thread.start()
            while True:
                item = chunk_queue.get()
                if item[0] == "chunk":
                    yield _sse_message("stream", {"text": item[1]})
                elif item[0] == "done":
                    story = item[1]
                    break
                elif item[0] == "error":
                    yield _sse_message("error", {"error": item[1]})
                    return
            yield _sse_message("thinking", {"text": "故事生成完成。"})
            yield _sse_message("result", {"story": story})
        except Exception as e:
            traceback.print_exc()
            yield _sse_message("error", {"error": str(e)})

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

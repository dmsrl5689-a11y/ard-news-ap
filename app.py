"""
카드뉴스 썸네일 생성 API 서버

엔드포인트:
  GET  /health          → "ok" (배포 상태 확인용)
  POST /thumbnail       → 썸네일 생성

POST /thumbnail 요청 형식 (JSON):
{
  "bg_base64":   "<배경이미지 base64 문자열>",   # 필수
  "title_lines": ["유튜브로 영어", "공부하는 앱 찾음"],  # 필수 (줄 단위)
  "subtitle":    "AI가 대신 찾아준 영어 공부 앱",   # 선택
  "account":     "@ai.trend.kr"                    # 선택
}

응답 형식 (JSON):
{ "image_base64": "<완성 썸네일 base64>" }
"""

import base64
import io
import os
import tempfile

from flask import Flask, request, jsonify
from card_thumbnail import make_thumbnail

app = Flask(__name__)

# 간단한 API 키 보호 (환경변수 API_SECRET 설정 시 활성화)
API_SECRET = os.environ.get("API_SECRET", "")


@app.route("/health")
def health():
    return "ok"


@app.route("/thumbnail", methods=["POST"])
def thumbnail():
    # ── (선택) API 키 확인 ──
    if API_SECRET:
        if request.headers.get("X-API-KEY", "") != API_SECRET:
            return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "invalid json body"}), 400

    # ── 필수 값 확인 ──
    bg_b64 = data.get("bg_base64")
    title_lines = data.get("title_lines")
    if not bg_b64 or not title_lines:
        return jsonify({"error": "bg_base64 and title_lines are required"}), 400

    bg_path = out_path = None
    try:
        # ── 배경 base64 → 임시 파일 저장 ──
        # "data:image/png;base64,...." 형태로 와도 처리
        if "," in bg_b64 and bg_b64.strip().startswith("data:"):
            bg_b64 = bg_b64.split(",", 1)[1]
        bg_bytes = base64.b64decode(bg_b64)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
            tf.write(bg_bytes)
            bg_path = tf.name

        out_path = tempfile.mktemp(suffix=".png")

        # ── 썸네일 생성 ──
        make_thumbnail(
            bg_path=bg_path,
            title_lines=title_lines,
            subtitle=data.get("subtitle", ""),
            account=data.get("account", "@ai.trend.kr"),
            label=data.get("label", "NEWS"),
            out_path=out_path,
        )

        # ── 완성 이미지 → base64 ──
        with open(out_path, "rb") as f:
            result_b64 = base64.b64encode(f.read()).decode()

        return jsonify({"image_base64": result_b64})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        for p in (bg_path, out_path):
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

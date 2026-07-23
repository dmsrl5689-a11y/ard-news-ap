"""
app.py — 카드뉴스 이미지 생성 API 서버 (Render)

엔드포인트
  GET  /            서버 상태 확인
  POST /thumbnail   표지 카드
  POST /body        본문 카드
  POST /cta         CTA 카드 (고정 문구)
"""

import os
import base64
import tempfile
import traceback

from flask import Flask, request, jsonify

import card_thumbnail
from card_thumbnail import make_thumbnail, make_body, make_cta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 폰트와 프로필 이미지는 이 파일과 같은 폴더 기준으로 찾는다
card_thumbnail.FONT_DIR = os.path.join(BASE_DIR, "fonts")
card_thumbnail.FONT_TPL = os.path.join(card_thumbnail.FONT_DIR, "SCDREAM{}.OTF")
CTA_PROFILE = os.path.join(BASE_DIR, "cta_profile.png")

app = Flask(__name__)


# ── 공통 헬퍼 ────────────────────────────────────────────────

def _save_temp_image(b64):
    """base64 문자열을 임시 PNG 파일로 저장하고 경로를 돌려준다."""
    if not b64:
        raise ValueError("이미지 데이터가 비어 있습니다.")
    if "," in b64:
        b64 = b64.split(",", 1)[1]
    f = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    f.write(base64.b64decode(b64))
    f.close()
    return f.name


def _read_as_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _cleanup(*paths):
    for p in paths:
        if p and os.path.exists(p):
            try:
                os.unlink(p)
            except OSError:
                pass


# ── 라우트 ───────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "endpoints": ["/thumbnail", "/body", "/cta"]
    })


@app.route("/thumbnail", methods=["POST"])
def thumbnail():
    """표지 카드. payload: bg_base64, title_lines[], subtitle, account"""
    bg_path = out_path = None
    try:
        data = request.get_json(force=True) or {}
        bg_path = _save_temp_image(data.get("bg_base64"))
        out_path = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name

        make_thumbnail(
            bg_path=bg_path,
            title_lines=data.get("title_lines") or [""],
            subtitle=data.get("subtitle", ""),
            account=data.get("account", "@jinyinacio"),
            out_path=out_path,
        )
        return jsonify({"image_base64": _read_as_b64(out_path)})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        _cleanup(bg_path, out_path)


@app.route("/body", methods=["POST"])
def body():
    """본문 카드. payload: image_base64, subtitle, lead, body, account"""
    img_path = out_path = None
    try:
        data = request.get_json(force=True) or {}
        img_path = _save_temp_image(data.get("image_base64"))
        out_path = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name

        make_body(
            image_path=img_path,
            subtitle=data.get("subtitle", ""),
            lead=data.get("lead", ""),
            body=data.get("body", ""),
            account=data.get("account", "@jinyinacio"),
            out_path=out_path,
        )
        return jsonify({"image_base64": _read_as_b64(out_path)})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        _cleanup(img_path, out_path)


@app.route("/cta", methods=["POST"])
def cta():
    """CTA 카드. payload 없어도 되고, account만 바꿀 수 있다."""
    out_path = None
    try:
        data = request.get_json(force=True, silent=True) or {}
        out_path = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name

        make_cta(
            profile_path=CTA_PROFILE if os.path.exists(CTA_PROFILE) else None,
            account=data.get("account", "@jinyinacio"),
            out_path=out_path,
        )
        return jsonify({"image_base64": _read_as_b64(out_path)})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        _cleanup(out_path)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

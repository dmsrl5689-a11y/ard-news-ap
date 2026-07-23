"""
card_thumbnail.py
─────────────────────────────────────────────────────────────
카드뉴스 이미지 생성 함수 모음.

  make_thumbnail(...)  표지(1페이지)
  make_body(...)       본문 페이지
  make_cta(...)        마지막 CTA 페이지

본문/CTA는 표지에 쓴 배경 이미지를 그대로 재사용하고
전체를 어둡게 깔아서 시리즈 통일감을 만든다.

필요:
    pip install pillow
    SCDREAM OTF 폰트 9종 (경로는 FONT_DIR 로 지정)
─────────────────────────────────────────────────────────────
"""

import re
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ── 폰트 경로 (SCDREAM1.OTF ~ SCDREAM9.OTF 가 들어있는 폴더) ──
FONT_DIR = "./fonts"          # 환경에 맞게 바꾸면 됨
FONT_TPL = FONT_DIR + "/SCDREAM{}.OTF"

# ── 기본 디자인 상수 ──
CANVAS_W, CANVAS_H = 1080, 1350   # 4:5 세로 카드
SUPERSAMPLE        = 2            # 렌더 후 축소 → 글자 선명
SIDE_MARGIN        = 70           # 좌우 안전 여백(px)
NEON               = (198, 255, 0)   # 형광 포인트 컬러 (#C6FF00)
WHITE              = (255, 255, 255)
BLACK              = (10, 10, 10)
SUBTITLE_GRAY      = (238, 238, 238)


def _font(weight, size, ss):
    """SCDream 특정 굵기/크기 폰트 로드. weight 1~9 (9=Black, 8=Heavy, 6=Bold, 5=Medium, 4=Regular)."""
    return ImageFont.truetype(FONT_TPL.format(weight), size * ss)


def _clean(text):
    """개행/탭이 섞여 들어오면 PIL textlength가 터지므로 미리 한 줄로 정리한다."""
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _clean_lines(lines):
    if lines is None:
        return []
    if isinstance(lines, str):
        lines = [lines]
    return [c for c in (_clean(x) for x in lines) if c]


def _prepare_bg(bg_path, cw, ch, crop_bias=0.30):
    """배경 사진을 4:5로 크롭해서 캔버스 크기로 맞춘다."""
    src = Image.open(bg_path).convert("RGB")
    sw, sh = src.size
    target = cw / ch
    if sw / sh > target:                       # 가로가 넓으면 좌우 크롭(중앙)
        nw = int(sh * target)
        x0 = (sw - nw) // 2
        src = src.crop((x0, 0, x0 + nw, sh))
    else:                                       # 세로가 길면 위/아래 크롭
        nh = int(sw / target)
        y0 = int((sh - nh) * crop_bias)
        src = src.crop((0, y0, sw, y0 + nh))
    return src.resize((cw, ch), Image.LANCZOS)


def _parse_marks(text):
    """
    '바뀐 건 **자세와 표정**뿐이었다'
      → [('바뀐 건 ', False), ('자세와 표정', True), ('뿐이었다', False)]
    ** ** 로 감싼 부분은 형광색으로 강조된다.
    """
    parts = []
    for i, chunk in enumerate(re.split(r"\*\*(.+?)\*\*", text)):
        if chunk:
            parts.append((chunk, i % 2 == 1))
    return parts or [(text, False)]


def _draw_marked(d, x, y, parts, font, base_fill, mark_fill):
    """강조 구간을 색만 바꿔가며 한 줄로 이어 그린다."""
    for chunk, marked in parts:
        d.text((x, y), chunk, font=font, fill=mark_fill if marked else base_fill)
        x += d.textlength(chunk, font=font)
    return x


def _plain(parts):
    return "".join(chunk for chunk, _ in parts)


# ══════════════════════════════════════════════════════════════
#  1) 표지
# ══════════════════════════════════════════════════════════════

def make_thumbnail(
    bg_path,
    title_lines,
    subtitle="",
    account="@jinyinacio",
    label="NEWS",
    center_mark="(   N   )",
    out_path="thumb.png",
    neon=NEON,
    title_weight=9,          # 타이틀 굵기 (9=Black 가장 두꺼움)
    max_title_size=118,      # 타이틀 최대 크기(자동 축소 상한)
    min_title_size=60,       # 타이틀 최소 크기
    crop_bias=0.30,          # 세로 사진일 때 위쪽을 얼마나 살릴지 (0=위, 1=아래)
):
    """카드뉴스 표지 썸네일을 생성해 out_path 에 저장한다."""
    # 타이틀에는 강조 표시를 쓰지 않는다. 들어오면 마커만 제거.
    title_lines = [t.replace("**", "") for t in _clean_lines(title_lines)] or [""]
    subtitle = _clean(subtitle)
    account = _clean(account)
    label = _clean(label)

    ss = SUPERSAMPLE
    cw, ch = CANVAS_W * ss, CANVAS_H * ss
    MX = SIDE_MARGIN * ss

    # ── 1) 배경 사진을 4:5로 크롭 ──
    bg = _prepare_bg(bg_path, cw, ch, crop_bias)

    # ── 2) 상단 살짝 + 하단 강하게 어둡게 (글자 가독성) ──
    ov = Image.new("L", (cw, ch), 0)
    od = ImageDraw.Draw(ov)
    for y in range(ch):
        a = 0
        if y < ch * 0.20:                              # 상단 (헤더용)
            a = int(150 * (1 - y / (ch * 0.20)))
        bot = 0.46                                     # 하단 그라데이션 시작점
        if y > ch * bot:
            t = (y / ch - bot) / (1 - bot)
            a = max(a, int(235 * (t ** 0.85)))         # 하단 진하게
        od.line([(0, y), (cw, y)], fill=a)
    bg = Image.composite(Image.new("RGB", (cw, ch), (8, 8, 8)), bg, ov)

    d = ImageDraw.Draw(bg)

    # ── 3) 상단 헤더 (라벨 · 중앙마크 · 계정명 + 라인) ──
    hy = int(150 * ss)
    fh = _font(6, 20, ss)
    d.text((MX, hy), label, font=fh, fill=WHITE)
    aw = d.textlength(account, font=fh)
    d.text((cw - MX - aw, hy), account, font=fh, fill=WHITE)
    fc = _font(4, 20, ss)
    mw = d.textlength(center_mark, font=fc)
    d.text(((cw - mw) / 2, hy), center_mark, font=fc, fill=neon)   # 형광 포인트 1
    ly = hy + int(46 * ss)
    d.line([(MX, ly), (cw - MX, ly)], fill=WHITE, width=max(1, int(1.4 * ss)))

    # ── 4) 대형 타이틀 (좌우 안 짤리게 자동 크기 조절) ──
    maxw = cw - MX * 2
    size = max_title_size
    ft = _font(title_weight, size, ss)
    while size > min_title_size:
        ft = _font(title_weight, size, ss)
        widest = max(d.textlength(t, font=ft) for t in title_lines)
        if widest <= maxw:
            break
        size -= 2
    asc, desc = ft.getmetrics()
    lh = asc + desc
    gap = int(10 * ss)
    total = lh * len(title_lines) + gap * (len(title_lines) - 1)
    ty = int(ch * 0.55)
    for i, ln in enumerate(title_lines):
        d.text((MX, ty + i * (lh + gap)), ln, font=ft, fill=WHITE)

    # ── 5) 형광 언더바 ──
    uy = ty + total + int(18 * ss)
    d.rectangle([MX, uy, MX + int(120 * ss), uy + int(10 * ss)], fill=neon)  # 형광 포인트 2

    # ── 6) 서브타이틀 ──
    if subtitle:
        # 폭을 넘지 않게 크기를 줄이고, 그래도 길면 2줄로 나눈다
        ssz = 27
        fs = _font(5, ssz, ss)
        while ssz > 20 and d.textlength(subtitle.replace("**", ""), font=fs) > maxw:
            ssz -= 1
            fs = _font(5, ssz, ss)
        sub_lines = _cap_lines(_wrap_marked(d, subtitle, fs, maxw), 2)
        sasc, sdesc = fs.getmetrics()
        sadv = int(ssz * ss * 1.42)
        for i, parts in enumerate(sub_lines):
            _draw_marked(d, MX, uy + int(34 * ss) + i * sadv,
                         parts, fs, SUBTITLE_GRAY, neon)

    # ── 7) 하단 라인 + 형광 화살표 ──
    by = int(ch * 0.915)
    d.line([(MX, by), (cw - MX, by)], fill=WHITE, width=max(1, int(1.4 * ss)))
    fa = _font(6, 42, ss)
    arrow = "→"
    awd = d.textlength(arrow, font=fa)
    d.text((cw - MX - awd, by + int(22 * ss)), arrow, font=fa, fill=neon)    # 형광 포인트 3

    # ── 8) 축소 저장 ──
    bg.resize((CANVAS_W, CANVAS_H), Image.LANCZOS).save(out_path)
    return out_path


# ══════════════════════════════════════════════════════════════
#  2) 본문 페이지  (어두운 단색 배경 + 상단 이미지 카드 + 텍스트)
# ══════════════════════════════════════════════════════════════

BG_DARK     = (13, 13, 15)    # 본문/CTA 배경 단색
CARD_RADIUS = 22              # 이미지 카드 모서리 라운드
LINE_HEIGHT = 1.52            # 본문 줄 높이 배수 (작을수록 촘촘)


def _rounded_image(img, box_w, box_h, radius, crop_bias=0.5):
    """이미지를 box 크기로 꽉 차게 크롭한 뒤 모서리를 둥글린 RGBA를 돌려준다."""
    sw, sh = img.size
    target = box_w / box_h
    if sw / sh > target:                      # 가로가 넓으면 좌우 중앙 크롭
        nw = int(sh * target)
        x0 = (sw - nw) // 2
        img = img.crop((x0, 0, x0 + nw, sh))
    else:                                     # 세로가 길면 위/아래 크롭
        nh = int(sw / target)
        y0 = int((sh - nh) * crop_bias)
        img = img.crop((0, y0, sw, y0 + nh))

    img = img.resize((box_w, box_h), Image.LANCZOS).convert("RGB")

    mask = Image.new("L", (box_w, box_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, box_w - 1, box_h - 1],
                                           radius=radius, fill=255)
    out = Image.new("RGBA", (box_w, box_h))
    out.paste(img, (0, 0), mask)
    return out


def _flatten(text):
    """'**40명**에게' → ('40명에게', [T,T,T,F,F,F])  강조 여부를 글자 단위로 편다."""
    plain, marks = "", []
    for chunk, m in _parse_marks(text):
        plain += chunk
        marks.extend([m] * len(chunk))
    return plain, marks


def _wrap_marked(d, text, font, maxw):
    """
    텍스트를 maxw 폭에 최대한 꽉 차게 자동 줄바꿈한다.
    강조 표시(**)는 글자 단위로 따라간다.
    반환: [[(조각, 강조여부), ...], ...]  (줄 단위)
    """
    plain, marks = _flatten(text)

    # 공백 기준으로 어절 분리 (강조 정보 유지)
    words, wt, wm = [], "", []
    for ch, m in zip(plain, marks):
        if ch == " ":
            if wt:
                words.append((wt, wm))
                wt, wm = "", []
        else:
            wt += ch
            wm.append(m)
    if wt:
        words.append((wt, wm))

    lines, lt, lm = [], "", []
    for word, wmark in words:
        cand = word if not lt else lt + " " + word
        if lt and d.textlength(cand, font=font) > maxw:
            lines.append((lt, lm))
            lt, lm = word, list(wmark)
        else:
            if lt:
                lt = cand
                lm = lm + [False] + list(wmark)
            else:
                lt, lm = word, list(wmark)
    if lt:
        lines.append((lt, lm))

    # 글자 단위 강조를 다시 연속 구간으로 묶는다
    out = []
    for lt, lm in lines:
        runs = []
        for ch, m in zip(lt, lm):
            if runs and runs[-1][1] == m:
                runs[-1][0] += ch
            else:
                runs.append([ch, m])
        out.append([(t, m) for t, m in runs])
    return out


def _cap_lines(lines, limit):
    """줄 수가 상한을 넘으면 잘라내고 마지막 줄에 말줄임표를 붙인다."""
    if len(lines) <= limit:
        return lines
    cut = lines[:limit]
    last = list(cut[-1])
    if last and not last[-1][0].rstrip().endswith(("…", ".", "!", "?")):
        last[-1] = (last[-1][0].rstrip() + "…", last[-1][1])
    cut[-1] = last
    return cut


def make_body(
    image_path,               # 본문 내용과 어울리는 이미지 (없으면 None)
    subtitle="",              # 형광 바 소제목 (검은 글씨)
    body="",                  # 본문 텍스트. 문자열 또는 리스트. **강조** 가능
    lead="",                  # 첫 문장을 굵게 강조하고 싶을 때 (선택)
    account="@jinyinacio",
    out_path="body.png",
    neon=NEON,
    bg_color=BG_DARK,
    crop_bias=0.45,
    max_body_size=40,
    min_body_size=27,
    subtitle_size=36,
    line_height=LINE_HEIGHT,
    image_min_h=330,
    image_max_h=660,
    max_lead_lines=1,         # 굵은 첫 문장은 1줄 고정
    max_body_lines=3,         # 설명 본문은 최대 3줄
):
    """
    본문 카드를 생성한다.

    - 배경은 어두운 단색, 상단에 라운드 이미지 카드
    - 이미지 아래 형광 바 소제목 + 본문
    - 본문은 우측 여백까지 꽉 채워서 자동 줄바꿈된다 (줄바꿈을 직접 넣을 필요 없음)
    - **단어** 로 감싸면 형광색 강조
    - 하단 중앙에 계정명, 구분선 없음
    """
    # 소제목은 무조건 한 줄. 강조 마커도 쓰지 않는다.
    subtitle = _clean(subtitle).replace("**", "")
    lead = _clean(lead)
    if isinstance(body, (list, tuple)):
        body = " ".join(_clean_lines(body))
    body = _clean(body)
    account = _clean(account)

    ss = SUPERSAMPLE
    cw, ch = CANVAS_W * ss, CANVAS_H * ss
    MX = SIDE_MARGIN * ss
    maxw = cw - MX * 2

    canvas = Image.new("RGB", (cw, ch), bg_color)
    d = ImageDraw.Draw(canvas)

    # ── 1) 소제목 바 크기 ──
    pad_x, pad_y = int(19 * ss), int(12 * ss)
    ssize = subtitle_size
    fs = _font(9, ssize, ss)
    while subtitle and ssize > 22 and d.textlength(subtitle, font=fs) > maxw - pad_x * 2:
        ssize -= 2
        fs = _font(9, ssize, ss)
    sasc, sdesc = fs.getmetrics()
    sw_ = d.textlength(subtitle, font=fs) if subtitle else 0
    bar_h = (sasc + sdesc) + pad_y * 2 if subtitle else 0
    bar_gap = int(34 * ss) if subtitle else 0

    # ── 2) 이미지가 최소 높이는 확보되도록 본문 폰트 크기를 자동 결정 ──
    top_limit = int(ch * 0.075)
    bot_limit = int(ch * 0.875)
    img_gap = int(46 * ss)

    text_budget = (bot_limit - top_limit) - bar_h - bar_gap
    if image_path:
        text_budget -= (image_min_h * ss + img_gap)

    bsize = max_body_size
    while True:
        fb = _font(6, bsize, ss)
        fl = _font(8, bsize + 5, ss)
        adv = int(bsize * ss * line_height)
        lead_adv = int((bsize + 5) * ss * line_height)

        lead_lines = _wrap_marked(d, lead, fl, maxw) if lead else []
        body_lines = _wrap_marked(d, body, fb, maxw) if body else []

        lasc, ldesc = fl.getmetrics()
        basc, bdesc = fb.getmetrics()

        text_h = 0
        if lead_lines:
            text_h += lead_adv * (len(lead_lines) - 1) + (lasc + ldesc)
            if body_lines:
                text_h += int(bsize * ss * 0.75)          # lead ↔ body 사이 간격
        if body_lines:
            text_h += adv * (len(body_lines) - 1) + (basc + bdesc)

        fits = (text_h <= text_budget
                and len(lead_lines) <= max_lead_lines
                and len(body_lines) <= max_body_lines)
        if fits or bsize <= min_body_size:
            break
        bsize -= 2

    # 최소 크기에서도 넘치면 강제로 잘라낸다
    lead_lines = _cap_lines(lead_lines, max_lead_lines)
    body_lines = _cap_lines(body_lines, max_body_lines)
    text_h = 0
    if lead_lines:
        text_h += lead_adv * (len(lead_lines) - 1) + (lasc + ldesc)
        if body_lines:
            text_h += int(bsize * ss * 0.75)
    if body_lines:
        text_h += adv * (len(body_lines) - 1) + (basc + bdesc)

    # ── 3) 이미지 높이는 남는 공간으로 ──
    img_card, img_h = None, 0
    if image_path:
        avail = (bot_limit - top_limit) - text_h - bar_h - bar_gap - img_gap
        img_h = int(max(image_min_h * ss, min(image_max_h * ss, avail)))
        img_card = _rounded_image(Image.open(image_path).convert("RGB"),
                                  maxw, img_h, CARD_RADIUS * ss, crop_bias)

    # ── 4) 전체 블록 세로 중앙 정렬 ──
    block_h = (img_h + img_gap if img_card else 0) + bar_h + bar_gap + text_h
    y = top_limit + int(((bot_limit - top_limit) - block_h) / 2)

    if img_card:
        canvas.paste(img_card, (MX, y), img_card)
        y += img_h + img_gap

    if subtitle:
        d.rectangle([MX, y, MX + sw_ + pad_x * 2, y + bar_h], fill=neon)
        d.text((MX + pad_x, y + pad_y), subtitle, font=fs, fill=BLACK)
        y += bar_h + bar_gap

    for i, parts in enumerate(lead_lines):
        _draw_marked(d, MX, y + i * lead_adv, parts, fl, WHITE, neon)
    if lead_lines:
        y += lead_adv * (len(lead_lines) - 1) + (lasc + ldesc)
        if body_lines:
            y += int(bsize * ss * 0.75)

    for i, parts in enumerate(body_lines):
        _draw_marked(d, MX, y + i * adv, parts, fb, (226, 226, 228), neon)

    # ── 5) 하단 중앙 계정명 ──
    if account:
        fa = _font(5, 23, ss)
        aw = d.textlength(account, font=fa)
        d.text(((cw - aw) / 2, int(ch * 0.925)), account, font=fa, fill=(148, 148, 150))

    canvas.resize((CANVAS_W, CANVAS_H), Image.LANCZOS).save(out_path)
    return out_path


# ══════════════════════════════════════════════════════════════
#  3) CTA 페이지 (어두운 단색 배경 + 프로필 원 + 형광 라인)
# ══════════════════════════════════════════════════════════════

CTA_TITLE_LINES = ["매일 업데이트 되는", "AI 이슈 & 정보!"]
CTA_SUBLINE     = "팔로우만 해도 뒤처지지 않습니다."


def make_cta(
    profile_path="cta_profile.png",   # 원형 프로필 이미지 (투명 PNG)
    title_lines=None,
    subline=CTA_SUBLINE,
    account="@jinyinacio",
    out_path="cta.png",
    neon=NEON,
    bg_color=BG_DARK,
    title_size=64,
    subline_size=32,
    account_size=40,
    circle_d=190,                     # 프로필 원 지름
    line_len=150,                     # 형광 라인 길이
    line_gap=35,                      # 라인과 원 사이 간격
    line_thick=7,
):
    """본문과 같은 어두운 단색 배경 위에 CTA를 그린다."""
    title_lines = _clean_lines(title_lines or CTA_TITLE_LINES)
    subline = _clean(subline)
    account = _clean(account)

    ss = SUPERSAMPLE
    cw, ch = CANVAS_W * ss, CANVAS_H * ss

    canvas = Image.new("RGB", (cw, ch), bg_color)
    d = ImageDraw.Draw(canvas)

    ft = _font(9, title_size, ss)
    fsub = _font(5, subline_size, ss)
    fac = _font(8, account_size, ss)

    tasc, tdesc = ft.getmetrics()
    t_adv = int(title_size * ss * 1.32)
    title_h = t_adv * (len(title_lines) - 1) + (tasc + tdesc)

    gap_title_row = int(42 * ss)
    row_h = int(circle_d * ss)
    gap_row_sub = int(46 * ss)
    sasc, sdesc = fsub.getmetrics()
    sub_h = (sasc + sdesc) if subline else 0
    gap_sub_ac = int(26 * ss)
    aasc, adesc = fac.getmetrics()
    ac_h = (aasc + adesc) if account else 0

    block_h = title_h + gap_title_row + row_h + gap_row_sub + sub_h + gap_sub_ac + ac_h
    y = int((ch - block_h) / 2) - int(60 * ss)   # 원본처럼 살짝 위로

    # ── 타이틀 ──
    for i, ln in enumerate(title_lines):
        w = d.textlength(ln, font=ft)
        d.text(((cw - w) / 2, y + i * t_adv), ln, font=ft, fill=WHITE)
    y += title_h + gap_title_row

    # ── 형광 라인 · 프로필 원 · 형광 라인 ──
    cd = int(circle_d * ss)
    ll = int(line_len * ss)
    lg = int(line_gap * ss)
    lt = max(1, int(line_thick * ss))
    total_w = ll + lg + cd + lg + ll
    x = int((cw - total_w) / 2)
    mid = y + cd // 2

    d.rectangle([x, mid - lt // 2, x + ll, mid + lt // 2], fill=neon)
    circle_x = x + ll + lg

    if profile_path:
        prof = Image.open(profile_path).convert("RGBA").resize((cd, cd), Image.LANCZOS)
        canvas.paste(prof, (circle_x, y), prof)

    rx = circle_x + cd + lg
    d.rectangle([rx, mid - lt // 2, rx + ll, mid + lt // 2], fill=neon)
    y += row_h + gap_row_sub

    # ── 서브 문구 ──
    if subline:
        w = d.textlength(subline, font=fsub)
        d.text(((cw - w) / 2, y), subline, font=fsub, fill=(235, 235, 237))
        y += sub_h + gap_sub_ac

    # ── 계정명 (형광) ──
    if account:
        w = d.textlength(account, font=fac)
        d.text(((cw - w) / 2, y), account, font=fac, fill=neon)

    canvas.resize((CANVAS_W, CANVAS_H), Image.LANCZOS).save(out_path)
    return out_path

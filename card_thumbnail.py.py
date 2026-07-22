"""
card_thumbnail.py
─────────────────────────────────────────────────────────────
카드뉴스 썸네일(표지) 생성 함수.

사용 예:
    from card_thumbnail import make_thumbnail

    make_thumbnail(
        bg_path="photo.png",
        title_lines=["유튜브로 영어", "공부하는 앱 찾음"],
        subtitle="AI가 대신 찾아준 영어 공부 앱",
        account="@ai.trend.kr",
        out_path="thumb.png",
    )

필요:
    pip install pillow
    SCDREAM OTF 폰트 9종 (경로는 FONT_DIR 로 지정)
─────────────────────────────────────────────────────────────
"""

from PIL import Image, ImageDraw, ImageFont

# ── 폰트 경로 (SCDREAM1.OTF ~ SCDREAM9.OTF 가 들어있는 폴더) ──
FONT_DIR = "./fonts"          # 환경에 맞게 바꾸면 됨
FONT_TPL = FONT_DIR + "/SCDREAM{}.OTF"

# ── 기본 디자인 상수 ──
CANVAS_W, CANVAS_H = 1080, 1350   # 4:5 세로 카드
SUPERSAMPLE        = 2            # 렌더 후 축소 → 글자 선명
SIDE_MARGIN        = 70           # 좌우 안전 여백(px)
NEON               = (198, 255, 0)   # 형광 포인트 컬러 (#C6FF00)
WHITE              = (255, 255, 255)
SUBTITLE_GRAY      = (238, 238, 238)


def _font(weight, size, ss):
    """SCDream 특정 굵기/크기 폰트 로드. weight 1~9 (9=Black, 8=Heavy, 6=Bold, 5=Medium, 4=Regular)."""
    return ImageFont.truetype(FONT_TPL.format(weight), size * ss)


def make_thumbnail(
    bg_path,
    title_lines,
    subtitle="",
    account="@ai.trend.kr",
    label="NEWS",
    center_mark="(   N   )",
    out_path="thumb.png",
    neon=NEON,
    title_weight=9,          # 타이틀 굵기 (9=Black 가장 두꺼움)
    max_title_size=118,      # 타이틀 최대 크기(자동 축소 상한)
    min_title_size=60,       # 타이틀 최소 크기
    crop_bias=0.30,          # 세로 사진일 때 위쪽을 얼마나 살릴지 (0=위, 1=아래)
):
    """
    카드뉴스 표지 썸네일을 생성해 out_path 에 저장한다.

    title_lines : 리스트. 각 원소가 한 줄. (예: ["유튜브로 영어", "공부하는 앱 찾음"])
                  좌우 여백 안에서 안 짤리도록 폰트 크기가 자동 조절된다.
    """
    ss = SUPERSAMPLE
    cw, ch = CANVAS_W * ss, CANVAS_H * ss
    MX = SIDE_MARGIN * ss

    # ── 0) 입력 텍스트 정리 (줄바꿈/빈줄 제거로 렌더 에러 방지) ──
    # title_lines 안에 \n 이 들어오면 한 줄에 여러 줄이 섞여 폭 측정이 실패한다.
    # 각 원소의 줄바꿈을 공백으로 바꾸고, 빈 줄은 버린다.
    clean_lines = []
    for ln in (title_lines or []):
        s = str(ln).replace("\r", " ").replace("\n", " ").strip()
        s = " ".join(s.split())          # 연속 공백 정리
        if s:
            clean_lines.append(s)
    if not clean_lines:
        clean_lines = [" "]              # 완전히 비면 최소 한 줄(공백) 확보
    title_lines = clean_lines

    # subtitle 도 줄바꿈 제거
    subtitle = " ".join(str(subtitle).replace("\n", " ").split()) if subtitle else ""

    # ── 1) 배경 사진을 4:5로 크롭 ──
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
    bg = src.resize((cw, ch), Image.LANCZOS)

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
        fs = _font(5, 27, ss)
        d.text((MX, uy + int(34 * ss)), subtitle, font=fs, fill=SUBTITLE_GRAY)

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


# ── 단독 실행 시 데모 ──
if __name__ == "__main__":
    make_thumbnail(
        bg_path="/home/claude/thumb/bg_photo.png",
        title_lines=["유튜브로 영어", "공부하는 앱 찾음"],
        subtitle="AI가 대신 찾아준 영어 공부 앱",
        account="@ai.trend.kr",
        out_path="/home/claude/thumb/demo_from_function.png",
    )
    print("saved: demo_from_function.png")

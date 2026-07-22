# 카드뉴스 썸네일 생성 API

## 폴더 구조
- app.py              : Flask API 서버
- card_thumbnail.py   : 썸네일 생성 함수
- requirements.txt    : 파이썬 패키지 목록
- render.yaml         : Render 배포 설정
- fonts/              : SCDream 폰트 9종

## 로컬 실행
    pip install -r requirements.txt
    python app.py
    # http://localhost:8080

## 엔드포인트
- GET  /health     → "ok"
- POST /thumbnail  → 썸네일 생성 (JSON)

## POST 요청 예시
{
  "bg_base64": "<배경이미지 base64>",
  "title_lines": ["유튜브로 영어", "공부하는 앱 찾음"],
  "subtitle": "AI가 대신 찾아준 영어 공부 앱",
  "account": "@ai.trend.kr"
}

## 응답
{ "image_base64": "<완성 썸네일 base64>" }

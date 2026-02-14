# TODO CLI + Web GUI

`todo.py` CLI와 `.todo.json` 데이터를 그대로 사용하면서 Flask 웹 GUI를 추가한 프로젝트입니다.

## Requirements

- Python 3.9+
- Flask

## Setup

```bash
python -m pip install flask
```

## CLI usage

```bash
python todo.py add "할 일"
python todo.py list
python todo.py list --pending
python todo.py done 1
python todo.py rm 1
python todo.py clear
```

## Web GUI run

```bash
python web_app.py
```

브라우저에서 아래 주소를 엽니다.

`http://127.0.0.1:5000`

## Web features

- 할 일 목록 보기
- 할 일 추가
- 체크박스로 완료/미완료 토글
- 항목 삭제

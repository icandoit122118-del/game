# 파이썬 기초 — AI 공부에 필요한 만큼만

「[생성형 AI 기초부터 공부하기](./generative-ai-fundamentals.md)」의 **0단계**를 자세히 푼 문서입니다.

목표는 "파이썬 개발자 되기"가 **아닙니다**. AI 코드를 읽고, 고치고, 직접 쓸 수 있을 만큼만
빠르게 도달하는 것입니다. 그 선이 생각보다 훨씬 낮습니다 — **3주면 충분합니다.**

---

## 먼저: 어디까지 알면 충분한가 (졸업 기준)

아래 코드를 보고 "무슨 일이 일어나는지" 설명할 수 있으면 파이썬 단계는 끝난 겁니다.
지금 이해 안 돼도 정상입니다. 3주 뒤에 다시 보세요.

```python
import json

def 문서_요약(문서들, 최대_길이=200):
    결과 = []
    for 문서 in 문서들:
        본문 = 문서.get("body", "")
        if len(본문) < 10:
            continue
        결과.append({
            "제목": 문서["title"],
            "미리보기": 본문[:최대_길이],
            "단어수": len(본문.split()),
        })
    return sorted(결과, key=lambda x: x["단어수"], reverse=True)

with open("data.json", encoding="utf-8") as f:
    문서들 = json.load(f)

for 항목 in 문서_요약(문서들)[:3]:
    print(f"{항목['제목']} ({항목['단어수']}단어)")
```

여기 쓰인 것: 함수·기본값 인자, 딕셔너리, `for`/`if`/`continue`, 슬라이싱,
리스트, 파일 열기, JSON, `sorted`+`lambda`, f-string. **이게 AI 코드의 90%입니다.**

---

## 3주 계획

| 주차 | 내용 | 하루 | 끝나면 |
|---|---|---|---|
| 1주 | 문법 최소 세트 | 1시간 | 혼자 30줄짜리 스크립트 작성 |
| 2주 | 데이터 다루기 (리스트·딕셔너리·파일·JSON) | 1시간 | 텍스트 파일 읽어 가공·저장 |
| 3주 | 라이브러리와 API 호출 | 1시간 | LLM API를 파이썬으로 호출 |

하루 1시간 × 5일 기준입니다. 주말은 쉬거나 밀린 거 하세요.

---

## 환경 세팅 (30분)

### 처음엔 Google Colab
브라우저에서 바로 씁니다. 설치 0분, 무료, 에러 날 일 없음. **1~2주차는 Colab으로 충분합니다.**

### 3주차부터 로컬
```bash
python3 --version          # 3.10 이상이면 OK

mkdir ai-study && cd ai-study
python3 -m venv .venv       # 가상환경 생성 (프로젝트별 라이브러리 격리)
source .venv/bin/activate   # 활성화 (Windows: .venv\Scripts\activate)
pip install anthropic       # 라이브러리 설치
```

> **가상환경(venv)이 뭔가요?** 프로젝트마다 라이브러리를 따로 담는 상자입니다.
> 안 쓰면 프로젝트 A와 B가 서로 다른 버전을 요구할 때 충돌합니다. 이유는 나중에 알아도 되고,
> **지금은 그냥 새 프로젝트마다 위 3줄을 치는 습관**만 들이세요.

에디터는 **VS Code** + Python 확장이면 됩니다.

---

## 1주차 — 문법 최소 세트

### ① 변수와 자료형
```python
이름 = "클로드"        # str  문자열
나이 = 3               # int  정수
점수 = 4.5             # float 실수
활성 = True            # bool 참/거짓
없음 = None            # 값이 없음을 뜻하는 특별한 값

print(type(이름))      # <class 'str'>
```
> `None`은 AI 코드에서 "아직 결과 없음", "선택 인자 안 넘김"으로 계속 나옵니다.

### ② f-string ⭐ 가장 많이 쓰게 됩니다
```python
주제 = "머신러닝"
개수 = 3

프롬프트 = f"{주제}에 대해 핵심 {개수}가지를 알려줘."
print(프롬프트)        # 머신러닝에 대해 핵심 3가지를 알려줘.

# 여러 줄 프롬프트는 삼중따옴표
프롬프트 = f"""너는 {주제} 강사다.
초보자에게 {개수}문장으로 설명하라."""
```
**프롬프트를 조립하는 게 AI 코드의 절반입니다. f-string이 그 도구입니다.**

### ③ 리스트와 딕셔너리 ⭐⭐ 가장 중요
```python
# 리스트 = 순서 있는 묶음
모델들 = ["opus", "sonnet", "haiku"]
print(모델들[0])       # opus  (0부터 셉니다)
print(모델들[-1])      # haiku (뒤에서 첫 번째)
print(모델들[0:2])     # ['opus', 'sonnet']  (슬라이싱: 0 이상 2 미만)
모델들.append("new")   # 뒤에 추가
print(len(모델들))     # 4  (길이)

# 딕셔너리 = 이름표가 붙은 묶음
메시지 = {"role": "user", "content": "안녕"}
print(메시지["role"])          # user
print(메시지.get("없는키"))     # None  ← 에러 안 남 (안전)
print(메시지["없는키"])         # KeyError! ← 에러 남
메시지["temperature"] = 0.7    # 추가

# 둘을 섞은 형태가 API의 기본 자료구조
messages = [
    {"role": "user", "content": "안녕"},
    {"role": "assistant", "content": "안녕하세요!"},
]
print(messages[0]["content"])   # 안녕
```
> **`.get()`을 쓰세요.** 외부 데이터(API 응답, JSON 파일)는 키가 없을 수 있습니다.

### ④ 반복과 조건
```python
for 모델 in 모델들:
    if "o" in 모델:
        print(f"{모델}에는 o가 있다")
    elif len(모델) > 5:
        print(f"{모델}은 길다")
    else:
        continue          # 이번 회차 건너뛰기

# 인덱스도 같이 필요하면 enumerate
for i, 모델 in enumerate(모델들):
    print(i, 모델)

# 숫자 범위
for i in range(3):        # 0, 1, 2
    print(i)

# 조건 반복
남은 = 3
while 남은 > 0:
    print(남은)
    남은 -= 1
```
> **들여쓰기(스페이스 4칸)가 문법입니다.** 중괄호가 없는 대신 들여쓰기로 블록을 구분합니다.

### ⑤ 함수
```python
def 프롬프트_만들기(주제, 문장수=3, 말투="친근하게"):
    """프롬프트 문자열을 조립해 돌려준다."""   # docstring (설명)
    return f"{주제}에 대해 {문장수}문장으로 {말투} 설명해줘."

print(프롬프트_만들기("RAG"))                    # 기본값 사용
print(프롬프트_만들기("RAG", 5))                 # 순서대로 전달
print(프롬프트_만들기("RAG", 말투="정중하게"))    # 이름으로 전달 ⭐ 이게 제일 많이 보임
```

### ⑥ import
```python
import json                    # 모듈 전체
from pathlib import Path       # 모듈에서 특정 것만
import numpy as np             # 별명 붙이기

print(json.dumps({"a": 1}))
```

### 1주차 실습
- [ ] 리스트에 든 단어들 중 5글자 넘는 것만 출력
- [ ] 이름과 나이를 받아 `"홍길동님은 30세입니다"`를 돌려주는 함수
- [ ] 딕셔너리 리스트에서 `점수`가 80 이상인 항목만 골라 새 리스트 만들기
- [ ] 구구단 3단 출력

---

## 2주차 — 데이터 다루기

### ① 리스트 컴프리헨션 ⭐ AI 코드에 계속 나옵니다
```python
숫자들 = [1, 2, 3, 4, 5]

# 일반 for문
제곱 = []
for n in 숫자들:
    제곱.append(n * n)

# 컴프리헨션 — 같은 뜻, 한 줄
제곱 = [n * n for n in 숫자들]              # [1, 4, 9, 16, 25]
짝수 = [n for n in 숫자들 if n % 2 == 0]     # [2, 4]

# 실전 예: 문서들에서 본문만 뽑기
본문들 = [문서["body"] for 문서 in 문서들]
```

### ② 문자열 다루기 (텍스트가 곧 데이터입니다)
```python
글 = "  생성형 AI 기초 공부  "

글.strip()              # '생성형 AI 기초 공부'  (앞뒤 공백 제거)
글.split()              # ['생성형', 'AI', '기초', '공부']  (공백 기준 분리)
"a,b,c".split(",")      # ['a', 'b', 'c']
"-".join(["a", "b"])    # 'a-b'  (합치기)
글.replace("AI", "인공지능")
글.lower()              # 소문자로
"AI" in 글              # True  (포함 여부)
len(글.split())         # 단어 수 세기

긴글 = "가나다라마바사"
긴글[:3]                # '가나다'  (앞 3글자 — 자르기의 기본)
```
> **청킹(RAG에서 문서 자르기)이 결국 이 슬라이싱입니다.**

### ③ 파일 읽고 쓰기
```python
# 읽기
with open("메모.txt", encoding="utf-8") as f:
    내용 = f.read()              # 전체를 하나의 문자열로

with open("메모.txt", encoding="utf-8") as f:
    줄들 = f.readlines()         # 줄 단위 리스트로

# 쓰기 ("w"는 덮어쓰기, "a"는 이어쓰기)
with open("결과.txt", "w", encoding="utf-8") as f:
    f.write("첫 줄\n")
```
> **`encoding="utf-8"`을 항상 쓰세요.** 안 쓰면 윈도우에서 한글이 깨집니다.
> **`with`를 쓰세요.** 블록이 끝나면 파일이 자동으로 닫힙니다.

### ④ JSON ⭐ API의 공용어
```python
import json

데이터 = {"name": "클로드", "tags": ["AI", "도우미"]}

# 파이썬 객체 ↔ JSON 문자열
문자열 = json.dumps(데이터, ensure_ascii=False, indent=2)  # 객체 → 문자열
다시 = json.loads(문자열)                                   # 문자열 → 객체

# 파일로 저장 / 불러오기
with open("d.json", "w", encoding="utf-8") as f:
    json.dump(데이터, f, ensure_ascii=False, indent=2)

with open("d.json", encoding="utf-8") as f:
    데이터 = json.load(f)
```
> `ensure_ascii=False`가 없으면 한글이 `안녕`처럼 저장됩니다.
> **`dump`/`load`는 파일용, `dumps`/`loads`는 문자열용** (s = string). 헷갈리기 쉬운 지점입니다.

### ⑤ 에러 처리
```python
try:
    결과 = 위험한_함수()
except KeyError as e:
    print(f"키가 없음: {e}")
except Exception as e:           # 나머지 모든 에러
    print(f"실패: {e}")
    결과 = None
```
> API 호출은 **반드시** 실패합니다(네트워크, 사용량 제한, 타임아웃).
> 3주차에 API를 부를 때부터 `try`를 습관화하세요.

### 2주차 실습
- [ ] 텍스트 파일을 읽어 단어 수와 가장 긴 단어 출력
- [ ] 긴 글을 500자씩 잘라 리스트로 만들기 (← RAG 청킹의 원형)
- [ ] 딕셔너리 리스트를 JSON 파일로 저장했다가 다시 읽기
- [ ] 문장 리스트에서 특정 단어가 든 문장만 골라 새 파일로 저장

---

## 3주차 — 라이브러리와 API

### ① 패키지 설치
```bash
pip install anthropic requests      # 설치
pip list                            # 설치된 것 확인
pip freeze > requirements.txt       # 목록 저장 (다른 컴퓨터에서 재현용)
```

### ② API 키 관리 — 하드코딩 절대 금지 ⭐
```bash
# 터미널에서 환경변수로 등록 (셸을 닫으면 사라집니다)
export ANTHROPIC_API_KEY="sk-ant-..."
```
```python
import os
키 = os.environ.get("ANTHROPIC_API_KEY")      # 없으면 None
```
> **코드에 키를 직접 쓰고 깃허브에 올리면 즉시 털립니다.** 봇이 24시간 스캔합니다.
> `.env` 파일을 쓴다면 반드시 `.gitignore`에 `.env`를 넣으세요.

### ③ 첫 LLM API 호출
```python
import anthropic

client = anthropic.Anthropic()      # ANTHROPIC_API_KEY 환경변수를 자동으로 읽습니다

response = client.messages.create(
    model="claude-opus-5",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "파이썬 리스트와 딕셔너리 차이를 3문장으로 알려줘."}
    ],
)

for block in response.content:       # content는 블록들의 리스트입니다
    if block.type == "text":
        print(block.text)
```
1주차에 배운 게 전부 보입니다 — 리스트 `[...]`, 딕셔너리 `{...}`, 이름 붙인 인자, `for`, `if`.

> **`response.content`가 왜 리스트인가?** 응답이 텍스트 한 덩어리가 아니라 여러 종류의
> 블록(텍스트, 추론, 도구 호출)으로 올 수 있기 때문입니다. `block.type`을 먼저 확인하고
> `.text`를 읽는 위 형태가 안전합니다. 인터넷 예제의 `response.content[0].text`는
> 짧게 쓴 것이고, 텍스트가 첫 블록이 아닐 때 깨집니다.

시스템 프롬프트를 주려면:
```python
response = client.messages.create(
    model="claude-opus-5",
    max_tokens=1024,
    system="너는 초보자에게 설명하는 파이썬 강사다. 전문용어를 쓰면 반드시 풀어 쓴다.",
    messages=[{"role": "user", "content": "데코레이터가 뭐야?"}],
)
```
쓸 수 있는 모델 ID와 가격은 바뀌므로 **항상 공식 문서에서 확인**하세요.

### ④ 반복 호출 — 여기서 파이썬이 힘을 씁니다
```python
질문들 = ["RAG가 뭐야?", "임베딩이 뭐야?", "파인튜닝이 뭐야?"]
답변들 = []

for 질문 in 질문들:
    try:
        r = client.messages.create(
            model="claude-opus-5",
            max_tokens=500,
            messages=[{"role": "user", "content": f"{질문} 2문장으로."}],
        )
        텍스트 = "".join(b.text for b in r.content if b.type == "text")
        답변들.append({"질문": 질문, "답변": 텍스트})
    except Exception as e:
        print(f"실패: {질문} → {e}")

import json
with open("답변.json", "w", encoding="utf-8") as f:
    json.dump(답변들, f, ensure_ascii=False, indent=2)
```
**이 30줄이 "AI로 뭔가 만든다"의 실체입니다.** 나머지는 여기서 확장될 뿐입니다.

### ⑤ 웹에서 데이터 가져오기
```python
import requests

r = requests.get("https://api.github.com/repos/python/cpython")
r.raise_for_status()          # 실패하면 에러를 일으킴
데이터 = r.json()              # JSON 응답 → 파이썬 딕셔너리
print(데이터["stargazers_count"])
```

### 3주차 실습
- [ ] 환경변수로 키를 읽어 API 한 번 호출하기
- [ ] 질문 5개를 리스트에 담아 반복 호출 후 JSON으로 저장
- [ ] 텍스트 파일을 읽어 → 500자씩 자르고 → 각 조각을 요약해 → 결과를 파일로 저장
- [ ] 같은 질문을 `system` 프롬프트만 바꿔가며 3번 호출하고 답변 차이 비교

---

## 지금은 안 배워도 되는 것

시간을 아끼기 위해 **명시적으로 건너뛰세요.**

| 주제 | 언제 필요한가 |
|---|---|
| 클래스 직접 설계 (상속, `__init__`, `self`) | 읽을 줄만 알면 됩니다. 직접 설계는 한참 뒤 |
| 데코레이터 만들기 (`@`로 시작하는 것) | `@` 붙은 코드를 쓸 일은 있어도 만들 일은 드뭅니다 |
| `async` / `await` | 동시에 수백 건 호출할 때. 그 전엔 불필요 |
| 제너레이터, `yield` | 대용량 스트리밍 처리할 때 |
| 타입 힌트 엄격하게 | `def f(x: str) -> int:` 는 읽기만. 지금 강박 가질 필요 없음 |
| 멀티스레딩, 패키징, 메타클래스 | AI 공부 단계에선 거의 안 씁니다 |
| 알고리즘 문제풀이 | AI 공부와 거의 무관합니다 |

---

## 자주 만나는 에러 해석법

| 에러 | 뜻 | 대처 |
|---|---|---|
| `IndentationError` | 들여쓰기가 어긋남 | 스페이스 4칸으로 통일 (탭/스페이스 섞지 말 것) |
| `NameError: name 'x' is not defined` | 없는 이름을 씀 | 오타, 또는 정의 전에 사용 |
| `TypeError: can only concatenate str` | 타입이 안 맞음 | `"나이" + 30` ❌ → `f"나이 {30}"` ⭕ |
| `KeyError: 'body'` | 딕셔너리에 그 키가 없음 | `.get("body", "")` 사용 |
| `IndexError: list index out of range` | 리스트 범위 밖 | `len()`으로 길이 먼저 확인 |
| `ModuleNotFoundError` | 라이브러리 미설치 | `pip install 이름` (가상환경 활성화됐는지 확인) |
| `FileNotFoundError` | 경로가 틀림 | 현재 폴더 확인: `import os; print(os.getcwd())` |
| `UnicodeDecodeError` | 인코딩 문제 | `open(..., encoding="utf-8")` |

> **에러 메시지는 맨 아랫줄부터 읽으세요.** 거기에 에러 종류와 이유가 있고,
> 그 위에 어느 파일 몇 번째 줄인지가 있습니다. 그 한 줄을 그대로 검색하면 대개 답이 나옵니다.

---

## 추천 자료

**한국어**
- **점프 투 파이썬** (wikidocs.net) — 무료, 한국어 입문서의 표준. 1~2주차 범위를 그대로 덮습니다.
- **파이썬 코딩 도장** (dojang.io) — 무료, 예제가 잘게 쪼개져 있어 막힐 때 찾아보기 좋습니다.

**영어**
- **Automate the Boring Stuff with Python** — 온라인 무료. 파일·텍스트 자동화 중심이라 AI 공부 방향과 잘 맞습니다.
- **Python Tutor** (pythontutor.com) — 코드가 한 줄씩 실행되는 걸 시각적으로 보여줍니다. 리스트·딕셔너리가 머릿속에 안 그려질 때 특효.
- 공식 문서 Tutorial — 나중에 레퍼런스로.

**안 추천**
- 두꺼운 완전정복서 — 3주차 분량이 300쪽인데 대부분 안 씁니다.
- 알고리즘 문제풀이 사이트 — 재밌지만 AI 공부와는 다른 길입니다.

**막힐 때**: LLM에게 물어보세요. `"이 코드가 왜 에러나는지 초보자에게 설명해줘"` +
코드 + 에러 메시지 전문을 붙여넣으면 대부분 해결됩니다. **이게 지금 파이썬 배우기의 가장 큰 이점입니다.**

---

## 졸업 시험

다음을 보지 않고 스스로 만들 수 있으면 통과입니다. AI 공부 1단계로 넘어가세요.

> 텍스트 파일(`input.txt`)을 읽어 문단 단위로 나누고, 각 문단의 글자 수를 세어,
> 100자 이상인 문단만 골라 `{"번호": 1, "글자수": 320, "미리보기": "앞 50자..."}`
> 형태의 딕셔너리 리스트를 만든 뒤 `result.json`으로 저장하시오.
> 파일이 없으면 에러 메시지를 출력하고 종료할 것.

필요한 재료: `open`/`with`, `split`, `len`, `for`, `if`, 딕셔너리, 리스트, 슬라이싱,
`json.dump`, `try/except`. 전부 위에 있습니다.

---

*파이썬을 "다 배우고" AI로 넘어가려 하지 마세요. 위 3주치면 충분하고,
나머지는 AI 코드를 만지면서 필요할 때 하나씩 채우는 게 훨씬 빠릅니다.*

# FinLit Reading Coach — LangGraph Assignment

교육 & 학습 테마의 LangGraph 과제 제출용 프로젝트입니다.

## 1. 에이전트 설계

### 이름

FinLit Reading Coach — 경제뉴스 문해력 튜터

### 목적

경제뉴스, 공시, 재무제표처럼 초보자가 어렵게 느끼는 금융 정보를 학습자의 수준에 맞춰 설명하고, 핵심 개념·오해 포인트·퀴즈·복습 문장으로 바꾸어 금융문해력을 기르는 것을 목표로 합니다.

이 에이전트는 뉴스를 대신 요약해주는 도구가 아니라, 사용자가 경제 정보를 스스로 읽고 이해하는 힘을 기르도록 돕는 교육용 튜터입니다.

## 2. 해결하려는 문제

경제뉴스는 매일 쏟아지지만, 초보 학습자는 다음을 놓치기 쉽습니다.

- 이 뉴스가 왜 중요한지
- 어떤 경제 개념과 연결되는지
- 숫자와 정책 변화가 내 생활과 어떤 관계가 있는지
- 기사 문장을 자기 말로 다시 설명할 수 있는지

FinLit Reading Coach는 어려운 경제 문장을 짧은 학습 세션으로 바꾸어, 학습자가 경제뉴스를 천천히 읽는 연습을 할 수 있도록 돕습니다.

## 3. 핵심 기능

### 1) 학습 요청 분석 및 경로 선택

사용자가 입력한 경제뉴스 문장 또는 학습 요청에서 핵심 주제와 학습 난이도를 추정합니다.
이후 사용자 입력에 "개념", "뜻", "금리", "환율", "물가", "공시"처럼 보강 설명이 필요한 단어가 있으면 Tool 보강 경로로 보내고, 일반 학습 요청이면 바로 미니 레슨 경로로 보냅니다.

예시 입력:
- 초보자에게 기준금리 동결 뉴스를 쉽게 설명해줘

예시 분석 결과:
- 주제: 기준금리
- 난이도: 입문

### 2) 미니 레슨 생성

주제에 맞는 짧은 학습 콘텐츠를 생성합니다.

구성:
- 오늘 읽을 문장
- 핵심 개념
- 그냥 읽으면 놓치는 포인트
- 나와의 연결
- 한 줄 복습

### 3) 여러 Tool 기반 학습 보강

커스텀 Tool인 `lookup_finlit_concept`를 사용해 기준금리, 환율, 물가, 기업공시 같은 핵심 금융 개념 설명을 찾아 레슨에 추가합니다.
또 다른 커스텀 Tool인 `suggest_review_activity`를 사용해 학습 난이도에 맞는 복습 활동을 추천합니다.

### 4) 병렬 복습 카드 생성

Send API를 사용해 핵심 개념, 오해 포인트, 생활 연결 복습 카드를 병렬로 생성합니다.

### 5) 퀴즈 생성

학습 내용을 확인할 수 있는 객관식 퀴즈를 만듭니다.

### 6) 답변 피드백

사용자의 답변을 채점하고, 왜 그 답이 맞는지 또는 틀렸는지 설명합니다.

## 4. LangGraph 그래프 구조

아래 흐름도는 FinLit Reading Coach의 기본 LangGraph 구조입니다.

![FinLit Reading Coach LangGraph Flow](assets/finlit_langgraph_flow.svg)

~~~mermaid
flowchart TD
    START([START]) --> A[analyze_request<br/>학습 요청 분석]
    A --> R{route_learning_path<br/>Conditional Edge}
    R -->|use_tool| T[enrich_with_tool<br/>커스텀 Tool 2개 호출]
    R -->|direct_lesson| B[build_micro_lesson<br/>미니 레슨 생성]
    T --> B
    B --> S{dispatch_review_tasks<br/>Send API 병렬 분배}
    S --> P1[build_practice_card<br/>핵심 개념 카드]
    S --> P2[build_practice_card<br/>오해 포인트 카드]
    S --> P3[build_practice_card<br/>생활 연결 카드]
    P1 --> C[create_quiz<br/>퀴즈 생성]
    P2 --> C
    P3 --> C
    C --> D[grade_answer<br/>답변 피드백]
    D --> END([END])
~~~

흐름 요약:

START → analyze_request → route_learning_path → enrich_with_tool 또는 build_micro_lesson → Send API 병렬 복습 카드 생성 → create_quiz → grade_answer → END

텍스트 흐름도:

[START]
   |
   v
[analyze_request]
학습 요청 분석
   |
   v
[route_learning_path]
사용자 입력에 따라 Tool 보강 여부 결정
   |
   +-- use_tool --> [enrich_with_tool]
   |                 커스텀 Tool로 개념 설명 보강
   |                 |
   |                 v
   +-----------> [build_micro_lesson]
                미니 레슨 생성
                  |
                  v
[dispatch_review_tasks]
Send API로 복습 카드 병렬 분배
   |
   v
[build_practice_card]
핵심 개념 / 오해 포인트 / 생활 연결 카드 생성
   |
   v
[create_quiz]
퀴즈 생성
   |
   v
[grade_answer]
답변 피드백
   |
   v
[END]

## 5. 노드 설명

| 노드 | 역할 |
|---|---|
| analyze_request | 사용자 입력에서 학습 주제와 난이도를 추정합니다. |
| enrich_with_tool | 커스텀 Tool 2개를 호출해 금융 개념 설명과 복습 활동을 보강합니다. |
| build_micro_lesson | 주제에 맞는 미니 레슨과 한 줄 복습 문장을 생성합니다. |
| build_practice_card | Send API로 병렬 실행되어 복습 카드를 생성합니다. |
| create_quiz | 학습 내용을 확인하는 객관식 퀴즈를 생성합니다. |
| grade_answer | 사용자의 답변을 채점하고 피드백을 제공합니다. |

## 6. State 정의

TutorState는 다음 정보를 관리합니다.

- user_input
- topic
- level
- route
- tool_result
- review_activity
- lesson
- quiz
- practice_cards
- answer
- feedback
- review_sentence

그래프는 `InMemorySaver` 체크포인터와 함께 컴파일되어 `thread_id` 기준으로 실행 상태를 저장합니다.

## 7. 실행 방법

의존성 설치:

    uv sync

실행:

    uv run python main.py

테스트:

    uv run python -m unittest

## 8. 과제 요구사항 충족 여부

| 요구사항 | 충족 여부 |
|---|---|
| LangGraph 사용 | 충족 |
| State 정의 | 충족 |
| 최소 3개 노드 구현 | 충족 — 6개 노드 구현 |
| Conditional Edge 구현 | 충족 — `route_learning_path`가 `use_tool` 또는 `direct_lesson` 경로를 선택 |
| Tool 연동 | 충족 — `lookup_finlit_concept`, `suggest_review_activity` 커스텀 Tool 연동 |
| 병렬 실행 | 충족 — Send API로 복습 카드 3개를 병렬 생성 |
| 메모리 기능 | 충족 — `InMemorySaver` 체크포인터와 `thread_id` 사용 |
| 여러 개의 Tool 연동 | 충족 — 2개 Tool 연동 |
| 기본 그래프 연결 | 충족 |
| 실행 가능한 코드 | 충족 |
| 교육 & 학습 테마 | 충족 |

## 9. 향후 확장 아이디어

- 실제 경제뉴스 제목을 입력받아 학습 세션 생성
- 공시 문장을 학습용 문장으로 변환
- 재무제표 숫자 해석 퀴즈 생성
- 학습자의 오답 패턴 기반 복습 카드 생성
- FinLit 앱의 학습 기록 기능과 연결

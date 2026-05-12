import operator
from typing import Annotated, TypedDict, List, Dict, Literal
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send


class TutorState(TypedDict):
    user_input: str
    topic: str
    level: str
    route: str
    prompt_chain: List[str]
    tool_result: str
    review_activity: str
    lesson: List[str]
    quiz: List[Dict[str, str]]
    practice_cards: Annotated[List[str], operator.add]
    answer: str
    feedback: str
    review_sentence: str
    judge_scores: Dict[str, int]
    judge_feedback: str
    judge_passed: bool


class ReviewTaskState(TypedDict):
    topic: str
    review_focus: str


@tool
def lookup_finlit_concept(topic: str) -> str:
    """금융문해력 학습에 필요한 핵심 개념 설명을 찾아옵니다."""
    glossary = {
        "기준금리": "기준금리는 중앙은행이 경제 상황에 맞춰 조정하는 대표 금리입니다. 대출, 예금, 투자 심리에 넓게 영향을 줍니다.",
        "환율": "환율은 서로 다른 나라 돈의 교환 비율입니다. 수출입 가격, 해외여행 비용, 기업 실적에 영향을 줄 수 있습니다.",
        "물가": "물가는 상품과 서비스 가격의 전반적인 수준입니다. 물가 상승은 같은 돈으로 살 수 있는 양이 줄어드는 상황과 연결됩니다.",
        "기업공시": "기업공시는 투자자와 시장에 중요한 회사 정보를 공식적으로 알리는 자료입니다.",
        "경제뉴스 읽기": "경제뉴스는 사건, 숫자, 원인, 이해관계자, 다음 변화를 함께 연결해 읽어야 합니다.",
    }
    return glossary.get(topic, glossary["경제뉴스 읽기"])


@tool
def suggest_review_activity(level: str) -> str:
    """학습 난이도에 맞는 복습 활동을 추천합니다."""
    activities = {
        "입문": "오늘 배운 개념을 자기 말로 한 문장으로 다시 써보세요.",
        "기초": "기사 제목을 보고 원인, 숫자, 영향을 각각 하나씩 표시해보세요.",
        "심화": "같은 주제를 다룬 다른 기사와 비교해 관점 차이를 찾아보세요.",
    }
    return activities.get(level, activities["기초"])


def analyze_request(state: TutorState) -> TutorState:
    """사용자 입력에서 학습 주제와 난이도를 간단히 추정합니다."""
    text = state["user_input"]

    if "기준금리" in text or "금리" in text:
        topic = "기준금리"
    elif "환율" in text:
        topic = "환율"
    elif "물가" in text or "인플레이션" in text:
        topic = "물가"
    elif "공시" in text:
        topic = "기업공시"
    else:
        topic = "경제뉴스 읽기"

    if any(word in text for word in ["초보", "입문", "쉽게", "처음"]):
        level = "입문"
    elif any(word in text for word in ["심화", "분석", "투자자"]):
        level = "심화"
    else:
        level = "기초"

    return {"topic": topic, "level": level}


def route_learning_path(state: TutorState) -> Literal["use_tool", "direct_lesson"]:
    """사용자 입력에 따라 Tool 보강 경로 또는 바로 레슨 경로를 선택합니다."""
    text = state["user_input"]
    tool_keywords = [
        "개념",
        "뜻",
        "정의",
        "용어",
        "검색",
        "자료",
        "금리",
        "환율",
        "물가",
        "인플레이션",
        "공시",
    ]

    if any(keyword in text for keyword in tool_keywords):
        return "use_tool"
    return "direct_lesson"


def enrich_with_tool(state: TutorState) -> TutorState:
    """커스텀 Tool들을 호출해 레슨에 사용할 참고 설명과 복습 활동을 보강합니다."""
    tool_result = lookup_finlit_concept.invoke(state["topic"])
    review_activity = suggest_review_activity.invoke(state["level"])
    return {
        "route": "use_tool",
        "tool_result": tool_result,
        "review_activity": review_activity,
    }


def build_lesson_prompt(state: TutorState) -> TutorState:
    """앞 노드의 분석 결과를 받아 미니 레슨 생성을 위한 프롬프트를 구성합니다."""
    route = state.get("route") or "direct_lesson"
    prompt = (
        f"[Lesson Prompt] topic={state['topic']}; level={state['level']}; "
        f"route={route}; concept_note={state.get('tool_result', '')}; "
        "include: reading sentence, core concept, hidden point, life connection."
    )
    return {
        "route": route,
        "prompt_chain": [*state.get("prompt_chain", []), prompt],
    }


def build_micro_lesson(state: TutorState) -> TutorState:
    """주제와 난이도에 맞는 짧은 학습 콘텐츠를 만듭니다."""
    topic = state["topic"]
    tool_result = state.get("tool_result", "")

    if topic == "기준금리":
        lesson = [
            "오늘 읽을 문장: 한국은행이 기준금리를 동결하면서 시장은 향후 인하 시점에 주목하고 있다.",
            "핵심 개념: 기준금리는 경제 전체의 돈값을 정하는 기준입니다.",
            "그냥 읽으면 놓치는 포인트: 동결은 '아무 일도 없음'이 아니라, 중앙은행이 물가와 경기 사이에서 아직 신중하다는 신호일 수 있습니다.",
            "나와의 연결: 기준금리는 예금금리, 대출금리, 환율, 주식시장 기대감에 영향을 줍니다.",
        ]
        review_sentence = "기준금리 동결 뉴스는 금리가 그대로라는 뜻을 넘어, 중앙은행이 다음 방향을 아직 확정하지 않았다는 신호로 읽어야 합니다."
    elif topic == "환율":
        lesson = [
            "오늘 읽을 문장: 원/달러 환율이 상승하면서 수입 물가 부담이 커질 수 있다는 우려가 나왔다.",
            "핵심 개념: 환율은 한 나라 돈과 다른 나라 돈의 교환 비율입니다.",
            "그냥 읽으면 놓치는 포인트: 환율 상승은 수출기업에는 유리할 수 있지만, 수입물가에는 부담이 될 수 있습니다.",
            "나와의 연결: 해외여행, 수입품 가격, 기업 실적, 물가에 영향을 줄 수 있습니다.",
        ]
        review_sentence = "환율 뉴스는 숫자의 상승·하락보다 누가 이익을 보고 누가 부담을 지는지 함께 읽어야 합니다."
    else:
        lesson = [
            f"오늘의 주제: {topic}",
            "핵심 개념: 경제뉴스는 결과보다 원인과 다음 변화를 읽는 것이 중요합니다.",
            "그냥 읽으면 놓치는 포인트: 기사 문장 뒤에 있는 숫자, 이해관계자, 정책 신호를 함께 봐야 합니다.",
            "나와의 연결: 경제뉴스는 소비, 투자, 취업, 기업 활동과 연결됩니다.",
        ]
        review_sentence = "경제뉴스는 사건 자체보다 그 사건이 어떤 판단으로 이어지는지 읽는 연습이 중요합니다."

    if tool_result:
        lesson.append(f"도구 참고: {tool_result}")

    if state.get("review_activity"):
        lesson.append(f"추천 복습 활동: {state['review_activity']}")

    return {
        "route": state.get("route") or "direct_lesson",
        "lesson": lesson,
        "review_sentence": review_sentence,
    }


def dispatch_review_tasks(state: TutorState) -> List[Send]:
    """Send API로 복습 카드 생성 작업을 병렬 분배합니다."""
    review_focuses = ["핵심 개념", "오해 포인트", "생활 연결"]
    return [
        Send(
            "build_practice_card",
            {
                "topic": state["topic"],
                "review_focus": review_focus,
            },
        )
        for review_focus in review_focuses
    ]


def build_practice_card(state: ReviewTaskState) -> Dict[str, List[str]]:
    """병렬 작업 단위로 주제별 복습 카드를 하나 생성합니다."""
    card = f"{state['review_focus']} 복습 카드: '{state['topic']}' 주제를 한 문장으로 설명해보세요."
    return {"practice_cards": [card]}


def build_quiz_prompt(state: TutorState) -> TutorState:
    """레슨과 복습 카드 결과를 받아 퀴즈 생성을 위한 다음 프롬프트를 구성합니다."""
    prompt = (
        f"[Quiz Prompt] topic={state['topic']}; level={state['level']}; "
        f"lesson_items={len(state['lesson'])}; practice_cards={len(state['practice_cards'])}; "
        "create one multiple-choice question with four options and an explanation."
    )
    return {"prompt_chain": [*state.get("prompt_chain", []), prompt]}


def create_quiz(state: TutorState) -> TutorState:
    """학습 내용을 확인하는 객관식 퀴즈를 만듭니다."""
    topic = state["topic"]

    if topic == "기준금리":
        quiz = [{
            "question": "기준금리 동결 뉴스를 읽을 때 가장 중요한 질문은 무엇일까요?",
            "A": "오늘 주가가 무조건 올랐는가?",
            "B": "왜 금리를 내리지 않고 유지했는가?",
            "C": "은행 이름이 무엇인가?",
            "D": "기사 제목이 몇 글자인가?",
            "correct": "B",
            "explanation": "기준금리 뉴스는 결과보다 결정의 이유와 다음 변화 가능성을 읽는 것이 중요합니다.",
        }]
    else:
        quiz = [{
            "question": "경제뉴스를 읽을 때 가장 중요한 태도는 무엇일까요?",
            "A": "제목만 보고 판단한다.",
            "B": "숫자와 원인, 다음 변화를 함께 본다.",
            "C": "댓글 반응만 확인한다.",
            "D": "어려운 용어는 모두 무시한다.",
            "correct": "B",
            "explanation": "경제뉴스 문해력은 사건, 숫자, 원인, 영향을 연결해 읽는 힘입니다.",
        }]

    return {"quiz": quiz}


def grade_answer(state: TutorState) -> TutorState:
    """사용자의 답변을 채점하고 피드백을 제공합니다."""
    quiz = state["quiz"][0]
    user_answer = state.get("answer", "").strip().upper()
    correct = quiz["correct"]

    if user_answer == correct:
        feedback = f"정답입니다. {quiz['explanation']}"
    elif user_answer:
        feedback = f"아쉽습니다. 정답은 {correct}입니다. {quiz['explanation']}"
    else:
        feedback = f"아직 답변이 없습니다. 문제를 읽고 A/B/C/D 중 하나를 골라보세요. 힌트: {quiz['explanation']}"

    return {"feedback": feedback}


def ai_as_judge_evaluate(state: TutorState) -> TutorState:
    """AI-as-judge 패턴을 흉내 낸 루브릭 평가 노드입니다."""
    lesson_text = " ".join(state["lesson"])
    quiz = state["quiz"][0] if state["quiz"] else {}
    feedback = state.get("feedback", "")

    scores = {
        "lesson_grounding": 1 if state["topic"] in lesson_text else 0,
        "lesson_structure": int(
            all(marker in lesson_text for marker in ["핵심 개념", "나와의 연결"])
        ),
        "quiz_quality": int(
            bool(quiz.get("question"))
            and all(key in quiz for key in ["A", "B", "C", "D", "correct", "explanation"])
            and quiz.get("correct") in {"A", "B", "C", "D"}
        ),
        "feedback_quality": int(bool(feedback) and quiz.get("explanation", "") in feedback),
    }
    passed = sum(scores.values()) >= 3
    missing = [name for name, score in scores.items() if score == 0]

    if passed:
        judge_feedback = "AI-as-judge 평가 통과: 레슨, 퀴즈, 피드백이 학습 목표에 맞게 구성되었습니다."
    else:
        judge_feedback = f"AI-as-judge 평가 보완 필요: {', '.join(missing)} 항목을 개선하세요."

    return {
        "judge_scores": scores,
        "judge_feedback": judge_feedback,
        "judge_passed": passed,
    }


memory = InMemorySaver()


def make_initial_state(user_input: str, answer: str = "") -> TutorState:
    """그래프 실행에 필요한 기본 TutorState를 만듭니다."""
    return {
        "user_input": user_input,
        "topic": "",
        "level": "",
        "route": "",
        "prompt_chain": [],
        "tool_result": "",
        "review_activity": "",
        "lesson": [],
        "quiz": [],
        "practice_cards": [],
        "answer": answer,
        "feedback": "",
        "review_sentence": "",
        "judge_scores": {},
        "judge_feedback": "",
        "judge_passed": False,
    }


def build_graph(use_memory: bool = True):
    graph_builder = StateGraph(TutorState)

    graph_builder.add_node("analyze_request", analyze_request)
    graph_builder.add_node("enrich_with_tool", enrich_with_tool)
    graph_builder.add_node("build_lesson_prompt", build_lesson_prompt)
    graph_builder.add_node("build_micro_lesson", build_micro_lesson)
    graph_builder.add_node("build_practice_card", build_practice_card)
    graph_builder.add_node("build_quiz_prompt", build_quiz_prompt)
    graph_builder.add_node("create_quiz", create_quiz)
    graph_builder.add_node("grade_answer", grade_answer)
    graph_builder.add_node("ai_as_judge_evaluate", ai_as_judge_evaluate)

    graph_builder.add_edge(START, "analyze_request")
    graph_builder.add_conditional_edges(
        "analyze_request",
        route_learning_path,
        {
            "use_tool": "enrich_with_tool",
            "direct_lesson": "build_lesson_prompt",
        },
    )
    graph_builder.add_edge("enrich_with_tool", "build_lesson_prompt")
    graph_builder.add_edge("build_lesson_prompt", "build_micro_lesson")
    graph_builder.add_conditional_edges(
        "build_micro_lesson",
        dispatch_review_tasks,
        ["build_practice_card"],
    )
    graph_builder.add_edge("build_practice_card", "build_quiz_prompt")
    graph_builder.add_edge("build_quiz_prompt", "create_quiz")
    graph_builder.add_edge("create_quiz", "grade_answer")
    graph_builder.add_edge("grade_answer", "ai_as_judge_evaluate")
    graph_builder.add_edge("ai_as_judge_evaluate", END)

    if use_memory:
        return graph_builder.compile(checkpointer=memory)
    return graph_builder.compile()


def main():
    app = build_graph()

    initial_state = make_initial_state(
        "초보자에게 기준금리 동결 뉴스를 쉽게 설명해줘",
        answer="B",
    )

    config = {"configurable": {"thread_id": "finlit-demo"}}
    result = app.invoke(initial_state, config)

    print("=== FinLit Reading Coach ===")
    print("주제:", result["topic"])
    print("난이도:", result["level"])
    print("학습 경로:", result["route"])

    print("\n=== 미니 레슨 ===")
    for line in result["lesson"]:
        print("-", line)

    print("\n=== 퀴즈 ===")
    q = result["quiz"][0]
    print(q["question"])
    for key in ["A", "B", "C", "D"]:
        print(f"{key}. {q[key]}")

    print("\n=== 피드백 ===")
    print(result["feedback"])

    print("\n=== 한 줄 복습 ===")
    print(result["review_sentence"])

    print("\n=== 병렬 복습 카드 ===")
    for card in result["practice_cards"]:
        print("-", card)

    print("\n=== AI-as-judge 평가 ===")
    print(result["judge_feedback"])
    print(result["judge_scores"])


if __name__ == "__main__":
    main()

from uuid import uuid4

import streamlit as st

from main import build_graph, make_initial_state


st.set_page_config(
    page_title="FinLit Reading Coach",
    page_icon=":blue_book:",
    layout="centered",
)


@st.cache_resource
def get_graph():
    return build_graph()


def render_learning_session(result: dict) -> None:
    st.markdown(f"**주제:** {result['topic']}  \n**난이도:** {result['level']}  \n**경로:** {result['route']}")

    if result.get("prompt_chain"):
        st.markdown("#### 프롬프트 체이닝")
        for index, prompt in enumerate(result["prompt_chain"], start=1):
            st.code(f"{index}. {prompt}", language="text")

    st.markdown("#### 미니 레슨")
    for line in result["lesson"]:
        st.markdown(f"- {line}")

    if result["practice_cards"]:
        st.markdown("#### 병렬 복습 카드")
        for card in result["practice_cards"]:
            st.markdown(f"- {card}")

    if result["quiz"]:
        quiz = result["quiz"][0]
        st.markdown("#### 퀴즈")
        st.markdown(quiz["question"])
        for key in ["A", "B", "C", "D"]:
            st.markdown(f"**{key}.** {quiz[key]}")

    st.markdown("#### 피드백")
    st.info(result["feedback"])

    st.markdown("#### 한 줄 복습")
    st.success(result["review_sentence"])

    if result.get("judge_feedback"):
        st.markdown("#### AI-as-judge 평가")
        if result.get("judge_passed"):
            st.success(result["judge_feedback"])
        else:
            st.warning(result["judge_feedback"])
        st.json(result.get("judge_scores", {}))


if "thread_id" not in st.session_state:
    st.session_state.thread_id = f"streamlit-{uuid4()}"

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "경제뉴스나 금융 개념을 입력하면 미니 레슨, 복습 카드, 퀴즈를 만들어드릴게요.",
        }
    ]

if "pending_quiz" not in st.session_state:
    st.session_state.pending_quiz = None


st.title("FinLit Reading Coach")

with st.sidebar:
    st.subheader("고급 패턴")
    st.markdown("- Option B: 프롬프트 체이닝")
    st.markdown("- Option B: Send API 기반 병렬 복습 카드 생성")
    st.markdown("- Option B: Orchestrator-Workers")
    st.markdown("- Option C: AI-as-judge 평가")
    st.markdown("- LangGraph 체크포인터로 thread_id별 상태 저장")
    if st.button("대화 초기화", use_container_width=True):
        st.session_state.thread_id = f"streamlit-{uuid4()}"
        st.session_state.messages = st.session_state.messages[:1]
        st.session_state.pending_quiz = None
        st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        content = message["content"]
        if isinstance(content, dict):
            render_learning_session(content)
        else:
            st.markdown(content)

prompt = st.chat_input("예: 초보자에게 기준금리 동결 뉴스를 쉽게 설명해줘")

if prompt:
    app = get_graph()
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    answer = ""
    if (
        st.session_state.pending_quiz
        and prompt.strip().upper() in {"A", "B", "C", "D"}
    ):
        answer = prompt.strip().upper()
        user_input = st.session_state.pending_quiz["user_input"]
    else:
        user_input = prompt

    with st.chat_message("assistant"):
        with st.spinner("학습 세션을 만들고 있어요..."):
            result = app.invoke(make_initial_state(user_input, answer=answer), config)
        render_learning_session(result)

    st.session_state.pending_quiz = {"user_input": user_input}
    st.session_state.messages.append({"role": "assistant", "content": result})

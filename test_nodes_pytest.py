import pytest

from main import (
    ai_as_judge_evaluate,
    analyze_request,
    build_graph,
    build_lesson_prompt,
    build_quiz_prompt,
    create_quiz,
    grade_answer,
    make_initial_state,
)


@pytest.mark.parametrize(
    ("user_input", "expected_topic", "expected_level"),
    [
        ("초보자에게 기준금리 개념을 쉽게 설명해줘", "기준금리", "입문"),
        ("환율 뉴스를 분석해줘", "환율", "심화"),
        ("물가 기사 읽는 법", "물가", "기초"),
    ],
)
def test_analyze_request_node_extracts_topic_and_level(
    user_input,
    expected_topic,
    expected_level,
):
    result = analyze_request(make_initial_state(user_input))

    assert result["topic"] == expected_topic
    assert result["level"] == expected_level


def test_prompt_chaining_nodes_append_lesson_and_quiz_prompts():
    state = make_initial_state("초보자에게 기준금리 개념을 쉽게 설명해줘")
    state.update({"topic": "기준금리", "level": "입문", "route": "use_tool"})

    lesson_prompt_result = build_lesson_prompt(state)
    state.update(lesson_prompt_result)
    state.update(
        {
            "lesson": ["핵심 개념: 기준금리는 돈값입니다.", "나와의 연결: 대출금리에 영향을 줍니다."],
            "practice_cards": ["핵심 개념 카드", "오해 포인트 카드", "생활 연결 카드"],
        }
    )
    quiz_prompt_result = build_quiz_prompt(state)

    prompt_chain = quiz_prompt_result["prompt_chain"]
    assert len(prompt_chain) == 2
    assert prompt_chain[0].startswith("[Lesson Prompt]")
    assert prompt_chain[1].startswith("[Quiz Prompt]")
    assert "practice_cards=3" in prompt_chain[1]


def test_ai_as_judge_node_scores_complete_learning_session():
    state = make_initial_state("초보자에게 기준금리 개념을 쉽게 설명해줘", answer="B")
    state.update(
        {
            "topic": "기준금리",
            "level": "입문",
            "lesson": [
                "핵심 개념: 기준금리는 경제 전체의 돈값을 정하는 기준입니다.",
                "나와의 연결: 기준금리는 예금금리와 대출금리에 영향을 줍니다.",
            ],
        }
    )
    state.update(create_quiz(state))
    state.update(grade_answer(state))

    result = ai_as_judge_evaluate(state)

    assert result["judge_passed"] is True
    assert result["judge_scores"]["lesson_grounding"] == 1
    assert result["judge_scores"]["quiz_quality"] == 1
    assert "평가 통과" in result["judge_feedback"]


def test_graph_runs_prompt_chain_parallel_workers_and_ai_judge():
    app = build_graph(use_memory=False)

    result = app.invoke(make_initial_state("초보자에게 기준금리 개념을 쉽게 설명해줘", answer="B"))

    assert len(result["prompt_chain"]) == 2
    assert len(result["practice_cards"]) == 3
    assert result["judge_passed"] is True
    assert sum(result["judge_scores"].values()) >= 3

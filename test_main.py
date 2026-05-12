import unittest

from main import (
    TutorState,
    build_graph,
    lookup_finlit_concept,
    make_initial_state,
    memory,
    route_learning_path,
    suggest_review_activity,
)


def make_state(user_input: str, answer: str = "B") -> TutorState:
    return make_initial_state(user_input, answer=answer)


class FinLitReadingCoachTest(unittest.TestCase):
    def test_route_uses_tool_for_concept_request(self):
        state = make_state("기준금리 개념을 초보자에게 쉽게 설명해줘")

        self.assertEqual(route_learning_path(state), "use_tool")

    def test_route_can_skip_tool_for_general_request(self):
        state = make_state("경제뉴스 읽는 연습을 하고 싶어")

        self.assertEqual(route_learning_path(state), "direct_lesson")

    def test_custom_tool_returns_finlit_concept(self):
        result = lookup_finlit_concept.invoke("환율")

        self.assertIn("교환 비율", result)

    def test_second_custom_tool_returns_review_activity(self):
        result = suggest_review_activity.invoke("입문")

        self.assertIn("자기 말", result)

    def test_initial_state_helper_builds_graph_ready_state(self):
        state = make_state("환율 개념 알려줘", answer="A")

        self.assertEqual(state["user_input"], "환율 개념 알려줘")
        self.assertEqual(state["answer"], "A")
        self.assertEqual(state["practice_cards"], [])
        self.assertEqual(state["quiz"], [])

    def test_graph_enriches_lesson_when_tool_path_is_selected(self):
        app = build_graph(use_memory=False)

        result = app.invoke(make_state("초보자에게 기준금리 개념을 쉽게 설명해줘"))

        self.assertEqual(result["topic"], "기준금리")
        self.assertEqual(result["level"], "입문")
        self.assertEqual(result["route"], "use_tool")
        self.assertTrue(result["tool_result"])
        self.assertTrue(result["review_activity"])
        self.assertTrue(any(line.startswith("도구 참고:") for line in result["lesson"]))
        self.assertTrue(any(line.startswith("추천 복습 활동:") for line in result["lesson"]))
        self.assertIn("정답입니다.", result["feedback"])

    def test_graph_keeps_direct_lesson_path_available(self):
        app = build_graph(use_memory=False)

        result = app.invoke(make_state("경제뉴스 읽는 연습을 하고 싶어"))

        self.assertEqual(result["route"], "direct_lesson")
        self.assertEqual(result["tool_result"], "")
        self.assertFalse(any(line.startswith("도구 참고:") for line in result["lesson"]))

    def test_send_api_builds_parallel_practice_cards(self):
        app = build_graph(use_memory=False)

        result = app.invoke(make_state("초보자에게 기준금리 개념을 쉽게 설명해줘"))

        self.assertEqual(len(result["practice_cards"]), 3)
        self.assertTrue(any("핵심 개념" in card for card in result["practice_cards"]))
        self.assertTrue(any("오해 포인트" in card for card in result["practice_cards"]))
        self.assertTrue(any("생활 연결" in card for card in result["practice_cards"]))

    def test_memory_checkpointer_stores_thread_state(self):
        app = build_graph()
        config = {"configurable": {"thread_id": "test-memory-thread"}}

        result = app.invoke(make_state("환율 개념을 쉽게 설명해줘"), config)
        snapshot = app.get_state(config)

        self.assertEqual(snapshot.values["topic"], result["topic"])
        self.assertTrue(list(memory.list(config)))


if __name__ == "__main__":
    unittest.main()

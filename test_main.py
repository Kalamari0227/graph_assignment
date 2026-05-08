import unittest

from main import (
    TutorState,
    build_graph,
    lookup_finlit_concept,
    route_learning_path,
)


def make_state(user_input: str, answer: str = "B") -> TutorState:
    return {
        "user_input": user_input,
        "topic": "",
        "level": "",
        "route": "",
        "tool_result": "",
        "lesson": [],
        "quiz": [],
        "answer": answer,
        "feedback": "",
        "review_sentence": "",
    }


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

    def test_graph_enriches_lesson_when_tool_path_is_selected(self):
        app = build_graph()

        result = app.invoke(make_state("초보자에게 기준금리 개념을 쉽게 설명해줘"))

        self.assertEqual(result["topic"], "기준금리")
        self.assertEqual(result["level"], "입문")
        self.assertEqual(result["route"], "use_tool")
        self.assertTrue(result["tool_result"])
        self.assertTrue(any(line.startswith("도구 참고:") for line in result["lesson"]))
        self.assertIn("정답입니다.", result["feedback"])

    def test_graph_keeps_direct_lesson_path_available(self):
        app = build_graph()

        result = app.invoke(make_state("경제뉴스 읽는 연습을 하고 싶어"))

        self.assertEqual(result["route"], "direct_lesson")
        self.assertEqual(result["tool_result"], "")
        self.assertFalse(any(line.startswith("도구 참고:") for line in result["lesson"]))


if __name__ == "__main__":
    unittest.main()

"""answer.guard 的測試：只測檢查函式，不呼叫模型。"""
import pytest

from faq.answer import REFUSAL, GuardError, RuleAnswer, build_prompt, guard

TOP3 = ["travelling", "double-dribble", "three-seconds"]


def test_sources_within_top3_pass():
    ans = RuleAnswer(answer="走三步是走步違例。", source_ids=["travelling"], confidence="高")
    assert guard(ans, TOP3) is ans


def test_source_outside_top3_blocked():
    ans = RuleAnswer(answer="……", source_ids=["travelling", "shot-clock"], confidence="中")
    with pytest.raises(GuardError, match="shot-clock"):
        guard(ans, TOP3)


def test_made_up_id_blocked():
    ans = RuleAnswer(answer="……", source_ids=["nba-zone-defense"], confidence="高")
    with pytest.raises(GuardError):
        guard(ans, TOP3)


def test_answer_without_source_blocked():
    ans = RuleAnswer(answer="走三步是走步違例。", source_ids=[], confidence="高")
    with pytest.raises(GuardError, match="出處"):
        guard(ans, TOP3)


def test_refusal_without_source_passes():
    ans = RuleAnswer(answer=REFUSAL, source_ids=[], confidence="低")
    assert guard(ans, TOP3) == ans


def test_answer_that_is_only_an_id_blocked():
    ans = RuleAnswer(answer="foul-limit", source_ids=["foul-limit"], confidence="高")
    with pytest.raises(GuardError, match="id"):
        guard(ans, ["foul-limit", "team-fouls", "disruptive-foul"])


def test_answer_mentioning_id_with_content_passes():
    ans = RuleAnswer(answer="根據 foul-limit，累積 5 次犯規要離場。", source_ids=["foul-limit"], confidence="高")
    assert guard(ans, ["foul-limit", "team-fouls", "disruptive-foul"]) == ans


def test_low_confidence_becomes_refusal():
    ans = RuleAnswer(answer="排球一局打到 25 分。", source_ids=["travelling"], confidence="低")
    out = guard(ans, TOP3)
    assert out.answer == REFUSAL and out.source_ids == []


def test_too_long_answer_blocked():
    ans = RuleAnswer(answer="走" * 101, source_ids=["travelling"], confidence="高")
    with pytest.raises(GuardError, match="超過"):
        guard(ans, TOP3)


def test_low_confidence_with_bad_id_still_blocked():
    ans = RuleAnswer(answer="……", source_ids=["shot-clock"], confidence="低")
    with pytest.raises(GuardError):
        guard(ans, TOP3)


def test_confidence_must_be_allowed_value():
    with pytest.raises(ValueError):
        RuleAnswer(answer="……", source_ids=[], confidence="很高")


def test_prompt_contains_only_given_items():
    items = [{"id": "travelling", "source": "FIBA OBR 2026 Art. 25", "question": "Q", "answer": "A"}]
    prompt = build_prompt("走三步", items)
    assert "travelling（FIBA OBR 2026 Art. 25）" in prompt and "走三步" in prompt
    assert "只能從這些 id 選：travelling" in prompt

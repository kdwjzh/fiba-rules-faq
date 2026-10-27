"""report.evaluate 的測試：用手寫的檢索結果，不呼叫模型。"""
from faq.report import evaluate, evaluate_answers, pct

ROWS = [
    {"expected": ["a"], "top": [("a", 0.9), ("b", 0.5), ("c", 0.4)]},       # Hit@1
    {"expected": ["c"], "top": [("a", 0.7), ("c", 0.6), ("b", 0.4)]},       # 只有 Hit@3
    {"expected": ["d"], "top": [("a", 0.45), ("b", 0.4), ("c", 0.3)]},      # 沒中，而且低於門檻（誤拒）
    {"expected": ["b", "c"], "top": [("c", 0.8), ("a", 0.5), ("b", 0.4)]},  # 多個可接受答案
    {"expected": [], "top": [("a", 0.3), ("b", 0.2), ("c", 0.1)]},          # 題庫外，正確拒答
    {"expected": [], "top": [("a", 0.6), ("b", 0.2), ("c", 0.1)]},          # 題庫外，沒擋到
]


def test_evaluate_counts():
    m = evaluate(ROWS, threshold=0.5)
    assert m["in_scope"] == 4 and m["out_of_scope"] == 2
    assert m["hit1"] == 2
    assert m["hit3"] == 3
    assert m["refused_out_of_scope"] == 1
    assert m["false_refusal"] == 1


def test_threshold_changes_refusal_only():
    low = evaluate(ROWS, threshold=0.2)
    assert low["refused_out_of_scope"] == 0 and low["false_refusal"] == 0
    assert low["hit1"] == 2 and low["hit3"] == 3


def test_evaluate_answers():
    answers = [
        {"expected": ["a"], "seconds": 10, "answer": "…", "source_ids": ["a"]},     # 採用、出處正確
        {"expected": ["a"], "seconds": 10, "answer": "…", "source_ids": ["b"]},     # 採用、出處不對
        {"expected": ["a"], "seconds": 10, "guard": "超過 100 字"},                  # guard 擋下
        {"expected": ["a"], "seconds": 0, "answer": "拒答", "source_ids": []},       # 誤拒
        {"expected": [], "seconds": 0, "answer": "拒答", "source_ids": []},          # 題庫外拒答
        {"expected": [], "seconds": 10, "answer": "…", "source_ids": ["a"]},        # 題庫外沒擋到
    ]
    a = evaluate_answers(answers, refusal="拒答")
    assert (a["adopted"], a["correct_source"], a["guard_blocked"]) == (2, 1, 1)
    assert a["refused_in_scope"] == 1 and a["refused_out_of_scope"] == 1
    assert a["avg_seconds"] == 6.7


def test_pct():
    assert pct(17, 24) == "17/24（71%）"
    assert pct(0, 0) == "—"

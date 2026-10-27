"""題庫與測試查詢的格式檢查，不呼叫模型。"""
import json

import pytest

from faq import store

ITEMS = store.load_faq()
IDS = [it["id"] for it in ITEMS]
REQUIRED = ["id", "question", "aliases", "answer", "category", "source", "status"]
CATEGORIES = {"比賽基本", "違例", "犯規", "罰則", "比賽管理", "2026 新制"}


@pytest.mark.parametrize("item", ITEMS, ids=IDS)
def test_required_fields(item):
    for key in REQUIRED:
        assert key in item, f"缺少欄位 {key}"
    for key in ["id", "question", "answer", "source"]:
        assert isinstance(item[key], str) and item[key].strip(), f"{key} 不可為空"
    assert isinstance(item["aliases"], list)


@pytest.mark.parametrize("item", ITEMS, ids=IDS)
def test_values(item):
    assert item["category"] in CATEGORIES
    # 重播（IRS）規定在附錄，沒有條號
    assert item["source"].startswith(("FIBA OBR 2026 Art.", "FIBA OBR 2026 Appendix "))
    assert item["status"] in {"draft", "verified"}


def test_ids_unique():
    assert len(IDS) == len(set(IDS))


def test_no_old_unsportsmanlike_term_as_rule():
    # 2026 已取消 unsportsmanlike foul；只允許出現在別名或說明「已取消」的答案裡
    for it in ITEMS:
        if "違反運動道德" in it["answer"] or "unsportsmanlike" in it["answer"]:
            assert "取消" in it["answer"], it["id"]


def test_queries_reference_existing_ids():
    queries = json.loads((store.ROOT / "data" / "test_queries.json").read_text(encoding="utf-8"))
    assert len(queries) >= 10
    assert sum(1 for q in queries if not q["expected"]) >= 2
    for q in queries:
        assert q["query"].strip()
        assert set(q["expected"]) <= set(IDS), q["query"]

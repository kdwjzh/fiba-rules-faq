"""store.py 的測試：用手做的小向量，不呼叫模型。"""
import numpy as np
import pytest

from faq import store

# 4 筆 3 維向量，方向分別接近 x、y、z 與 x+y
VECTORS = store.normalize(np.array([
    [1.0, 0.0, 0.0],
    [0.0, 1.0, 0.0],
    [0.0, 0.0, 1.0],
    [1.0, 1.0, 0.0],
]))


def test_normalize_unit_length():
    v = store.normalize(np.array([[3.0, 4.0, 0.0], [0.0, 0.0, 2.0]]))
    assert np.allclose(np.linalg.norm(v, axis=1), 1.0)


def test_normalize_zero_vector_stays_zero():
    v = store.normalize(np.array([[0.0, 0.0, 0.0]]))
    assert np.allclose(v, 0.0)


def test_cosine():
    assert store.cosine(np.array([1.0, 0.0]), np.array([2.0, 0.0])) == pytest.approx(1.0)
    assert store.cosine(np.array([1.0, 0.0]), np.array([0.0, 3.0])) == pytest.approx(0.0)
    assert store.cosine(np.array([1.0, 1.0]), np.array([1.0, 0.0])) == pytest.approx(2 ** -0.5)


def test_top_k_order():
    hits = store.top_k(np.array([0.9, 0.1, 0.0]), VECTORS, k=3)
    assert [i for i, _ in hits] == [0, 3, 1]
    scores = [s for _, s in hits]
    assert scores == sorted(scores, reverse=True)


def test_top_k_query_not_normalized():
    # 查詢向量長度不影響排序與分數
    a = store.top_k(np.array([0.0, 0.0, 5.0]), VECTORS, k=2)
    b = store.top_k(np.array([0.0, 0.0, 1.0]), VECTORS, k=2)
    assert a[0][0] == 2
    assert a == pytest.approx(b)


def test_top_k_k_larger_than_size():
    assert len(store.top_k(np.array([1.0, 0.0, 0.0]), VECTORS, k=10)) == 4


def test_threshold_accept():
    hits = store.top_k(np.array([1.0, 0.0, 0.0]), VECTORS, k=3)
    assert store.is_answerable(hits, threshold=0.5)


def test_threshold_reject():
    # 跟每筆都差很多（cosine 都 ≤ 0）→ 拒答
    hits = store.top_k(np.array([-1.0, -1.0, -1.0]), VECTORS, k=3)
    assert not store.is_answerable(hits, threshold=0.5)
    assert not store.is_answerable([], threshold=0.5)


def test_doc_text_and_hash():
    item = {"id": "a", "question": "Q", "aliases": ["x", "y"], "answer": "A"}
    assert store.doc_text(item) == "Q\nx、y\nA"
    changed = {**item, "answer": "B"}
    assert store.faq_hash([item]) != store.faq_hash([changed])
    # 不影響 embedding 的欄位（例如 status）不改變 hash
    assert store.faq_hash([item]) == store.faq_hash([{**item, "status": "verified"}])

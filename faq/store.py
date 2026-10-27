"""題庫與向量的純函式：載入題庫、cosine 相似度、top-k、門檻判斷。不可呼叫模型。"""
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
FAQ_PATH = ROOT / "data" / "faq.json"
INDEX_PATH = ROOT / "data" / "index.npz"

THRESHOLD = 0.5  # 最高分低於這個值就拒答；之後用 test_queries.json 調整


def load_faq(path: Path = FAQ_PATH) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_index(path: Path = INDEX_PATH) -> tuple[np.ndarray, list[str], str]:
    """讀 build_index 存的 vectors、ids 與題庫 hash。"""
    with np.load(path) as z:
        return z["vectors"], [str(i) for i in z["ids"]], str(z["faq_hash"])


def doc_text(item: dict) -> str:
    """算 embedding 用的文字：question + aliases + answer。"""
    return "\n".join([item["question"], "、".join(item.get("aliases", [])), item["answer"]])


def faq_hash(items: list[dict]) -> str:
    """只看會影響 embedding 的內容；題庫改了就要重建索引。"""
    text = "\n\n".join(f"{it['id']}\n{doc_text(it)}" for it in items)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize(vectors: np.ndarray) -> np.ndarray:
    """每列除以自己的長度；正規化後內積就是 cosine。"""
    v = np.asarray(vectors, dtype=np.float32)
    norms = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.where(norms == 0, 1, norms)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(normalize(a) @ normalize(b))


def top_k(query_vec: np.ndarray, vectors: np.ndarray, k: int = 3) -> list[tuple[int, float]]:
    """回傳分數最高的 k 筆 (索引, 分數)，由高到低。vectors 需已正規化。"""
    scores = vectors @ normalize(query_vec)
    order = np.argsort(-scores, kind="stable")[:k]
    return [(int(i), float(scores[i])) for i in order]


def is_answerable(hits: list[tuple[int, float]], threshold: float = THRESHOLD) -> bool:
    """最高分達門檻才回答，否則回「題庫沒有相關規則」。"""
    return bool(hits) and hits[0][1] >= threshold

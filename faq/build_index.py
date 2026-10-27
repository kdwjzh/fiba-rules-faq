"""把題庫轉成 embedding，存到 data/index.npz。用法：uv run python -m faq.build_index"""
import time

import numpy as np

from faq import store
from faq.llm import EMBED_MODEL, get_llm


def embed(texts: list[str]) -> np.ndarray:
    """embedding 一律用本地 Ollama；回傳已正規化的向量。"""
    llm = get_llm("local")
    r = llm.client.embeddings.create(model=EMBED_MODEL, input=texts)
    return store.normalize(np.array([d.embedding for d in r.data]))


def main() -> None:
    items = store.load_faq()
    t0 = time.perf_counter()
    vectors = embed([store.doc_text(it) for it in items])
    np.savez(
        store.INDEX_PATH,
        vectors=vectors,
        ids=np.array([it["id"] for it in items]),
        faq_hash=np.array(store.faq_hash(items)),
    )
    sec = time.perf_counter() - t0
    print(f"已建立索引：{len(items)} 題，維度 {vectors.shape[1]}，模型 {EMBED_MODEL}，{sec:.1f} 秒")
    print(f"→ {store.INDEX_PATH.relative_to(store.ROOT)}")


if __name__ == "__main__":
    main()

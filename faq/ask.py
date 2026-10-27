"""命令列查詢。用法：uv run python -m faq.ask "拿球走三步會怎樣" """
import sys

from faq import store
from faq.build_index import embed_query


def search(query: str, k: int = 3) -> list[tuple[dict, float]]:
    """回傳 top-k 的 (題目, 分數)。題庫改過但沒重建索引時提醒。"""
    items = {it["id"]: it for it in store.load_faq()}
    if not store.INDEX_PATH.exists():
        sys.exit("找不到 data/index.npz，請先執行：uv run python -m faq.build_index")
    vectors, ids, saved_hash = store.load_index()
    if saved_hash != store.faq_hash(list(items.values())):
        print("⚠ 題庫已變更，索引是舊的，請重新執行 faq.build_index", file=sys.stderr)
    hits = store.top_k(embed_query(query), vectors, k=k)
    return [(items[ids[i]], score) for i, score in hits if ids[i] in items]


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit('用法：uv run python -m faq.ask "你的問題"')
    query = " ".join(sys.argv[1:])
    results = search(query)
    print(f"問題：{query}\n")
    for rank, (it, score) in enumerate(results, 1):
        print(f"  {rank}. [{score:.3f}] {it['id']}：{it['question']}")
    print()
    if not store.is_answerable([(0, s) for _, s in results]):
        print(f"題庫沒有相關規則（最高分低於門檻 {store.THRESHOLD}）")
        return
    best = results[0][0]
    note = "" if best.get("status") == "verified" else "（草稿，尚未人工核對）"
    print(f"{best['question']}{note}\n{best['answer']}\n出處：{best['source']}")


if __name__ == "__main__":
    main()

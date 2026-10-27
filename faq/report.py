"""跑 data/test_queries.json，輸出作品頁要用的 site/data/results.json 與 site/similarity.png。

用法：uv run python -m faq.report             （只跑檢索，約 10 秒）
      uv run python -m faq.report --answers   （另外跑 answer.py 的結構化回答，約 5–10 分鐘）
"""
import json
import sys
import time
from datetime import datetime, timezone

import numpy as np

from faq import store
from faq.build_index import QUERY_INSTRUCT, embed
from faq.llm import EMBED_MODEL, get_llm

QUERIES_PATH = store.ROOT / "data" / "test_queries.json"
SITE = store.ROOT / "site"


def evaluate(rows: list[dict], threshold: float = store.THRESHOLD) -> dict:
    """rows：每條查詢的 expected 與 top（[(id, 分數), ...]，由高到低）。不呼叫模型。

    - Hit@1／Hit@3 只算題庫內的查詢（expected 不為空），而且不管有沒有被門檻拒答
    - 題庫外拒答：expected 為空的查詢中，最高分低於門檻的比例
    - 題庫內誤拒：expected 不為空、最高分卻低於門檻的數量
    """
    pos = [r for r in rows if r["expected"]]
    neg = [r for r in rows if not r["expected"]]
    hit1 = sum(r["top"][0][0] in r["expected"] for r in pos)
    hit3 = sum(any(i in r["expected"] for i, _ in r["top"][:3]) for r in pos)
    refused = sum(r["top"][0][1] < threshold for r in neg)
    false_refusal = sum(r["top"][0][1] < threshold for r in pos)
    return {
        "in_scope": len(pos),
        "out_of_scope": len(neg),
        "hit1": hit1,
        "hit3": hit3,
        "refused_out_of_scope": refused,
        "false_refusal": false_refusal,
        "threshold": threshold,
    }


def evaluate_answers(answers: list[dict], refusal: str) -> dict:
    """answer.py 的結果：題庫內採用／出處正確／guard 擋下，題庫外是否拒答。不呼叫模型。"""
    pos = [a for a in answers if a["expected"]]
    neg = [a for a in answers if not a["expected"]]
    adopted = [a for a in pos if "guard" not in a and a["answer"] != refusal]
    return {
        "adopted": len(adopted),
        "correct_source": sum(bool(set(a["source_ids"]) & set(a["expected"])) for a in adopted),
        "guard_blocked": sum("guard" in a for a in pos),
        "refused_in_scope": sum("guard" not in a and a["answer"] == refusal for a in pos),
        "refused_out_of_scope": sum("guard" in a or a["answer"] == refusal for a in neg),
        "avg_seconds": round(sum(a["seconds"] for a in answers) / len(answers), 1) if answers else 0,
    }


def pct(n: int, d: int) -> str:
    return f"{n}/{d}（{n / d:.0%}）" if d else "—"


def heatmap(sim: np.ndarray, queries: list[dict], ids: list[str], path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    matplotlib.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "Noto Sans CJK TC", "sans-serif"]
    matplotlib.rcParams["axes.unicode_minus"] = False
    fig, ax = plt.subplots(figsize=(16, 9))
    im = ax.imshow(sim, cmap="Reds", vmin=0.2, vmax=0.9, aspect="auto")
    ax.set_xticks(range(len(ids)), ids, rotation=70, ha="right", fontsize=7)
    labels = [q["query"] if len(q["query"]) <= 14 else q["query"][:13] + "…" for q in queries]
    ax.set_yticks(range(len(queries)), labels, fontsize=8)
    col = {i: j for j, i in enumerate(ids)}
    for r, q in enumerate(queries):  # 期望答案用藍框標出
        for e in q["expected"]:
            ax.add_patch(Rectangle((col[e] - 0.5, r - 0.5), 1, 1, fill=False, ec="#1d4ed8", lw=1.5))
    ax.set_title("測試查詢 × 題庫的 cosine 相似度（藍框＝期望答案）")
    fig.colorbar(im, ax=ax, fraction=0.025, pad=0.01)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def main() -> None:
    with_answers = "--answers" in sys.argv[1:]
    items = {it["id"]: it for it in store.load_faq()}
    vectors, ids, saved_hash = store.load_index()
    if saved_hash != store.faq_hash(list(items.values())):
        sys.exit("題庫已變更，請先執行：uv run python -m faq.build_index")
    queries = json.loads(QUERIES_PATH.read_text(encoding="utf-8"))

    qv = embed([QUERY_INSTRUCT + q["query"] for q in queries])
    sim = qv @ vectors.T
    rows = []
    for q, s in zip(queries, sim):
        order = np.argsort(-s, kind="stable")[:3]
        rows.append({"query": q["query"], "expected": q["expected"],
                     "top": [(ids[i], round(float(s[i]), 3)) for i in order]})
    m = evaluate(rows)

    answers = []
    if with_answers:
        from faq.answer import REFUSAL, GuardError, answer

        for q in queries:
            t0 = time.perf_counter()
            try:
                a, _ = answer(q["query"])
                rec = {"answer": a.answer, "source_ids": a.source_ids, "confidence": a.confidence}
            except GuardError as e:
                rec = {"guard": str(e)}
            answers.append({"query": q["query"], "expected": q["expected"],
                            "seconds": round(time.perf_counter() - t0, 1), **rec})
            print(f"  {answers[-1]['seconds']:5.1f}s {q['query']}")

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "models": {"embedding": EMBED_MODEL, "answer": get_llm("local").model},
        "faq_count": len(items),
        # 作品頁直接把 metrics 畫成表格，所以用給人看的字串
        "metrics": {
            "題庫題數": len(items),
            "測試查詢": f"{len(queries)} 條（題庫內 {m['in_scope']}、題庫外 {m['out_of_scope']}）",
            "Hit@1": pct(m["hit1"], m["in_scope"]),
            "Hit@3": pct(m["hit3"], m["in_scope"]),
            "題庫外拒答": pct(m["refused_out_of_scope"], m["out_of_scope"]),
            "題庫內誤拒": pct(m["false_refusal"], m["in_scope"]),
            "拒答門檻": m["threshold"],
        },
        "counts": m,
        "answer_counts": evaluate_answers(answers, REFUSAL) if answers else None,
        "queries": rows,
        "answers": answers,
    }
    if answers:
        a = result["answer_counts"]
        result["metrics"].update({
            "模型回答（題庫內）": f"採用 {a['adopted']}（出處正確 {a['correct_source']}）、"
                                f"guard 擋下 {a['guard_blocked']}、拒答 {a['refused_in_scope']}",
            "模型回答（題庫外拒答）": pct(a["refused_out_of_scope"], m["out_of_scope"]),
            "模型回答平均秒數": a["avg_seconds"],
        })
    (SITE / "data").mkdir(parents=True, exist_ok=True)
    out = SITE / "data" / "results.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    heatmap(sim, queries, ids, SITE / "similarity.png")
    for k, v in result["metrics"].items():
        print(f"{k}：{v}")
    print(f"→ {out.relative_to(store.ROOT)}、site/similarity.png")


if __name__ == "__main__":
    main()

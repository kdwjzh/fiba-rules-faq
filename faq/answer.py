"""加強版：根據 top-3 的 FAQ，用結構化輸出產生回答。用法：uv run python -m faq.answer "拿球走三步會怎樣" """
import re
import sys
from typing import Literal

from pydantic import BaseModel, Field

from faq import store
from faq.ask import search
from faq.llm import get_llm

# 拒答交給檢索門檻決定：讓 qwen3:1.7b 自己拒答時，22 條題庫內查詢有 9–12 條被誤拒
SYSTEM = (
    "你是 FIBA 2026 籃球規則的查詢助手。下面 3 條 FAQ 是用相似度從題庫找出來、跟問題最接近的條目；"
    "使用者的問法很口語，字眼通常跟 FAQ 不同，請想想問題在問哪一條規則。"
    "從中選出最能回答問題的條目（1–2 條），只根據它們、用繁體中文、100 字以內回答，不可使用 FAQ 以外的知識或 NBA 規則。"
    "answer 只寫回答內容，不要寫 id。confidence：條目明確回答了問題填「高」，部分相關填「中」，都不太相關填「低」。"
)
REFUSAL = "題庫沒有相關規則"
MAX_CHARS = 100


class RuleAnswer(BaseModel):
    answer: str = Field(description="100 字內，只根據提供的 FAQ")
    source_ids: list[str] = Field(description="用到的 FAQ id，只能是提供的 id")
    confidence: Literal["高", "中", "低"]


class GuardError(ValueError):
    """模型輸出不符合規定（例如引用了 top-3 以外的 id）。"""


def guard(ans: RuleAnswer, allowed_ids: list[str]) -> RuleAnswer:
    """程式端檢查：source_ids 必須是 top-3 的子集；回答了就要附出處；不可超過 100 字。不呼叫模型。
    信心「低」時改成拒答。"""
    extra = [i for i in ans.source_ids if i not in allowed_ids]
    if extra:
        raise GuardError(f"引用了不在 top-3 的 id：{extra}")
    if ans.answer.strip() == REFUSAL or ans.confidence == "低":
        return RuleAnswer(answer=REFUSAL, source_ids=[], confidence="低")
    if not ans.source_ids:
        raise GuardError("有回答但沒有附出處")
    if len(ans.answer) > MAX_CHARS:  # 試跑時有幾次把整段 FAQ 原文貼進 answer
        raise GuardError(f"回答 {len(ans.answer)} 字，超過 {MAX_CHARS} 字")
    rest = ans.answer.lower()
    for i in allowed_ids:
        rest = rest.replace(i.lower(), "")
    if len(re.sub(r"[\W_]", "", rest)) < 5:  # 試跑時有幾次 answer 只寫了 id 本身
        raise GuardError("回答只有 id，沒有內容")
    return ans


def build_prompt(query: str, items: list[dict]) -> str:
    # 第一次試跑時模型把「id: travelling」整段抄進 source_ids，所以另外列出可用的 id
    faq = "\n\n".join(
        f"{it['id']}（{it['source']}）\n問：{it['question']}\n答：{it['answer']}" for it in items
    )
    ids = "、".join(it["id"] for it in items)
    return f"FAQ 條目：\n{faq}\n\nsource_ids 只能從這些 id 選：{ids}\n\n使用者問題：{query}"


def answer(query: str, profile: str | None = None) -> tuple[RuleAnswer, list[tuple[dict, float]]]:
    results = search(query)
    if not store.is_answerable([(0, s) for _, s in results]):
        return RuleAnswer(answer=REFUSAL, source_ids=[], confidence="低"), results
    items = [it for it, _ in results]
    llm = get_llm(profile)
    r = llm.client.chat.completions.parse(
        model=llm.model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": build_prompt(query, items)},
        ],
        response_format=RuleAnswer,
        temperature=0,
    )
    return guard(r.choices[0].message.parsed, [it["id"] for it in items]), results


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit('用法：uv run python -m faq.answer "你的問題"')
    query = " ".join(sys.argv[1:])
    try:
        ans, results = answer(query)
    except GuardError as e:
        # 模型回答不採用，改給檢索第 1 名的題庫答案（人工審核過的文字）
        best = search(query)[0][0]
        print(f"問題：{query}\n（模型回答沒通過檢查，不採用：{e}）\n")
        print(f"{best['answer']}\n出處：{best['id']}（{best['source']}）")
        return
    print(f"問題：{query}")
    print(f"檢索：{'、'.join(f'{it['id']} {s:.3f}' for it, s in results)}\n")
    print(ans.answer)
    sources = {it["id"]: it["source"] for it, _ in results}
    if ans.source_ids:
        print(f"出處：{'、'.join(f'{i}（{sources[i]}）' for i in ans.source_ids)}")
    print(f"信心：{ans.confidence}")


if __name__ == "__main__":
    main()

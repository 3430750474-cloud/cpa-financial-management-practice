"""Recalculate selected numeric families from what learners can actually read."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path


DATA = Path(__file__).resolve().parents[1] / "dist" / "data"


def values(stem: str, pattern: str) -> tuple[float, ...]:
    match = re.search(pattern, stem)
    if not match:
        raise ValueError(f"Cannot parse visible inputs: {stem}")
    return tuple(float(value.replace(",", "")) for value in match.groups())


def visible_result(question: dict) -> float:
    stem, topic = question["stem"], question["topic"]
    if topic == "货币时间价值—复利终值":
        principal, rate, years = values(stem, r"存入银行([\d,]+)万元，年利率为([\d.]+)%.*?([\d.]+)年后")
        return principal * (1 + rate / 100) ** years
    if topic == "投资项目资本预算—净现值":
        investment, cash_flow, rate = values(stem, r"初始投资([\d.]+)万元.*?现金净流量([\d.]+)万元，折现率([\d.]+)%")
        return -investment + sum(cash_flow / (1 + rate / 100) ** year for year in (1, 2, 3))
    if topic == "期权价值评估—单期二叉树看涨期权":
        spot, strike, rise, fall, rate = values(stem, r"股票现价([\d.]+)元、执行价格([\d.]+)元.*?上行([\d.]+)%或下行([\d.]+)%.*?无风险利率为([\d.]+)%")
        up, down, growth = 1 + rise / 100, 1 - fall / 100, 1 + rate / 100
        p = (growth - down) / (up - down)
        return (p * max(spot * up - strike, 0) + (1 - p) * max(spot * down - strike, 0)) / growth
    if topic == "企业价值评估—股权现金流量折现模型":
        cash_flow, growth, required = values(stem, r"下一年股权现金流量为([\d.]+)万元，此后按([\d.]+)%永续增长，股权资本成本为([\d.]+)%")
        return cash_flow / ((required - growth) / 100)
    if topic == "长期筹资—债券价值评估":
        face, coupon, years, yield_rate = values(stem, r"面值([\d,]+)元、票面利率([\d.]+)%.*?期限([\d.]+)年的债券，市场必要报酬率为([\d.]+)%")
        return sum(face * coupon / 100 / (1 + yield_rate / 100) ** year for year in range(1, int(years) + 1)) + face / (1 + yield_rate / 100) ** years
    raise ValueError(f"Unsupported topic: {topic}")


from verify_ch09 import manual_ch09_visible


def main() -> None:
    wanted = {"货币时间价值—复利终值", "投资项目资本预算—净现值", "期权价值评估—单期二叉树看涨期权", "企业价值评估—股权现金流量折现模型"}
    checked = {topic: 0 for topic in wanted}
    manual_ch09_checked = 0
    for chapter in (3, 5, 6, 7, 9):
        questions = json.loads((DATA / f"chapter-{chapter:02d}.json").read_text(encoding="utf-8"))["questions"]
        for q in questions:
            if q["type"] != "calculation" or q["topic"] not in wanted:
                continue
            answer = visible_result(q)
            if abs(answer - q["numericAnswer"]) > .011:
                raise AssertionError(f"{q['id']}: visible inputs yield {answer:.2f}; stored answer {q['numericAnswer']:.2f}")
            checked[q["topic"]] += 1
    chapter9 = json.loads((DATA / "chapter-09.json").read_text(encoding="utf-8"))["questions"]
    for q in chapter9:
        if q.get("authoringMethod") != "manual" or q["type"] != "calculation":
            continue
        answer = manual_ch09_visible(q)
        if abs(answer - q["numericAnswer"]) > .011:
            raise AssertionError(f"{q['id']}: visible inputs yield {answer:.2f}; stored answer {q['numericAnswer']:.2f}")
        manual_ch09_checked += 1
    if not all(checked.values()):
        raise AssertionError(f"Missing formula family: {checked}")
    if manual_ch09_checked != 15:
        raise AssertionError(f"Chapter 9 manual calculations checked: {manual_ch09_checked}, expected 15")
    print(f"Recalculated {sum(checked.values())} displayed calculations plus {manual_ch09_checked} hand-authored chapter 9 items from visible stem inputs")


if __name__ == "__main__":
    main()

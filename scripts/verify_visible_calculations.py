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
from verify_ch19 import visible_ch19
from verify_ch20 import visible_ch20, visible_case20
from verify_ch02 import visible_ch02, visible_case02
from verify_ch13 import visible_ch13
from verify_ch15 import visible_ch15
from verify_ch10 import visible_ch10
from verify_ch03 import visible_ch03
from verify_ch06 import visible_ch06
from verify_ch11 import visible_ch11, visible_case11
from verify_ch04 import visible_ch04
from verify_ch05 import visible_ch05, visible_case05


def main() -> None:
    wanted = {"企业价值评估—股权现金流量折现模型"}
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
    chapter2 = json.loads((DATA / "chapter-02.json").read_text(encoding="utf-8"))["questions"]
    authored2 = [q for q in chapter2 if q.get("authoringMethod") == "manual" and q["type"] == "calculation"]
    if len(authored2) != 22:
        raise AssertionError(f"Chapter 2 manual calculations found: {len(authored2)}, expected 22")
    for q in authored2:
        if abs(visible_ch02(q) - q["numericAnswer"]) > .011:
            raise AssertionError(f"{q['id']} differs from visible calculation")
    cases2 = [q for q in chapter2 if q.get("authoringMethod") == "manual" and q["type"] == "case"]
    if len(cases2) != 8:
        raise AssertionError(f"Chapter 2 manual cases found: {len(cases2)}, expected 8")
    for q in cases2:
        expected = visible_case02(q)
        if len(expected) != len(q["questions"]):
            raise AssertionError(f"{q['id']} case question count mismatch")
        for subquestion, actual in zip(q["questions"], expected):
            if abs(actual - subquestion["numericAnswer"]) > .011:
                raise AssertionError(f"{q['id']} case answer differs from visible calculation")
    chapter3 = json.loads((DATA / "chapter-03.json").read_text(encoding="utf-8"))["questions"]
    authored3 = [q for q in chapter3 if q.get("authoringMethod") == "manual" and q["type"] == "calculation"]
    if len(authored3) != 18:
        raise AssertionError(f"Chapter 3 manual calculations found: {len(authored3)}, expected 18")
    for q in authored3:
        if abs(visible_ch03(q) - q["numericAnswer"]) > .011:
            raise AssertionError(f"{q['id']} differs from visible calculation")
    chapter4 = json.loads((DATA / "chapter-04.json").read_text(encoding="utf-8"))["questions"]
    authored4 = [q for q in chapter4 if q.get("authoringMethod") == "manual" and q["type"] == "calculation"]
    if len(authored4) != 10:
        raise AssertionError(f"Chapter 4 manual calculations found: {len(authored4)}, expected 10")
    for q in authored4:
        if abs(visible_ch04(q) - q["numericAnswer"]) > .011:
            raise AssertionError(f"{q['id']} differs from visible calculation")
    chapter5 = json.loads((DATA / "chapter-05.json").read_text(encoding="utf-8"))["questions"]
    authored5 = [q for q in chapter5 if q.get("authoringMethod") == "manual" and q["type"] == "calculation"]
    cases5 = [q for q in chapter5 if q.get("authoringMethod") == "manual" and q["type"] == "case"]
    if len(authored5) != 8 or len(cases5) != 8:
        raise AssertionError(f"Chapter 5 authored counts: {len(authored5)} calculations, {len(cases5)} cases")
    for q in authored5:
        if abs(visible_ch05(q)-q["numericAnswer"]) > .011:
            raise AssertionError(f"{q['id']} differs from visible calculation")
    for q in cases5:
        expected = visible_case05(q)
        if len(expected) != len(q["questions"]):
            raise AssertionError(f"{q['id']} case question count mismatch")
        for subquestion, actual in zip(q["questions"], expected):
            if abs(actual-subquestion["numericAnswer"]) > .011:
                raise AssertionError(f"{q['id']} case answer differs from visible calculation")
    chapter6 = json.loads((DATA / "chapter-06.json").read_text(encoding="utf-8"))["questions"]
    authored6 = [q for q in chapter6 if q.get("authoringMethod") == "manual" and q["type"] == "calculation"]
    if len(authored6) != 17:
        raise AssertionError(f"Chapter 6 manual calculations found: {len(authored6)}, expected 17")
    for q in authored6:
        if abs(visible_ch06(q) - q["numericAnswer"]) > .011:
            raise AssertionError(f"{q['id']} differs from visible calculation")
    chapter9 = json.loads((DATA / "chapter-09.json").read_text(encoding="utf-8"))["questions"]
    for q in chapter9:
        if q.get("authoringMethod") != "manual" or q["type"] != "calculation":
            continue
        answer = manual_ch09_visible(q)
        if abs(answer - q["numericAnswer"]) > .011:
            raise AssertionError(f"{q['id']}: visible inputs yield {answer:.2f}; stored answer {q['numericAnswer']:.2f}")
        manual_ch09_checked += 1
    chapter10 = json.loads((DATA / "chapter-10.json").read_text(encoding="utf-8"))["questions"]
    authored10 = [q for q in chapter10 if q.get("authoringMethod") == "manual" and q["type"] == "calculation"]
    if len(authored10) != 11:
        raise AssertionError(f"Chapter 10 manual calculations found: {len(authored10)}, expected 11")
    for q in authored10:
        if abs(visible_ch10(q) - q["numericAnswer"]) > .011:
            raise AssertionError(f"{q['id']} differs from visible calculation")
    chapter11 = json.loads((DATA / "chapter-11.json").read_text(encoding="utf-8"))["questions"]
    authored11 = [q for q in chapter11 if q.get("authoringMethod") == "manual" and q["type"] == "calculation"]
    cases11 = [q for q in chapter11 if q.get("authoringMethod") == "manual" and q["type"] == "case"]
    if len(authored11) != 16 or len(cases11) != 8:
        raise AssertionError(f"Chapter 11 authored counts: {len(authored11)} calculations, {len(cases11)} cases")
    for q in authored11:
        if abs(visible_ch11(q)-q["numericAnswer"]) > .011:
            raise AssertionError(f"{q['id']} differs from visible calculation")
    for q in cases11:
        expected = visible_case11(q)
        if len(expected) != len(q["questions"]):
            raise AssertionError(f"{q['id']} case question count mismatch")
        for subquestion, actual in zip(q["questions"], expected):
            if actual is not None and abs(actual-subquestion["numericAnswer"]) > .011:
                raise AssertionError(f"{q['id']} case answer differs from visible calculation")
    chapter13 = json.loads((DATA / "chapter-13.json").read_text(encoding="utf-8"))["questions"]
    authored13 = [q for q in chapter13 if q.get("authoringMethod") == "manual" and q["type"] == "calculation"]
    if len(authored13) != 13:
        raise AssertionError(f"Chapter 13 manual calculations found: {len(authored13)}, expected 13")
    for q in authored13:
        if abs(visible_ch13(q) - q["numericAnswer"]) > .011:
            raise AssertionError(f"{q['id']} differs from visible calculation")
    chapter15 = json.loads((DATA / "chapter-15.json").read_text(encoding="utf-8"))["questions"]
    authored15 = [q for q in chapter15 if q.get("authoringMethod") == "manual" and q["type"] == "calculation"]
    if len(authored15) != 12:
        raise AssertionError(f"Chapter 15 manual calculations found: {len(authored15)}, expected 12")
    for q in authored15:
        if abs(visible_ch15(q) - q["numericAnswer"]) > .011:
            raise AssertionError(f"{q['id']} differs from visible calculation")
    if not all(checked.values()):
        raise AssertionError(f"Missing formula family: {checked}")
    if manual_ch09_checked != 15:
        raise AssertionError(f"Chapter 9 manual calculations checked: {manual_ch09_checked}, expected 15")
    chapter19 = json.loads((DATA / "chapter-19.json").read_text(encoding="utf-8"))["questions"]
    authored19 = [q for q in chapter19 if q.get("authoringMethod") == "manual" and q["type"] == "calculation"]
    if len(authored19) != 20:
        raise AssertionError(f"Chapter 19 manual calculations found: {len(authored19)}, expected 20")
    for q in authored19:
        answer = visible_ch19(q)
        if abs(answer - q["numericAnswer"]) > .011:
            raise AssertionError(f"{q['id']}: visible inputs yield {answer:.2f}; stored answer {q['numericAnswer']:.2f}")
    chapter20 = json.loads((DATA / "chapter-20.json").read_text(encoding="utf-8"))["questions"]
    authored20 = [q for q in chapter20 if q.get("authoringMethod") == "manual" and q["type"] == "calculation"]
    cases20 = [q for q in chapter20 if q.get("authoringMethod") == "manual" and q["type"] == "case"]
    if len(authored20) != 15 or len(cases20) != 8:
        raise AssertionError(f"Chapter 20 authored counts: {len(authored20)} calculations, {len(cases20)} cases")
    for q in authored20:
        if abs(visible_ch20(q) - q["numericAnswer"]) > .011:
            raise AssertionError(f"{q['id']} differs from visible calculation")
    for q in cases20:
        expected = visible_case20(q)
        if len(expected) != len(q["questions"]):
            raise AssertionError(f"{q['id']} case question count mismatch")
        for subquestion, actual in zip(q["questions"], expected):
            if actual is not None and abs(actual - subquestion["numericAnswer"]) > .011:
                raise AssertionError(f"{q['id']} case answer differs from visible calculation")
    print(f"Recalculated {sum(checked.values())} legacy calculations, {len(authored2)} chapter 2, {len(authored3)} chapter 3, {len(authored4)} chapter 4, {len(authored5)} chapter 5, {len(authored6)} chapter 6, {manual_ch09_checked} chapter 9, {len(authored10)} chapter 10, {len(authored11)} chapter 11, {len(authored13)} chapter 13, {len(authored15)} chapter 15, {len(authored19)} chapter 19, {len(authored20)} chapter 20 calculations, and {len(cases2)+len(cases5)+len(cases11)+len(cases20)} cases")


if __name__ == "__main__":
    main()

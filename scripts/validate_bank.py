from __future__ import annotations

import json
import math
import re
import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "dist" / "data"
manifest = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
errors: list[str] = []
ids: set[str] = set()
stems: Counter[str] = Counter()
near_groups: dict[tuple[str, str, str], list[dict]] = {}
all_q: list[dict] = []
if manifest.get("total") != 15000:
    errors.append(f"manifest total={manifest.get('total')}, expected 15000")
if len(manifest.get("chapters", [])) != 20:
    errors.append(f"chapter count={len(manifest.get('chapters', []))}, expected 20")

for ch in manifest["chapters"]:
    path = DATA / ch["file"]
    if not path.exists():
        errors.append(f"missing chapter file {path.name}")
        continue
    bank = json.loads(path.read_text(encoding="utf-8"))["questions"]
    if len(bank) != ch["count"]:
        errors.append(f"{ch['id']} expected {ch['count']} questions, got {len(bank)}")
    if len(bank) < 100:
        errors.append(f"{ch['id']} below minimum 100")
    for q in bank:
        all_q.append(q)
        for key in ("id", "chapterId", "chapterTitle", "topic", "type", "difficulty", "sourceType", "source", "explanation", "tags"):
            if not q.get(key):
                errors.append(f"{q.get('id','?')} missing {key}")
        if q.get("abilityLevel") not in {1, 2, 3}:
            errors.append(f"{q.get('id','?')} missing or invalid abilityLevel")
        if q.get("id") in ids:
            errors.append(f"duplicate id {q.get('id')}")
        ids.add(q.get("id"))
        text = q.get("stem") or q.get("material") or ""
        stems[re.sub(r"\s+", "", text)] += 1
        skeleton = re.sub(r"\d+(?:[,.，．]\d+)*(?:%|％)?", "<N>", text)
        skeleton = re.sub(r"[甲乙丙丁]公司|某公司|某企业|某产品", "<CO>", skeleton)
        skeleton = re.sub(r"[\s，。；：、！？（）()“”‘’\-—×÷=+/%]", "", skeleton)
        if len(skeleton) >= 28:
            near_groups.setdefault((q["chapterId"], q["type"], skeleton), []).append(q)
        if q.get("sourceType") not in {"textbook-example", "past-exam", "original"}:
            errors.append(f"{q['id']} unknown sourceType")
        if q["type"] in {"single", "multiple"}:
            stem = (q.get("stem") or "").strip()
            compact_stem = re.sub(r"\s+", "", stem)
            if not compact_stem:
                errors.append(f"{q['id']} choice question has no stem")
            elif len(compact_stem) < 10:
                errors.append(f"{q['id']} choice question stem is too short: {stem!r}")
            if stem.endswith((":", "：")):
                errors.append(f"{q['id']} choice question ends before its question: {stem!r}")
            options = q.get("options", [])
            if len(options) != 4:
                errors.append(f"{q['id']} choice question has {len(options)} options")
            keys = {x.get("key") for x in options}
            if keys != {"A", "B", "C", "D"}:
                errors.append(f"{q['id']} choices must have exactly A/B/C/D keys")
            if any(not (x.get("text") or "").strip() for x in options):
                errors.append(f"{q['id']} has an empty option")
            answers = q.get("answer", [])
            if not answers or not set(answers).issubset(keys):
                errors.append(f"{q['id']} invalid choice answer")
            if q["type"] == "single" and len(answers) != 1:
                errors.append(f"{q['id']} single answer count is {len(answers)}")
            if q["type"] == "multiple" and len(answers) < 2:
                errors.append(f"{q['id']} multiple answer count is {len(answers)}")
            if len({re.sub(r"\s+", "", x.get("text", "")).casefold() for x in options}) != len(options):
                errors.append(f"{q['id']} duplicate option text")
        elif q["type"] == "calculation":
            stem = (q.get("stem") or "").strip()
            if len(re.sub(r"\s+", "", stem)) < 10:
                errors.append(f"{q['id']} calculation question has no complete stem")
            if stem.endswith((":", "：")):
                errors.append(f"{q['id']} calculation question ends before its ask: {stem!r}")
            if not isinstance(q.get("numericAnswer"), (int, float)) or not math.isfinite(q["numericAnswer"]):
                errors.append(f"{q['id']} invalid numericAnswer")
            if not q.get("unit"):
                errors.append(f"{q['id']} missing calculation unit")
            rendered = q.get("explanation", "").replace(",", "")
            answer = q.get("numericAnswer")
            answer_visible = isinstance(answer, (int, float)) and (f"{answer:.2f}" in rendered or (float(answer).is_integer() and str(int(answer)) in rendered))
            if not answer_visible:
                errors.append(f"{q['id']} numeric answer is not shown in its calculation steps")
            final_values = re.findall(r"=\s*(-?[\d,]+(?:\.\d+)?)", rendered)
            if final_values:
                final_value = float(final_values[-1].replace(",", ""))
                if abs(final_value - float(answer)) > 0.011:
                    errors.append(f"{q['id']} final calculation step {final_value} differs from numericAnswer {answer}")
        elif q["type"] == "case":
            material = (q.get("material") or "").strip()
            if len(material) < 20:
                errors.append(f"{q['id']} case material is missing or too short")
            subquestions = q.get("questions", [])
            if len(subquestions) < 2:
                errors.append(f"{q['id']} case has fewer than two subquestions")
            for index, sub in enumerate(subquestions, 1):
                if len((sub.get("prompt") or "").strip()) < 8:
                    errors.append(f"{q['id']} case subquestion {index} has no complete prompt")
                if not (sub.get("answer") or "").strip():
                    errors.append(f"{q['id']} case subquestion {index} is missing its answer")
                if not sub.get("points"):
                    errors.append(f"{q['id']} case subquestion {index} is missing scoring points")
                value = sub.get("numericAnswer")
                rendered = " ".join(sub.get("points", [])).replace(",", "")
                answer_visible = value is None or f"{value:.2f}" in rendered or (float(value).is_integer() and str(int(value)) in rendered)
                if not answer_visible:
                    errors.append(f"{q['id']} case numeric answer is not shown in scoring points")
        else:
            errors.append(f"{q['id']} invalid question type {q['type']}")
        if q["sourceType"] == "past-exam" and not q.get("year"):
            errors.append(f"{q['id']} past exam missing year")
        if q["sourceType"] != "original" and not q.get("page"):
            # The PDF extraction may not expose text for every layout; the source file is still traceable.
            if not q.get("source"):
                errors.append(f"{q['id']} source question lacks traceable reference")

if len(all_q) != 15000:
    errors.append(f"loaded total={len(all_q)}, expected 15000")
dups = [(s, n) for s, n in stems.items() if n > 1]
if dups:
    errors.append(f"duplicate stems={len(dups)}; first={dups[:3]}")
near_candidates = [(key, group) for key, group in near_groups.items() if len(group) > 1]
near_review = ROOT / "review" / "near-duplicate-candidates.csv"
near_review.parent.mkdir(parents=True, exist_ok=True)
with near_review.open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.writer(stream)
    writer.writerow(["章节", "题型", "候选数量", "题目ID", "代表题干（已遮蔽数字）", "复核状态"])
    for (chapter_id, qtype, skeleton), group in sorted(near_candidates, key=lambda x: (-len(x[1]), x[0][0])):
        writer.writerow([chapter_id, qtype, len(group), "、".join(q["id"] for q in group), skeleton[:500], "待逐项审阅；数字/公司名变体保留为候选"])
review = ROOT / "review" / "cpa-financial-management-question-review.xlsx"
if not review.exists() or review.stat().st_size < 100_000:
    errors.append("review workbook missing or unexpectedly small")

source_counts = Counter(q["sourceType"] for q in all_q)
type_counts = Counter(q["type"] for q in all_q)
if errors:
    print("\n".join(errors[:80]))
    print(f"Total errors: {len(errors)}")
    raise SystemExit(1)
levels = Counter(q["abilityLevel"] for q in all_q)
print(f"Validated {len(all_q)} questions across 20 chapters; sources={dict(source_counts)}; types={dict(type_counts)}; abilityLevels={dict(levels)}; nearDuplicateGroups={len(near_candidates)}; nearReview={near_review.name}; workbook={review.stat().st_size:,} bytes")

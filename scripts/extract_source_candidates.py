"""Build a private, review-only index of headed source questions.

No candidate is added to the public bank by this script. Paragraph numbers refer
to the flattened Word body, not PDF pages; all candidates require human review.
"""
from __future__ import annotations

import argparse
import json
import re
import tempfile
import zipfile
from collections import Counter
from pathlib import Path

from build_bank import WORD_ARCHIVE, docx_paragraphs

HEADING = re.compile(r"例题[·.]|经典真题|(?:19|20)\d{2}年.{0,20}(?:单选题|多选题|计算分析题)")
OPTION = re.compile(r"(?:^|[\s　])([A-D])[.．、](?=\s*\S)")
ANSWER = re.compile(r"^【答案】\s*([A-D](?:\s*[,，、\s]?\s*[A-D])*)(?=\s|$|[。；;])")


def candidates(paragraphs: list[str], chapter: str, source: str) -> list[dict]:
    result = []
    for index, paragraph in enumerate(paragraphs):
        if not paragraph.startswith("【答案】"):
            continue
        previous = next((i for i in range(index - 1, -1, -1)
                         if paragraphs[i].startswith("【答案】")), -1)
        start = next((i for i in range(index - 1, previous, -1)
                      if HEADING.search(paragraphs[i])), None)
        if start is None:
            continue
        block = paragraphs[start:index]
        options = []
        stem = []
        for line in block:
            matches = list(OPTION.finditer(line))
            if not matches:
                if not options:
                    stem.append(line)
                else:
                    options[-1][1] += " " + line
                continue
            if line[:matches[0].start()].strip():
                prefix = line[:matches[0].start()].strip()
                if options:
                    options[-1][1] += " " + prefix
                else:
                    stem.append(prefix)
            for pos, match in enumerate(matches):
                end = matches[pos + 1].start() if pos + 1 < len(matches) else len(line)
                options.append([match.group(1), line[match.end():end].strip()])
        answer_match = ANSWER.match(paragraph)
        answer = re.findall(r"[A-D]", answer_match.group(1)) if answer_match else []
        labels = [item[0] for item in options]
        flags = []
        if labels != ["A", "B", "C", "D"]:
            flags.append("选项不完整或顺序异常")
        if not answer or len(set(answer)) != len(answer) or not set(answer) <= set(labels):
            flags.append("答案未可靠识别")
        kind = "multiple" if "多选题" in paragraphs[start] else "single" if "单选题" in paragraphs[start] else "other"
        if (kind == "single" and len(answer) != 1) or (kind == "multiple" and len(answer) < 2):
            flags.append("题型与答案数量不符")
        explanation = []
        for line in paragraphs[index + 1:]:
            if HEADING.search(line) or line.startswith("【答案】"):
                break
            if len(explanation) >= 8:
                break
            explanation.append(line)
        if not explanation or not explanation[0].startswith("【解析】"):
            flags.append("解析边界需核查")
        if any("|" in line or "如下表" in line for line in stem):
            flags.append("表格需核查原文")
        result.append({"chapter": chapter, "source": source, "paragraphStart": start + 1,
                       "paragraphAnswer": index + 1, "kind": kind, "stem": stem,
                       "options": options, "answer": answer, "followingParagraphs": explanation,
                       "flags": flags, "reviewStatus": "未人工审核"})
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(tempfile.gettempdir()) / "cpa-financial-source-candidates.json")
    args = parser.parse_args()
    rows = []
    with zipfile.ZipFile(WORD_ARCHIVE) as archive:
        for name in archive.namelist():
            match = re.match(r"(\d{2}).*\.docx$", name, re.I)
            if match and 1 <= int(match.group(1)) <= 20:
                rows.extend(candidates(docx_paragraphs(archive.read(name)), match.group(1), name))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "candidates": len(rows),
                      "chapters": len(set(row["chapter"] for row in rows)),
                      "withoutAutomaticFlags": sum(not row["flags"] for row in rows),
                      "flags": Counter(flag for row in rows for flag in row["flags"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()

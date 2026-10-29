from __future__ import annotations

import io
import json
import math
import random
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
INPUT = Path(r"C:\Users\Cr\Desktop\轻1·基础细讲班-闫华红")
WORD_ARCHIVE = INPUT / "轻1·基础细讲班-闫华红(笔记版word)(Word笔记版).zip"
PDF_ARCHIVE = INPUT / "轻1·基础细讲班-闫华红(笔记版pdf)(PDF笔记版).zip"
OUT = ROOT / "dist" / "data"
REVIEW = ROOT / "review"
NAMESPACE = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
CN_NUMBERS = "一二三四五六七八九十百"


def docx_paragraphs(data: bytes) -> list[str]:
    with zipfile.ZipFile(io.BytesIO(data)) as docx:
        root = ET.fromstring(docx.read("word/document.xml"))
    result: list[str] = []
    for block in root.findall(".//w:body/*", NAMESPACE):
        if block.tag.endswith("}p"):
            value = "".join(t.text or "" for t in block.findall(".//w:t", NAMESPACE)).strip()
            if value:
                result.append(value)
        elif block.tag.endswith("}tbl"):
            for row in block.findall(".//w:tr", NAMESPACE):
                cells = ["".join(t.text or "" for t in cell.findall(".//w:t", NAMESPACE)).strip()
                         for cell in row.findall("./w:tc", NAMESPACE)]
                if any(cells):
                    result.append(" | ".join(cells))
    return result


def normalize(text: str) -> str:
    return re.sub(r"\s+", "", text).replace("　", "")


def find_title(paragraphs: list[str], chapter: int) -> str:
    pat = re.compile(rf"第\s*{chapter_to_chinese(chapter)}\s*章\s*[　\s]*([^\n|]+)")
    for text in paragraphs[:80]:
        m = pat.search(text)
        if m:
            candidate = m.group(1).strip(" ：:|")
            if candidate and not candidate.startswith(("（", "(", "—")):
                return f"第{chapter}章 {candidate[:40]}"
        row = re.search(rf"第{chapter_to_chinese(chapter)}章\s*\|\s*([^|]+)", text)
        if row and not row.group(1).lstrip().startswith(("（", "(")):
            return f"第{chapter}章 {row.group(1).strip()[:40]}"
    return f"第{chapter}章"


def chapter_to_chinese(n: int) -> str:
    nums = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九"]
    if n < 10:
        return nums[n]
    if n == 10:
        return "十"
    if n < 20:
        return "十" + nums[n % 10]
    return "二十" if n == 20 else "二十" + nums[n % 10]


def extract_pdf_page_map() -> dict[str, list[tuple[int, str]]]:
    """Index PDF page text for citation checks. No PDF text is copied into the public app."""
    try:
        from pypdf import PdfReader
    except Exception:
        return {}
    pages: dict[str, list[tuple[int, str]]] = {}
    if not PDF_ARCHIVE.exists():
        return pages
    with zipfile.ZipFile(PDF_ARCHIVE) as archive:
        pdf_names = [n for n in archive.namelist() if n.lower().endswith(".pdf")]
        for name in pdf_names:
            m = re.match(r"(\d{2})", name)
            if not m:
                continue
            chapter = m.group(1)
            try:
                reader = PdfReader(io.BytesIO(archive.read(name)))
                pages[chapter] = [(i + 1, normalize(page.extract_text() or ""))
                                  for i, page in enumerate(reader.pages)]
            except Exception:
                pages[chapter] = []
    return pages


def find_pdf_page(chapter: str, phrase: str, pages: dict[str, list[tuple[int, str]]]) -> int | None:
    needle = normalize(phrase)[:24]
    if len(needle) < 8:
        return None
    for number, text in pages.get(chapter, []):
        if needle in text:
            return number
    return None


def parse_source() -> tuple[list[dict], dict[str, list[dict]]]:
    if not WORD_ARCHIVE.exists():
        raise FileNotFoundError(f"未找到 Word 笔记版：{WORD_ARCHIVE}")
    pdf_pages = extract_pdf_page_map()
    chapters: dict[str, list[dict]] = {}
    with zipfile.ZipFile(WORD_ARCHIVE) as archive:
        entries = [n for n in archive.namelist() if n.lower().endswith(".docx")]
        for name in entries:
            m = re.match(r"(\d{2})", name)
            if not m:
                continue
            chapter_id = m.group(1)
            chapter_num = int(chapter_id)
            all_paras = docx_paragraphs(archive.read(name))
            title = find_title(all_paras, chapter_num)
            paras = all_paras
            if chapter_num == 1:
                # The first Word file includes a long preface, syllabus analysis and all-chapter tables.
                # Start chapter evidence at its actual first section so those pages do not pollute chapter 1.
                chapter_start = next((i for i, p in enumerate(paras) if re.match(r"^[\s|]*第一节\s+", p)), None)
                if chapter_start is not None:
                    paras = paras[chapter_start:]
            joined = "\n".join(paras)
            # Extract meaningful study points while excluding long tables, solution blocks and exam-analysis tables.
            topics: list[dict] = []
            current_section = title
            for p in paras:
                clean_line = p.lstrip(" |　")
                section = re.match(r"第([一二三四五六七八九十百\d]+)节", clean_line)
                if section:
                    current_section = clean_line[section.end():].strip(" ：:|　")[:48] or title
                    topics.append({"name": current_section, "kind": "section"})
                    continue
                if re.match(r"(?:\d{1,2}[.、]\s*|[一二三四五六七八九十]+、)\S{3,45}$", p) and len(p) <= 60:
                    candidate = re.sub(r"^\d{1,2}[.、]\s*|^[一二三四五六七八九十]+、", "", p).strip()
                    if candidate and candidate not in {x["name"] for x in topics}:
                        topics.append({"name": candidate, "kind": "topic"})
                if 18 <= len(p) <= 150 and not any(x in p for x in ("【答案】", "【解析】", "试卷Ⅰ", "试卷Ⅱ")):
                    if not re.search(r"例题|教材例题|考情分析|目录|考试时间|考试方式", p):
                        # Prefer declarative source material over headers and table fragments.
                        clean = p.strip("▪　 ")
                        if clean and not clean.startswith(("注：", "【提示】", "注:", "答案：")) and not re.match(r"^[A-D][.．、]", clean):
                            topics.append({"name": clean, "kind": "fact", "section": current_section})

            # Preserve text on the question side of answer/analysis markers for the bank builder.
            source_items = []
            source_signatures: set[str] = set()
            previous_answer = -1
            question_heading = re.compile(r"例题[·.]|经典真题|(?:19|20)\d{2}年.{0,20}(?:单选题|多选题|计算分析题|题)")
            for i, paragraph in enumerate(paras):
                if "【答案】" not in paragraph:
                    continue
                search_floor = max(previous_answer + 1, i - 160)
                start = max(previous_answer + 1, i - 14)
                for j in range(i - 1, search_floor - 1, -1):
                    if question_heading.search(paras[j]):
                        start = j
                        break
                before = paras[start:i]
                # Keep every part of the stem, including tables and facts between the
                # question heading and option A. These rows often carry the numbers
                # needed to answer CPA calculation and case-based choice questions.
                prompt_parts = []
                for candidate in before:
                    first_option = re.search(r"(?:^|\s)A[.．、]\s*", candidate)
                    if first_option:
                        lead = candidate[:first_option.start()].strip()
                        if lead:
                            prompt_parts.append(lead)
                        break
                    prompt_parts.append(candidate.strip())
                prompt = "\n".join(part for part in prompt_parts if part)
                option_matches = []
                for candidate in before[1:]:
                    match = re.match(r"^\s*([A-D])[.．、]\s*(.+)$", candidate)
                    if match:
                        option_matches.append((match.group(1), match.group(2)))
                    else:
                        option_matches.extend(re.findall(r"(?:^|\s)([A-D])[.．、]\s*([^|]+?)(?=\s+[A-D][.．、]|$)", candidate))
                # Some source paragraphs contain prompt and choices on a single line.
                if len(option_matches) < 3:
                    flat = "\n".join(before)
                    option_matches = re.findall(r"(?:^|\s)([A-D])[.．、]\s*(.*?)(?=\s+[A-D][.．、]|$)", flat)
                ans_match = re.search(r"【答案】\s*([A-D](?:\s*[、,， ]\s*[A-D])*)", paragraph)
                if not ans_match:
                    previous_answer = i
                    continue
                answers = re.findall(r"[A-D]", ans_match.group(1))
                if not answers:
                    previous_answer = i
                    continue
                options = []
                seen_keys = set()
                for key, value in option_matches:
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)
                    options.append({"key": key, "text": value.strip()})
                if len(options) < 3:
                    previous_answer = i
                    continue
                source_signature = normalize(prompt) + "|" + "|".join(normalize(x["text"]) for x in options[:4])
                if source_signature in source_signatures:
                    previous_answer = i
                    continue
                source_signatures.add(source_signature)
                expl = ""
                for next_paragraph in paras[i + 1:min(len(paras), i + 5)]:
                    if "【解析】" in next_paragraph:
                        expl = next_paragraph.split("【解析】", 1)[1].strip()
                        break
                    if "【答案】" in next_paragraph or "例题·" in next_paragraph:
                        break
                year = re.search(r"(?:19|20)\d{2}年", prompt)
                prefix_patterns = [r"^[·▪\s]*(?:例题[·\s]*(?:单选题|多选题)?[·\s]*)+", r"^[·▪\s]*(?:19|20)\d{2}年[·\s]*(?:例题[·\s]*(?:单选题|多选题)?[·\s]*)?"]
                previous = None
                while previous != prompt:
                    previous = prompt
                    for prefix in prefix_patterns:
                        prompt = re.sub(prefix, "", prompt).strip()
                if not prompt.strip():
                    previous_answer = i
                    continue
                source_topic = title
                for prior in reversed(paras[:start]):
                    prior_line = prior.lstrip(" |　")
                    section_match = re.match(r"第([一二三四五六七八九十百\d]+)节", prior_line)
                    if section_match:
                        source_topic = prior_line[section_match.end():].strip(" ：:|　")[:48] or title
                        break
                source_items.append({
                    "prompt": prompt.strip(), "options": options[:5], "answer": answers,
                    "explanation": expl, "year": year.group(0)[:4] if year else None,
                    "topic": source_topic, "source_file": name,
                    "sourceType": "past-exam" if year else "textbook-example",
                    "page": find_pdf_page(chapter_id, prompt, pdf_pages),
                })
                previous_answer = i

            # Count recent exam frequency from the chapter's exam-table region.
            analysis_paras = all_paras if chapter_id == "01" else paras
            try:
                analysis_start = next(i for i, x in enumerate(analysis_paras) if "本章考情分析" in x)
            except StopIteration:
                analysis_start = 0
            section_start = next((i for i in range(analysis_start + 1, len(analysis_paras)) if analysis_paras[i].lstrip(" |　").startswith(tuple(f"第{x}节" for x in "一二三四五六七八九十"))), len(analysis_paras))
            exam_region = "\n".join(analysis_paras[analysis_start:section_start])
            exam_frequency = 0
            for match in re.findall(r"(?:\d+(?:\.\d+)?题|\d+题)", exam_region):
                try:
                    exam_frequency += max(1, round(float(re.search(r"\d+(?:\.\d+)?", match).group()) * 10))
                except Exception:
                    exam_frequency += 1
            importance_terms = sum(len(re.findall(term, joined)) for term in ("重点", "重要", "掌握", "难点", "高频"))
            fact_rows = [x for x in topics if x["kind"] == "fact"]
            section_count = sum(x["kind"] in {"section", "topic"} for x in topics)
            chapters[chapter_id] = {
                "meta": {"id": chapter_id, "title": title, "sourceFile": name,
                         "importanceSignals": importance_terms, "examFrequency": exam_frequency,
                         "topicBreadth": max(1, section_count), "factCount": len(fact_rows),
                         "sourceQuestionCount": len(source_items), "textChars": len(joined)},
                "topics": topics, "sourceQuestions": source_items,
            }
    return [], chapters


def largest_remainder(chapters: dict[str, list[dict]], total: int = 15000) -> dict[str, int]:
    ids = sorted(chapters, key=int)
    reserve = 100
    remaining = total - reserve * len(ids)
    importance = {cid: chapters[cid]["meta"]["importanceSignals"] + 1 for cid in ids}
    exam = {cid: chapters[cid]["meta"]["examFrequency"] + 1 for cid in ids}
    breadth = {cid: chapters[cid]["meta"]["topicBreadth"] + 1 for cid in ids}
    sums = (sum(importance.values()), sum(exam.values()), sum(breadth.values()))
    scores = {cid: 0.50 * importance[cid] / sums[0] + 0.30 * exam[cid] / sums[1] + 0.20 * breadth[cid] / sums[2] for cid in ids}
    exact = {cid: remaining * scores[cid] for cid in ids}
    allocated = {cid: reserve + math.floor(exact[cid]) for cid in ids}
    left = total - sum(allocated.values())
    for cid in sorted(ids, key=lambda c: exact[c] - math.floor(exact[c]), reverse=True)[:left]:
        allocated[cid] += 1
    return allocated


def main() -> None:
    _, chapters = parse_source()
    if len(chapters) != 20 or sorted(chapters, key=int) != [f"{i:02d}" for i in range(1, 21)]:
        raise ValueError(f"应提取20章，实际{len(chapters)}章：{sorted(chapters)}")
    quotas = largest_remainder(chapters)
    for cid, chapter in chapters.items():
        chapter["meta"]["quota"] = quotas[cid]
    OUT.mkdir(parents=True, exist_ok=True)
    source_path = Path(__import__("tempfile").gettempdir()) / "cpa-financial-source-analysis.json"
    source_path.write_text(json.dumps(chapters, ensure_ascii=False), encoding="utf-8")
    build_questions(chapters, quotas)
    print(json.dumps({cid: {**x["meta"], "topics": len(x["topics"])} for cid, x in sorted(chapters.items())}, ensure_ascii=False, indent=2))


def clean_fact(value: str) -> str:
    value = re.sub(r"\s+", "", value).strip("▪　•；;。")
    return value


MATH_GLYPHS = str.maketrans({
    **dict(zip("⁰¹²³⁴⁵⁶⁷⁸⁹", (f"^{n}" for n in range(10)))),
    **dict(zip("₀₁₂₃₄₅₆₇₈₉", (f"_{n}" for n in range(10)))),
    "ⁿ": "^n", "ᵗ": "^t", "ₛ": "_s", "ᵣ": "_r",
})


def normalize_math_glyphs(value):
    if isinstance(value, str):
        # Preserve a multi-digit exponent as one exponent, not e.g. ^1^2.
        value = re.sub(r"[⁰¹²³⁴⁵⁶⁷⁸⁹]+", lambda m: "^(" + m[0].translate(str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")) + ")", value)
        value = re.sub(r"[₀₁₂₃₄₅₆₇₈₉]+", lambda m: "_(" + m[0].translate(str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")) + ")", value)
        return value.translate(MATH_GLYPHS)
    if isinstance(value, list):
        return [normalize_math_glyphs(item) for item in value]
    if isinstance(value, dict):
        return {key: normalize_math_glyphs(item) for key, item in value.items()}
    return value


def is_declarative_fact(value: str) -> bool:
    cues = ("是", "指", "可以", "应当", "不得", "必须", "包括", "等于", "属于", "称为", "反映", "提高", "降低", "增加", "减少", "导致", "取决于", "表现为", "扩展为", "意味着", "要求", "需要", "越", "不是", "有助于")
    incomplete_ends = (":", "：", "，", "、", "和", "或", "及", "为", "是", "包括", "例如", "如下", "方法", "内容", "关系", "特点", "影响")
    return any(cue in value for cue in cues) and not value.endswith(incomplete_ends)


OPPOSITES = [
    ("不可以", "可以"), ("不得", "可以"), ("不能", "可以"), ("不应当", "应当"),
    ("不应", "应当"), ("可以", "不可以"), ("应当", "不应当"), ("必须", "无须"),
    ("增加", "减少"), ("减少", "增加"), ("提高", "降低"), ("降低", "提高"),
    ("高于", "低于"), ("低于", "高于"), ("大于", "小于"), ("小于", "大于"),
    ("正相关", "负相关"), ("负相关", "正相关"), ("固定成本", "变动成本"),
    ("变动成本", "固定成本"), ("经营风险", "财务风险"), ("财务风险", "经营风险"),
    ("现值", "终值"), ("终值", "现值"), ("税前", "税后"), ("税后", "税前"),
    ("经营现金流量", "融资现金流量"), ("融资现金流量", "经营现金流量"),
    ("相关成本", "不相关成本"), ("不相关成本", "相关成本"),
]


def invert_fact(text: str) -> tuple[str, str] | None:
    for old, new in OPPOSITES:
        if old in text:
            return text.replace(old, new, 1), f"将“{old}”错误地改为“{new}”"
    if "是指" in text:
        return text.replace("是指", "不是指", 1), "颠倒了定义"
    if "包括" in text:
        return text.replace("包括", "不包括", 1), "颠倒了包含关系"
    if "等于" in text:
        return text.replace("等于", "不等于", 1), "颠倒了等式关系"
    if "取决于" in text:
        return text.replace("取决于", "不取决于", 1), "颠倒了因果关系"
    if "由" in text and "组成" in text:
        return text.replace("由", "不由", 1), "颠倒了组成关系"
    return None


def calculation_item(chapter: int, rng: random.Random, topic: str, stem: str, answer: float, unit: str, explanation: str) -> dict:
    return {"topic": topic, "stem": stem, "numericAnswer": round(answer, 2), "unit": unit,
            "explanation": explanation, "sourceType": "original",
            "source": f"依据第{chapter}章考点原创编写", "difficulty": rng.choices(["基础", "进阶", "冲刺"], [0.35, 0.45, 0.20])[0],
            "type": "calculation", "tags": [topic]}


def alternate_calculation(chapter: int, rng: random.Random) -> dict | None:
    """Use distinct learning objectives so numerical practice is not just parameter substitution."""
    if chapter == 2:
        ca, inventory, cl = rng.randint(300, 3000), rng.randint(40, 800), rng.randint(200, 1800)
        answer = (ca - inventory) / cl
        return calculation_item(chapter, rng, "财务比率分析—速动比率",
            f"某企业流动资产{ca}万元，其中存货{inventory}万元；流动负债{cl}万元。按速动比率口径计算其短期偿债指标。",
            answer, "倍", f"速动比率=(流动资产−存货)÷流动负债=({ca}−{inventory})÷{cl}={answer:.2f}倍。")
    if chapter == 3:
        future, rate, years = rng.randint(100, 5000), rng.choice([0.04, 0.05, 0.06, 0.08, 0.10]), rng.randint(2, 8)
        answer = future / (1 + rate) ** years
        return calculation_item(chapter, rng, "货币时间价值—复利现值",
            f"若{years}年后需要取得{future}万元，年利率为{rate:.0%}且按年复利，现需一次存入多少万元？",
            answer, "万元", f"复利现值=P=F/(1+i)^n={future}/(1+{rate:.0%})^{years}={answer:.2f}万元。")
    if chapter == 4:
        kd, tax = rng.randrange(4, 11) / 100, rng.randrange(15, 26) / 100
        answer = kd * (1 - tax) * 100
        return calculation_item(chapter, rng, "资本成本—税后债务资本成本",
            f"某公司债务资本成本为{kd:.0%}，适用所得税税率为{tax:.0%}。在利息税前扣除条件成立时，税后债务资本成本为多少？",
            answer, "%", f"税后债务资本成本=税前债务资本成本×(1−所得税税率)={kd:.0%}×(1−{tax:.0%})={answer:.2f}%。")
    if chapter == 5:
        investment, cf = rng.randrange(100, 1001, 10), rng.randrange(30, 201, 10)
        answer = investment / cf
        return calculation_item(chapter, rng, "投资项目资本预算—静态回收期",
            f"某项目初始投资{investment}万元，预计每年年末产生相等的现金净流量{cf}万元。按静态回收期法，投资回收期为多少年？",
            answer, "年", f"静态回收期=原始投资额÷每年现金净流量={investment}÷{cf}={answer:.2f}年；该法不折现现金流量。")
    if chapter == 6:
        spot, strike, rate = rng.randint(50, 300), rng.randint(50, 300), rng.randrange(2, 9) / 100
        pv_strike = strike / (1 + rate)
        put = max(rng.randint(1, 40), math.ceil(pv_strike - spot + 1))
        answer = put + spot - pv_strike
        return calculation_item(chapter, rng, "期权价值评估—看涨看跌平价",
            f"某股票现价{spot}元，执行价格{strike}元的一年期欧式看跌期权价值为{put}元，无风险年利率为{rate:.0%}。按看涨看跌平价关系，欧式看涨期权价值为多少元？",
            answer, "元", f"看涨看跌平价C−P=S0−PV(K)；PV(K)={strike}÷(1+{rate:.0%})={pv_strike:.2f}元；C=P+S0−PV(K)={put}+{spot}−{pv_strike:.2f}={answer:.2f}元。")
    if chapter == 7:
        ebitda, multiple = rng.randint(100, 2000), rng.randrange(6, 13)
        debt, cash, shares = rng.randint(100, min(5000, ebitda * multiple)), rng.randint(50, 2000), rng.randint(100, 1000)
        answer = (ebitda * multiple - debt + cash) / shares
        return calculation_item(chapter, rng, "企业价值评估—相对价值法",
            f"可比企业的EV/EBITDA倍数为{multiple}倍。目标企业EBITDA为{ebitda}万元，付息债务{debt}万元、现金{cash}万元，普通股{shares}万股。估计每股股权价值。",
            answer, "元/股", f"企业价值={ebitda}×{multiple}={ebitda*multiple}万元；股权价值=企业价值−债务+现金={ebitda*multiple}−{debt}+{cash}={ebitda*multiple-debt+cash}万元；每股价值={ebitda*multiple-debt+cash}÷{shares}={answer:.2f}元/股。")
    if chapter == 8:
        price, variable, volume, fixed = rng.randint(80, 300), rng.randint(20, 70), rng.randint(1000, 8000), rng.randint(20000, 150000)
        if variable >= price:
            variable = price - 10
        contribution = (price - variable) * volume
        ebit = contribution - fixed
        if ebit <= 0:
            fixed = max(1000, contribution // 2)
            ebit = contribution - fixed
        answer = contribution / ebit
        return calculation_item(chapter, rng, "资本结构—经营杠杆系数",
            f"某企业产品单价{price}元，单位变动成本{variable}元，销量{volume}件，固定经营成本{fixed}元。计算经营杠杆系数。",
            answer, "倍", f"边际贡献=({price}−{variable})×{volume}={contribution}元；息税前利润={contribution}−{fixed}={ebit}元；DOL=边际贡献÷息税前利润={contribution}÷{ebit}={answer:.2f}倍。")
    if chapter == 11:
        daily, lead, safety = rng.randint(20, 400), rng.randint(2, 15), rng.randint(0, 1200)
        answer = daily * lead + safety
        return calculation_item(chapter, rng, "营运资本管理—再订货点",
            f"某材料日均耗用量{daily}件，订货提前期{lead}天，安全库存{ safety }件。计算再订货点。",
            answer, "件", f"再订货点=日需求量×提前期+安全库存={daily}×{lead}+{safety}={answer}件。")
    if chapter == 14:
        aq, sq, sp = rng.randint(500, 20000), rng.randint(500, 20000), rng.randint(3, 30)
        answer = (aq - sq) * sp
        return calculation_item(chapter, rng, "标准成本法—直接材料数量差异",
            f"某产品实际耗用材料{aq}千克，标准允许用量{sq}千克，标准单价{sp}元/千克。计算直接材料数量差异，正数表示不利差异。",
            answer, "元", f"材料数量差异=(实际用量−标准用量)×标准价格=({aq}−{sq})×{sp}={answer}元。")
    if chapter == 16:
        price, variable, fixed, target = rng.randint(60, 300), rng.randint(15, 50), rng.randint(20000, 300000), rng.randint(10000, 100000)
        if variable >= price:
            variable = price - 10
        raw_sales = (fixed + target) / (price - variable)
        answer = math.ceil(raw_sales)
        return calculation_item(chapter, rng, "本量利分析—目标利润销售量",
            f"某产品单价{price}元、单位变动成本{variable}元，固定成本{fixed}元。若目标利润为{target}元，需销售多少件？",
            answer, "件", f"目标利润销售量=({fixed}+{target})÷({price}−{variable})={raw_sales:.2f}件；销售量按整件向上取整=向上取整({raw_sales:.2f})={answer}件。")
    if chapter == 17:
        buy, make_v, avoidable, qty = rng.randint(20, 100), rng.randint(10, 60), rng.randint(0, 30), rng.randint(1000, 10000)
        if make_v >= buy:
            make_v = buy - 5
        advantage = qty * (buy - make_v - avoidable)
        return calculation_item(chapter, rng, "短期经营决策—自制或外购",
            f"某零件年需求{qty}件。外购单价{buy}元；自制单位变动成本{make_v}元，外购后可避免专属固定成本{avoidable}元/件。选择自制相对外购可节约多少元（负数表示外购更优）？",
            advantage, "元", f"自制相对外购差额={qty}×(外购单价−自制变动成本−可避免固定成本)={qty}×({buy}−{make_v}−{avoidable})={advantage}元。")
    if chapter == 18:
        production, per_unit, ending, beginning = rng.randint(1000, 20000), rng.randint(2, 8), rng.randint(100, 3000), rng.randint(100, 3000)
        answer = production * per_unit + ending - beginning
        return calculation_item(chapter, rng, "全面预算—直接材料采购预算",
            f"预算期计划生产{production}件产品，单位产品耗用材料{per_unit}千克；期末材料库存{ending}千克，期初库存{beginning}千克。预算材料采购量为多少千克？",
            answer, "千克", f"采购量=生产耗用量+期末库存−期初库存={production}×{per_unit}+{ending}−{beginning}={answer}千克。")
    if chapter == 19:
        profit, assets = rng.randint(100, 3000), rng.randint(500, 20000)
        answer = profit / assets * 100
        return calculation_item(chapter, rng, "责任会计—投资报酬率",
            f"某投资中心税前经营利润{profit}万元，平均经营资产{assets}万元。按投资报酬率口径计算其业绩指标。",
            answer, "%", f"投资报酬率=税前经营利润÷平均经营资产×100%={profit}÷{assets}×100%={answer:.2f}%。")
    return None


def calc_question(chapter: int, rng: random.Random) -> dict:
    """Generate a numerical CPA-style exercise with computed result and a visible formula trail."""
    if rng.random() < 0.5:
        varied = alternate_calculation(chapter, rng)
        if varied:
            return varied
    money = rng.choice([80, 120, 150, 200, 240, 300, 360, 480, 600, 750])
    rate = rng.choice([0.04, 0.05, 0.06, 0.08, 0.10, 0.12])
    years = rng.choice([2, 3, 4, 5])
    if chapter == 2:
        cl = rng.randint(100, 2000)
        ca = rng.randint(round(cl * 1.25), round(cl * 2.50))
        ans = round(ca / cl, 2)
        topic = "财务比率分析—流动比率"
        stem = f"甲公司期末流动资产为{ca:.0f}万元，流动负债为{cl:.0f}万元。该公司的流动比率为多少？"
        formula = f"流动比率=流动资产÷流动负债={ca:.0f}÷{cl:.0f}={ans:.2f}。"
        unit = "倍"
    elif chapter == 3:
        money = rng.randint(100, 5000)
        rate = rng.randrange(20, 151, 1) / 1000
        years = rng.randint(2, 12)
        ans = money * (1 + rate) ** years
        topic = "货币时间价值—复利终值"
        stem = f"现存入银行{money}万元，年利率为{rate:.1%}，按年复利计息。{years}年后的本利和为多少万元？"
        exponent = str(years).translate(str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹"))
        formula = f"复利终值=P×(1+i)ⁿ={money}×(1+{rate:.1%}){exponent}={ans:.2f}万元。"
        unit = "万元"
    elif chapter == 4:
        rf = rng.randrange(15, 41, 1) / 1000
        beta = rng.randrange(7, 19, 1) / 10
        rm = rng.randrange(70, 151, 5) / 1000
        if rm <= rf:
            rm = rf + 0.04
        ans = rf + beta * (rm - rf)
        topic = "资本成本—资本资产定价模型"
        stem = f"无风险报酬率为{rf:.1%}，市场组合报酬率为{rm:.1%}，某公司β系数为{beta:.1f}。按资本资产定价模型估计其权益资本成本。"
        formula = f"权益资本成本=R_f+β(R_m−R_f)={rf:.1%}+{beta:.1f}×({rm:.1%}−{rf:.1%})={ans:.2%}。"
        unit = "%"
        ans *= 100
    elif chapter == 5:
        investment = rng.randrange(80, 1001, 10)
        cf = investment * rng.randrange(35, 61, 1) / 100
        rate = rng.randrange(8, 16) / 100
        rate = 0.10
        pvf = [1 / (1 + rate) ** t for t in (1, 2, 3)]
        ans = -investment + cf * sum(pvf)
        topic = "投资项目资本预算—净现值"
        stem = f"项目初始投资{investment}万元，预计未来3年每年年末产生现金净流量{cf:.2f}万元，折现率10%。净现值为多少万元？"
        formula = f"NPV=−{investment}+{cf:.2f}/(1+{rate:.0%})+{cf:.2f}/(1+{rate:.0%})²+{cf:.2f}/(1+{rate:.0%})³={ans:.2f}万元。"
        unit = "万元"
    elif chapter == 6:
        s = rng.randrange(20, 301, 5)
        strike = round(s * rng.randrange(85, 116, 1) / 100, 2)
        up, down = rng.choice([1.15, 1.20, 1.25, 1.30, 1.35]), rng.choice([0.65, 0.70, 0.75, 0.80, 0.85])
        r = rng.randrange(2, 9) / 100
        if up <= 1 + r or down >= 1 + r:
            up, down = 1.25, 0.75
        p = ((1 + r) - down) / (up - down)
        cu, cd = max(s * up - strike, 0), max(s * down - strike, 0)
        ans = (p * cu + (1 - p) * cd) / (1 + r)
        topic = "期权价值评估—单期二叉树看涨期权"
        stem = f"股票现价{s}元、执行价格{strike:.2f}元；一期后股价分别按上行{up-1:.0%}或下行{1-down:.0%}变动，无风险利率为{r:.0%}。按风险中性定价，欧式看涨期权现值为多少元？"
        formula = f"风险中性概率p=[(1+{r:.0%})−{down:.2f}]/({up:.2f}−{down:.2f})={p:.4f}；Cu={cu:.2f}，Cd={cd:.2f}；期权价值=[pCu+(1−p)Cd]/(1+{r:.0%})={ans:.2f}元。"
        unit = "元"
    elif chapter == 7:
        fcfe = rng.randint(80, 1200)
        growth, required = rng.randrange(0, 61, 1) / 1000, rng.randrange(7, 16) / 100
        if required <= growth:
            required = growth + 0.04
        ans = fcfe / (required - growth)
        topic = "企业价值评估—股权现金流量折现模型"
        stem = f"某公司预计下一年股权现金流量为{fcfe:.2f}万元，此后按{growth:.1%}永续增长，股权资本成本为{required:.1%}。股权价值为多少万元？"
        formula = f"股权价值=FCFE₁/(rₛ−g)={fcfe:.2f}/({required:.1%}−{growth:.1%})={ans:.2f}万元。"
        unit = "万元"
    elif chapter == 8:
        ebit = rng.randint(500, 10000)
        interest = rng.randint(50, ebit // 2)
        ans = ebit / (ebit - interest)
        topic = "资本结构—财务杠杆系数"
        stem = f"某公司息税前利润为{ebit:.0f}万元，利息费用为{interest:.0f}万元。按定义计算财务杠杆系数。"
        formula = f"DFL=EBIT/(EBIT−I)={ebit:.0f}/({ebit:.0f}−{interest:.0f})={ans:.2f}。"
        unit = "倍"
    elif chapter == 9:
        face = rng.randrange(100000, 3000001, 10000)
        coupon = rng.randrange(30, 101, 5) / 1000
        ytm = rng.randrange(40, 121, 5) / 1000
        n = rng.randint(2, 12)
        ans = sum(face * coupon / (1 + ytm) ** t for t in range(1, n + 1)) + face / (1 + ytm) ** n
        topic = "长期筹资—债券价值评估"
        stem = f"面值{face:,.0f}元、票面利率{coupon:.1%}、每年付息一次、期限{n}年的债券，市场必要报酬率为{ytm:.1%}。债券价值为多少元？"
        formula = f"债券价值=Σ[票面利息/(1+r)ᵗ]+面值/(1+r)ⁿ={ans:,.2f}元。"
        unit = "元"
    elif chapter == 10:
        shares = rng.randint(100, 5000)
        div = rng.randrange(1, 21) / 10
        ans = shares * div
        topic = "股利分配—现金股利总额"
        stem = f"某公司有普通股{shares}万股，拟每股发放现金股利{div:.2f}元。现金股利总额为多少万元？"
        formula = f"现金股利总额=股数×每股股利={shares}万股×{div:.2f}元/股={ans:.2f}万元。"
        unit = "万元"
    elif chapter == 11:
        d = rng.randrange(10000, 100001, 1000)
        s = rng.randint(50, 500)
        h = rng.randint(1, 20)
        ans = math.sqrt(2 * d * s / h)
        topic = "营运资本管理—经济订货量"
        stem = f"某材料年需求量{d:,}件，每次订货成本{s}元，单位材料年储存成本{h}元。不考虑数量折扣，经济订货量约为多少件？"
        formula = f"EOQ=√(2DS/H)=√(2×{d}×{s}/{h})={ans:.2f}件。"
        unit = "件"
    elif chapter == 12:
        q1 = rng.randint(1000, 6000)
        q2 = q1 + rng.randint(500, 3000)
        b = rng.randint(2, 25)
        a = rng.randint(1000, 20000)
        y1, y2 = a + b * q1, a + b * q2
        ans = (y2 - y1) / (q2 - q1)
        topic = "成本管理会计基础—高低点法"
        stem = f"某企业业务量{q1}件时总成本{y1}元，业务量{q2}件时总成本{y2}元。按高低点法估计单位变动成本。"
        formula = f"单位变动成本=(高点成本−低点成本)/(高点业务量−低点业务量)=({y2}−{y1})/({q2}−{q1})={ans:.2f}元/件。"
        unit = "元/件"
    elif chapter == 13:
        completed = rng.randrange(1000, 7001, 100)
        end = rng.randrange(100, 2501, 100)
        pct = rng.randrange(1, 10) / 10
        equivalent = completed + end * pct
        costs = rng.randrange(20000, 250001, 1000)
        ans = costs / equivalent
        topic = "产品成本计算—约当产量法"
        stem = f"本期完工产品{completed}件，月末在产品{end}件，完工程度{pct:.0%}。本期应分配的某项加工成本为{costs:,}元（假定无期初在产品成本），单位约当产量成本为多少元？"
        formula = f"约当产量={completed}+{end}×{pct:.0%}={equivalent:.0f}件；单位成本={costs}/{equivalent:.0f}={ans:.2f}元/件。"
        unit = "元/件"
    elif chapter == 14:
        aq, ap, sp = rng.randint(500, 20000), rng.randint(3, 30), rng.randint(3, 30)
        ans = aq * (ap - sp)
        topic = "标准成本法—直接材料价格差异"
        stem = f"本期实际耗用材料{aq}千克，实际单价{ap}元/千克，标准单价{sp}元/千克。直接材料价格差异为多少元？（正数表示不利差异）"
        formula = f"材料价格差异=实际数量×(实际价格−标准价格)={aq}×({ap}−{sp})={ans:.2f}元。"
        unit = "元"
    elif chapter == 15:
        pool, drivers = rng.randint(100000, 2000000), rng.randint(500, 20000)
        ans = pool / drivers
        topic = "作业成本法—作业成本分配率"
        stem = f"某作业成本库归集成本{pool:,}元，成本动因总量{drivers:,}次。该成本库的单位成本动因分配率为多少元/次？"
        formula = f"分配率=作业成本库成本÷成本动因总量={pool:,}÷{drivers:,}={ans:.2f}元/次。"
        unit = "元/次"
    elif chapter == 16:
        price = rng.randint(40, 300)
        vc = rng.randint(5, price - 10)
        fixed = rng.randrange(20000, 1000001, 1000)
        ans = fixed / (price - vc)
        topic = "本量利分析—盈亏临界点销售量"
        stem = f"某产品单价{price}元，单位变动成本{vc}元，固定成本总额{fixed:,}元。盈亏临界点销售量为多少件？"
        formula = f"盈亏临界点销售量=固定成本/(单价−单位变动成本)={fixed:,}/({price}−{vc})={ans:.2f}件。"
        unit = "件"
    elif chapter == 17:
        price = rng.randint(80, 300)
        vc = rng.randint(30, price - 10)
        qty = rng.randint(200, 10000)
        fixed = rng.randrange(1000, 100001, 1000)
        ans = qty * (price - vc) - fixed
        topic = "短期经营决策—特殊订单增量收益"
        stem = f"企业有剩余产能，可接受特殊订单{qty}件，订单单价{price}元，单位变动成本{vc}元；接受订单需增加专属固定成本{fixed:,}元。接受订单对利润的影响为多少元？"
        formula = f"增量利润={qty}×({price}−{vc})−{fixed:,}={ans:.2f}元。结果为正表示接受订单增加利润。"
        unit = "元"
    elif chapter == 18:
        sales = rng.randrange(5000, 50001, 100)
        ending = rng.randrange(1000, 10001, 100)
        beginning = rng.randrange(1000, 10001, 100)
        ans = sales + ending - beginning
        topic = "全面预算—生产预算"
        stem = f"预算期预计销售量{sales:,}件，期末产成品存货{ending:,}件，期初存货{beginning:,}件。预算生产量为多少件？"
        formula = f"生产量=销售量+期末存货−期初存货={sales:,}+{ending:,}−{beginning:,}={ans:,}件。"
        unit = "件"
    elif chapter == 19:
        profit, assets, rate0 = rng.randint(100, 1200), rng.randint(500, 8000), rng.randrange(5, 19) / 100
        ans = profit - assets * rate0
        topic = "责任会计—剩余收益"
        stem = f"某投资中心税前经营利润{profit}万元，平均经营资产{assets}万元，要求的最低投资报酬率为{rate0:.0%}。剩余收益为多少万元？"
        formula = f"剩余收益=经营利润−平均经营资产×最低报酬率={profit}−{assets}×{rate0:.0%}={ans:.2f}万元。"
        unit = "万元"
    else:
        nopat, capital, wacc = rng.randint(100, 2000), rng.randint(800, 15000), rng.randrange(4, 16) / 100
        ans = nopat - capital * wacc
        topic = "业绩评价—经济增加值"
        stem = f"某企业税后净营业利润{nopat}万元，投入资本{capital}万元，加权平均资本成本为{wacc:.0%}。经济增加值为多少万元？"
        formula = f"EVA=税后净营业利润−投入资本×加权平均资本成本={nopat}−{capital}×{wacc:.0%}={ans:.2f}万元。"
        unit = "万元"
    # Round to two decimals for display and deterministic numeric grading.
    ans = round(ans, 2)
    ref = f"闫华红《轻1·基础细讲班》{chapter}章相关考点原创计算题"
    return {"topic": topic, "stem": stem, "numericAnswer": ans, "unit": unit,
            "explanation": formula, "sourceType": "original", "source": ref,
            "difficulty": rng.choices(["基础", "进阶", "冲刺"], [0.35, 0.45, 0.20])[0],
            "type": "calculation", "tags": [topic]}


def make_original_concept(chapter_id: str, info: dict, rng: random.Random, serial: int) -> dict:
    chapter = int(chapter_id)
    facts = []
    for row in info["topics"]:
        if row.get("kind") != "fact":
            continue
        fact = clean_fact(row["name"])
        if 24 <= len(fact) <= 120 and "|" not in fact and is_declarative_fact(fact) \
                and not re.search(r"\d|[=<>+*/√×÷]|(?:例题|教材例题|题目|答案|解析|表格|计算|如下|求|试卷Ⅰ|试卷Ⅱ|选项[A-D]|年末|年初|万元|元/)", fact) \
                and not fact.endswith(("，", "、", "和", "或", "及", "：", ":", "。")):
            fact = re.sub(r"^[A-D][.．、]\s*", "", fact)
            if re.match(r"^[A-D][.．、]", fact):
                continue
            facts.append({"text": fact, "section": row.get("section", "本章核心考点")})
    facts = list({x["text"]: x for x in facts}.values())
    if not facts:
        # Fall back to short, non-numeric section statements; these are still tied to extracted notes.
        facts = [{"text": clean_fact(row["name"]), "section": row.get("section", info["meta"]["title"])}
                 for row in info["topics"] if row.get("kind") == "fact" and 24 <= len(clean_fact(row["name"])) <= 120
                 and not re.search(r"\d|[=<>+*/√×÷]|(?:例题|答案|解析|计算|求|如下)", clean_fact(row["name"]))]
    if not facts:
        raise ValueError(f"第{chapter}章没有足够的讲义事实可用于构造概念题")
    fact_texts = {x["text"] for x in facts}
    invertible = [(row, invert_fact(row["text"])) for row in facts]
    invertible = [(row, inv) for row, inv in invertible if inv and inv[0] not in fact_texts]
    target, corrupted = invertible[serial % len(invertible)] if invertible else (facts[serial % len(facts)], None)
    if corrupted is None:
        # Retain a true source statement and create a logically opposite, clearly scoped proposition.
        false_fact = f"在{target['section']}中，{target['text']}这一判断方向应完全相反。"
        reason = "该表述颠倒了讲义中的判断方向"
    else:
        false_fact, reason = corrupted
    section_facts = [x["text"] for x in facts if x["section"] == target["section"] and x["text"] != target["text"] and x["text"] != false_fact]
    if len(section_facts) < 3:
        section_facts = [x["text"] for x in facts if x["text"] != target["text"]]
    rng.shuffle(section_facts)
    true_facts = section_facts[:3]
    while len(true_facts) < 3:
        true_facts.append(f"{info['meta']['title']}的分析应依据题目给出的已知条件和适用公式。")
    wrong_count = 2 if serial % 5 == 0 else 1
    options_raw = [(false_fact, True)]
    reasons = [reason]
    if wrong_count == 2:
        same_section = [(row, inv) for row, inv in invertible if row["section"] == target["section"] and row["text"] != target["text"] and inv[0] not in true_facts and inv[0] != false_fact]
        second_candidates = same_section or [(row, inv) for row, inv in invertible if row["text"] != target["text"] and inv[0] not in true_facts and inv[0] != false_fact]
        second_target, second_bad = second_candidates[(serial + 7) % len(second_candidates)] if second_candidates else (None, None)
        if second_bad:
            options_raw.append((second_bad[0], True))
            true_facts = true_facts[:2]
            reasons.append(second_bad[1])
    options_raw.extend((f, False) for f in true_facts)
    unique_raw = []
    seen_raw = set()
    for item in options_raw:
        if item[0] not in seen_raw:
            unique_raw.append(item)
            seen_raw.add(item[0])
    if len(unique_raw) < 4:
        for row in facts:
            if row["text"] not in seen_raw and row["text"] not in {false_fact}:
                unique_raw.append((row["text"], False))
                seen_raw.add(row["text"])
            if len(unique_raw) == 4:
                break
    options_raw = unique_raw
    options_raw = options_raw[:4]
    rng.shuffle(options_raw)
    options = [{"key": chr(65 + i), "text": text} for i, (text, _) in enumerate(options_raw)]
    frames = ["某分析人员据此作出判断，下列哪项判断不正确？", "结合题目所述条件，下列说法错误的是？", "下列关于该考点的理解不准确的是？", "下列选项中，哪项与本章原理不符？",
              "针对该管理情境，下列哪项处理思路不恰当？", "下列判断中，哪项违背该考点的适用条件？", "根据上述概念，下列表述错误的是？", "下列说法中需要修正的是？",
              "某分析人员据此作出判断，下列哪些判断正确？", "结合题目所述条件，下列哪些说法正确？", "下列关于该考点的理解，哪些准确？", "下列选项中，哪些符合本章原理？",
              "针对该管理情境，下列哪些处理思路恰当？", "下列判断中，哪些符合该考点的适用条件？", "根据上述概念，下列哪些表述正确？", "下列说法中哪些无需修正？"]
    frame_index = (serial // max(1, len(invertible))) % len(frames)
    ask_incorrect = frame_index < 8
    answers = [o["key"] for o, (_, wrong) in zip(options, options_raw) if wrong == ask_incorrect]
    perspectives = ["按定义理解", "结合适用条件", "从因果关系看", "对照讲义结论", "从指标口径看", "结合决策用途", "从计算关系看", "按本节要点判断"]
    context_pool = [x["text"] for x in facts if x["section"] == target["section"] and x["text"] != target["text"]]
    if len(context_pool) < 2:
        context_pool = [x["text"] for x in facts if x["text"] != target["text"]]
    base = max(1, len(invertible))
    context_fact = context_pool[(serial // (base * len(frames))) % len(context_pool)] if context_pool else "题目给定的条件应结合适用公式分析。"
    support_pool = [x for x in context_pool if x != context_fact] or context_pool
    support_fact = support_pool[(serial // (base * len(frames) * max(1, len(context_pool)))) % len(support_pool)]
    review_angle = perspectives[(serial // (base * len(frames) * max(1, len(context_pool)) * max(1, len(support_pool)))) % len(perspectives)]
    frame = frames[frame_index]
    style_index = (serial // (max(1, len(invertible)) * len(frames))) % 3
    if style_index == 0:
        stem = f"在复核「{target['section']}」时，分析人员关注以下要点：“{target['text']}”。同时需考虑：“{context_fact}”；还应结合：“{support_fact}”。{review_angle}，{frame}"
    elif style_index == 1:
        stem = f"某企业复核{target['section']}专题报告，报告提到“{context_fact}”，财务负责人又提出“{target['text']}”，并要求结合“{support_fact}”判断。{review_angle}，{frame}"
    else:
        stem = f"审阅{target['section']}方案时，资料列示三项依据：①{target['text']}；②{context_fact}；③{support_fact}。请按题设口径复核这些依据。{review_angle}，{frame}"
    stem += '（多选）' if len(answers) > 1 else '（单选）'
    explanation = (f"本题要求识别不准确表述。考点：{target['text']}。答案为{'、'.join(answers)}；{ '；'.join(reasons) }。"
                   if ask_incorrect else
                   f"本题要求识别准确表述。考点：{target['text']}。答案为{'、'.join(answers)}；其余错误表述的判断依据：{ '；'.join(reasons) }。")
    return {"topic": target["section"], "stem": stem, "options": options,
            "answer": answers, "explanation": explanation,
            "sourceType": "original", "source": f"依据闫华红《轻1·基础细讲班》{chapter}章考点原创编写",
            "difficulty": rng.choices(["基础", "进阶", "冲刺"], [0.35, 0.45, 0.20])[0],
            "type": "multiple" if len(answers) > 1 else "single",
            "tags": [target["section"], target["text"][:32]]}


def create_review_workbook(manifest: dict, question_index: list[dict]) -> None:
    wb = Workbook()
    summary = wb.active
    summary.title = "章节配额"
    summary.append(["章节", "计划题量", "实际题量", "重要标注信号", "近年真题频次指标", "考点广度", "单选", "多选", "计算", "综合", "教材例题", "历年真题", "原创"])
    bank_by_ch = Counter(q["chapterId"] for q in question_index)
    type_by_ch = Counter((q["chapterId"], q["type"]) for q in question_index)
    source_by_ch = Counter((q["chapterId"], q["sourceType"]) for q in question_index)
    for ch in manifest["chapters"]:
        cid = ch["id"]
        meta = ch["metrics"]
        summary.append([ch["title"], ch["count"], bank_by_ch[cid], meta["importanceSignals"], meta["examFrequency"], meta["topicBreadth"],
                        type_by_ch[cid, "single"], type_by_ch[cid, "multiple"], type_by_ch[cid, "calculation"], type_by_ch[cid, "case"],
                        source_by_ch[cid, "textbook-example"], source_by_ch[cid, "past-exam"], source_by_ch[cid, "original"]])
    chapter_ids = [ch["id"] for ch in manifest["chapters"]]
    summary.append(["合计", sum(ch["count"] for ch in manifest["chapters"]), len(question_index), "", "", "",
                    sum(type_by_ch[cid, "single"] for cid in chapter_ids), sum(type_by_ch[cid, "multiple"] for cid in chapter_ids),
                    sum(type_by_ch[cid, "calculation"] for cid in chapter_ids), sum(type_by_ch[cid, "case"] for cid in chapter_ids),
                    sum(source_by_ch[cid, "textbook-example"] for cid in bank_by_ch), sum(source_by_ch[cid, "past-exam"] for cid in bank_by_ch),
                    sum(source_by_ch[cid, "original"] for cid in bank_by_ch)])
    detail = wb.create_sheet("逐题核验")
    headers = ["题目ID", "章节", "考点", "题型", "难度", "来源类型", "来源", "年份", "页码", "题干", "选项", "答案", "数值答案", "单位", "解析/步骤"]
    detail.append(headers)
    for q in question_index:
        detail.append([q.get("id"), q.get("chapterTitle"), q.get("topic"), q.get("type"), q.get("difficulty"), q.get("sourceType"),
                       q.get("source"), q.get("year"), q.get("page"), q.get("stem") or q.get("material"),
                       json.dumps(q.get("options", []), ensure_ascii=False), "、".join(q.get("answer", [])), q.get("numericAnswer"), q.get("unit"), q.get("explanation")])
    for ws in wb.worksheets:
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        for cell in ws[1]:
            cell.font = Font(color="FFFFFF", bold=True)
            cell.fill = PatternFill("solid", fgColor="174F3B")
            cell.alignment = Alignment(vertical="center", wrap_text=True)
        ws.row_dimensions[1].height = 30
        for col in ws.columns:
            letter = get_column_letter(col[0].column)
            max_len = min(45, max(len(str(c.value or "")) if c.data_type != "f" else 12 for c in col[:150]))
            ws.column_dimensions[letter].width = max(12, max_len + 2)
    summary.column_dimensions["A"].width = 36
    for col in ("B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M"):
        summary.column_dimensions[col].width = 16
    for col in ("J", "K", "O"):
        detail.column_dimensions[col].width = 50
    REVIEW.mkdir(parents=True, exist_ok=True)
    wb.save(REVIEW / "cpa-financial-management-question-review.xlsx")


def next_unique_calculation(chapter: int, rng: random.Random, used: set[str]) -> dict:
    for _ in range(500):
        q = calc_question(chapter, rng)
        signature = normalize(q["stem"])
        if signature not in used:
            used.add(signature)
            return q
    raise ValueError(f"第{chapter}章计算题参数组合不足，无法继续去重")


def build_questions(chapters: dict, quotas: dict[str, int]) -> None:
    all_chapters = []
    flat_index: list[dict] = []
    retired_ids: list[str] = []
    used_all_prompts: set[str] = set()
    for cid in sorted(chapters, key=int):
        info = chapters[cid]
        chapter_num = int(cid)
        meta = info["meta"]
        questions: list[dict] = []
        # Public distribution policy: use the course files for chapter/topic mapping and
        # importance signals, but do not republish their verbatim paid-course questions.
        # All public items below are newly written from the extracted concepts.
        target = quotas[cid]
        remaining = target - len(questions)
        rng = random.Random(260826 + chapter_num)
        # Keep numeric practice substantial but avoid flooding the bank with one-formula parameter variants.
        # Numerical drills remain available, but avoid filling the bank with one-formula
        # clones that differ only in input values.
        calc_share = 0.02 if chapter_num > 1 else 0.0
        calc_count = min(remaining, round(remaining * calc_share))
        case_count = max(8, round(calc_count * 0.18)) if chapter_num in {5, 11, 16, 18, 19, 20} else 0
        calc_count -= case_count
        authored_calculations = []
        if chapter_num == 2:
            from curated_ch02 import chapter_two_applications
            authored_calculations = chapter_two_applications()
            if len(authored_calculations) != calc_count:
                raise ValueError(f"第2章手写计算题数量 {len(authored_calculations)} 不等于配额 {calc_count}")
        elif chapter_num == 3:
            from curated_ch03 import chapter_three_calculations
            authored_calculations = chapter_three_calculations()
            if len(authored_calculations) != calc_count:
                raise ValueError(f"第3章手写计算题数量 {len(authored_calculations)} 不等于配额 {calc_count}")
        elif chapter_num == 9:
            from curated_ch09 import chapter_nine_applications
            authored_calculations = chapter_nine_applications()
            if len(authored_calculations) != calc_count:
                raise ValueError(f"第9章手写计算题数量 {len(authored_calculations)} 不等于配额 {calc_count}")
        elif chapter_num == 10:
            from curated_ch10 import chapter_ten_calculations
            authored_calculations = chapter_ten_calculations()
            if len(authored_calculations) != calc_count:
                raise ValueError(f"第10章手写计算题数量 {len(authored_calculations)} 不等于配额 {calc_count}")
        elif chapter_num == 13:
            from curated_ch13 import chapter_thirteen_calculations
            authored_calculations = chapter_thirteen_calculations()
            if len(authored_calculations) != calc_count:
                raise ValueError(f"第13章手写计算题数量 {len(authored_calculations)} 不等于配额 {calc_count}")
        elif chapter_num == 15:
            from curated_ch15 import chapter_fifteen_calculations
            authored_calculations = chapter_fifteen_calculations()
            if len(authored_calculations) != calc_count:
                raise ValueError(f"第15章手写计算题数量 {len(authored_calculations)} 不等于配额 {calc_count}")
        elif chapter_num == 19:
            from curated_ch19 import chapter_nineteen_applications
            authored_calculations = chapter_nineteen_applications()
            if len(authored_calculations) != calc_count:
                raise ValueError(f"第19章手写计算题数量 {len(authored_calculations)} 不等于配额 {calc_count}")
        elif chapter_num == 20:
            from curated_ch20 import chapter_twenty_calculations
            authored_calculations = chapter_twenty_calculations()
            if len(authored_calculations) != calc_count:
                raise ValueError(f"第20章手写计算题数量 {len(authored_calculations)} 不等于配额 {calc_count}")
        for n in range(calc_count):
            if chapter_num in {3, 9, 10, 13, 15, 19, 20} and authored_calculations:
                # Preserve the legacy RNG sequence so unchanged choice-question IDs
                # continue to refer to their previous content and saved progress.
                next_unique_calculation(chapter_num, rng, used_all_prompts)
            q = authored_calculations[n].copy() if authored_calculations else next_unique_calculation(chapter_num, rng, used_all_prompts)
            q.update({"id": f"fm-{cid}-{len(questions)+1:05d}", "chapterId": cid, "chapterTitle": meta["title"],
                      "year": None, "page": None})
            if authored_calculations:
                retired_ids.append(q["id"])
                q["id"] = authored_calculations[n]["id"]
            questions.append(q)
        authored_cases = []
        if chapter_num == 20:
            from curated_ch20 import chapter_twenty_cases
            authored_cases = chapter_twenty_cases()
            if len(authored_cases) != case_count:
                raise ValueError(f"第20章手写案例数 {len(authored_cases)} 不等于配额 {case_count}")
        for n in range(case_count):
            calc = next_unique_calculation(chapter_num, rng, used_all_prompts)
            case_advice_by_topic = {
                "投资项目资本预算—净现值": ("依据净现值判断该项目是否满足价值增加原则。", "净现值为正表示按给定折现率折现后的现金流入超过初始投资，通常可接受；净现值为负则通常不接受。"),
                "投资项目资本预算—静态回收期": ("指出静态回收期用于投资判断时遗漏了什么。", "静态回收期只说明收回初始投资所需的时间，不考虑现金流量的时间价值，也不计入回收期后的现金流量，不能单独据此判断项目价值。"),
                "营运资本管理—经济订货量": ("说明经济订货量所对应的管理含义。", "该订货批量在题设需求量、订货成本和储存成本条件下，使相关订货成本与储存成本之和达到最低；实际执行仍需结合供应约束和采购批量政策。"),
                "营运资本管理—再订货点": ("说明库存降至该水平时应采取的行动。", "现有库存降至再订货点时应发出订单；提前期内的预计耗用量与安全库存共同决定该点，安全库存用于缓冲需求和交货波动。"),
                "本量利分析—盈亏临界点销售量": ("说明实际销量相对盈亏临界点的位置如何影响经营结果。", "在线性假设和相关范围内，销量低于盈亏临界点发生亏损，高于盈亏临界点实现盈利。"),
                "本量利分析—目标利润销售量": ("解释为什么所需销量通常要向上取整。", "产品销量以整件实现，计算值若不是整数，向下取整将不足以达到目标利润，因此应向上取整。"),
                "全面预算—生产预算": ("分析期末产成品目标库存变化对预算生产量的影响。", "在预计销售量和期初库存不变时，期末产成品目标库存每增加1件，预算生产量相应增加1件。"),
                "全面预算—直接材料采购预算": ("分析期末材料目标库存变化对预算采购量的影响。", "在计划生产量、单位产品材料耗用量及期初材料库存不变时，期末材料目标库存每增加1千克，预算采购量增加1千克。"),
                "责任会计—剩余收益": ("将计算出的剩余收益与零比较并解释其含义。", "剩余收益大于零表示税前经营利润超过按最低投资报酬率要求的最低报酬；小于零表示未达到该要求。"),
                "责任会计—投资报酬率": ("说明该指标为何可能妨碍投资中心接受有利项目。", "若新项目报酬率高于资本成本但低于投资中心现有投资报酬率，接受项目可能拉低考核比率，经理可能因此拒绝能增加企业价值的项目。"),
                "业绩评价—经济增加值": ("将经济增加值与零比较并解释其含义。", "经济增加值大于零表示税后经营利润超过全部投入资本的资本成本；小于零表示未覆盖资本成本。"),
            }
            second_prompt, second_answer = case_advice_by_topic[calc["topic"]]
            q = {"id": f"fm-{cid}-{len(questions)+1:05d}", "chapterId": cid, "chapterTitle": meta["title"],
                 "topic": calc["topic"], "type": "case", "difficulty": calc["difficulty"], "sourceType": "original",
                 "source": calc["source"], "year": None, "page": None,
                 "material": f"{meta['title']}案例：{calc['stem']}",
                 "questions": [{"prompt": "计算题干要求的指标，并写出主要计算步骤。", "answer": f"{calc['numericAnswer']} {calc['unit']}",
                                "numericAnswer": calc["numericAnswer"], "unit": calc["unit"], "points": [calc["explanation"]]},
                               {"prompt": second_prompt, "answer": second_answer,
                                "points": [second_answer]}],
                 "explanation": calc["explanation"], "tags": [calc["topic"]]}
            if authored_cases:
                retired_ids.append(q["id"])
                q = authored_cases[n].copy()
                q.update({"chapterId": cid, "chapterTitle": meta["title"]})
            questions.append(q)
        authored_choices = []
        if chapter_num == 2:
            from curated_ch02_choices import chapter_two_choices
            from curated_ch02_cases import chapter_two_cases
            from curated_ch02_more import chapter_two_more_choices
            authored_choices = chapter_two_choices() + chapter_two_more_choices() + chapter_two_cases()
        elif chapter_num == 3:
            from curated_ch03_choices import chapter_three_choices
            authored_choices = chapter_three_choices()
        elif chapter_num == 9:
            from curated_ch09_choices import chapter_nine_choices
            authored_choices = chapter_nine_choices()
        elif chapter_num == 10:
            from curated_ch10_choices import chapter_ten_choices
            authored_choices = chapter_ten_choices()
        elif chapter_num == 13:
            from curated_ch13_choices import chapter_thirteen_choices
            authored_choices = chapter_thirteen_choices()
        elif chapter_num == 15:
            from curated_ch15_choices import chapter_fifteen_choices
            authored_choices = chapter_fifteen_choices()
        elif chapter_num == 19:
            from curated_ch19_choices import chapter_nineteen_choices
            authored_choices = chapter_nineteen_choices()
        elif chapter_num == 20:
            from curated_ch20_choices import chapter_twenty_choices
            authored_choices = chapter_twenty_choices()
        concept_count = target - len(questions)
        for n in range(concept_count):
            # With all public items freshly written, some chapters need a wider search
            # across the fact/frame/context combinations before a unique stem is found.
            for attempt in range(10000):
                q = make_original_concept(cid, info, rng, n + attempt * 7919)
                signature = normalize(q["stem"])
                if signature not in used_all_prompts:
                    used_all_prompts.add(signature)
                    break
            else:
                raise ValueError(f"第{cid}章原创概念题无法构造唯一题干")
            if n < len(authored_choices):
                q = authored_choices[n].copy()
                authored_signature = normalize(q.get("stem") or q.get("material", ""))
                if authored_signature in used_all_prompts:
                    raise ValueError(f"重复手写题干：{q['id']}")
                used_all_prompts.add(authored_signature)
            q.update({"id": f"fm-{cid}-{len(questions)+1:05d}", "chapterId": cid, "chapterTitle": meta["title"],
                      "year": None, "page": None})
            if n < len(authored_choices):
                retired_ids.append(q["id"])
                q["id"] = authored_choices[n]["id"]
            questions.append(q)
        if chapter_num in {2, 3, 10, 13, 15, 19, 20}:
            # Alternate the newly authored numerical and judgment tasks so a
            # chapter session does not begin with a long run of one format.
            numerical = [q for q in questions if q.get("authoringMethod") == "manual" and q["type"] == "calculation"]
            choices = [q for q in questions if q.get("authoringMethod") == "manual" and q["type"] == "single"]
            cases = [q for q in questions if q.get("authoringMethod") == "manual" and q["type"] == "case"]
            remainder = [q for q in questions if q.get("authoringMethod") != "manual"]
            mixed = []
            for index in range(max(len(numerical), len(choices), len(cases))):
                if index < len(numerical): mixed.append(numerical[index])
                if index < len(choices): mixed.append(choices[index])
                if index < len(cases): mixed.append(cases[index])
            questions = mixed + remainder
        # Fill chapter/topic page references where a phrase can be confirmed in the paired PDF.
        # Fail fast on repeated prompts rather than disguising them with a sequence suffix.
        seen: Counter[str] = Counter()
        for q in questions:
            q["abilityLevel"] = 3 if q["type"] == "case" or q["difficulty"] == "冲刺" else 2 if q["difficulty"] == "进阶" else 1
            q.update(normalize_math_glyphs(q))
            signature = normalize(q.get("stem", q.get("material", "")))
            seen[signature] += 1
            if seen[signature] > 1:
                raise ValueError(f"重复题干：{q['id']} {q.get('stem') or q.get('material')}")
        OUT.mkdir(parents=True, exist_ok=True)
        path = OUT / f"chapter-{cid}.json"
        path.write_text(json.dumps({"chapterId": cid, "questions": questions}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        all_chapters.append({"id": cid, "title": meta["title"], "count": len(questions), "file": path.name,
                             "importance": round(len(questions) / 15000, 4),
                             "metrics": meta})
        flat_index.extend(questions)
    if sum(ch["count"] for ch in all_chapters) != 15000:
        raise ValueError(f"题目总数不等于15000：{sum(ch['count'] for ch in all_chapters)}")
    manifest = {"version": "2026.10.26-v4", "total": 15000,
                "methodology": "每章保底100题，剩余题量按50%讲义重点标注、30%近年真题频次、20%考点广度评分分配；最大余数法取整。新增题参考2026年中注协大纲的理解、应用和综合运用能力等级设计。",
                "syllabus": {"title": "2026年注册会计师全国统一考试大纲（专业阶段）", "url": "https://www.cicpa.org.cn/xxfb/tzgg/202603/W020260304555799366109.pdf", "competencyLevels": {"1": "知识理解能力", "2": "基本应用能力", "3": "综合运用能力"}},
                "chapters": all_chapters, "retiredIds": retired_ids,
                "sourcePolicy": "课程资料仅用于章节、考点和重要度分析；公开题目均依据考点原创编写，不复刻讲义原题。",
                "quality": {"questionCount": len(flat_index), "sourceQuestions": sum(q["sourceType"] != "original" for q in flat_index)}}
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated {len(flat_index)} questions across {len(all_chapters)} chapters.")


if __name__ == "__main__":
    main()

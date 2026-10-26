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
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

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


def largest_remainder(chapters: dict[str, list[dict]], total: int = 10000) -> dict[str, int]:
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


def calc_question(chapter: int, rng: random.Random) -> dict:
    """Generate a numerical CPA-style exercise with computed result and a visible formula trail."""
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
        stem = f"现存入银行{money}万元，年利率为{rate:.0%}，按年复利计息。{years}年后的本利和为多少万元？"
        formula = f"复利终值=P×(1+i)^n={money}×(1+{rate:.0%})^{years}={ans:.2f}万元。"
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
        pvf = [1 / (1 + rate) ** t for t in (1, 2, 3)]
        ans = -investment + cf * sum(pvf)
        topic = "投资项目资本预算—净现值"
        stem = f"项目初始投资{investment}万元，预计未来3年每年年末产生现金净流量{cf:.0f}万元，折现率10%。净现值为多少万元？"
        formula = f"NPV=−{investment}+{cf:.0f}/1.1+{cf:.0f}/1.1²+{cf:.0f}/1.1³={ans:.2f}万元。"
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
        stem = f"股票现价{ s }元，执行价格{strike:.0f}元；一期后股价可能上涨25%或下跌20%，无风险利率为5%。按风险中性定价，欧式看涨期权现值为多少元？"
        formula = f"风险中性概率p=[(1+5%)−0.80]/(1.25−0.80)={p:.4f}；Cu={cu:.2f}，Cd={cd:.2f}；期权价值=[pCu+(1−p)Cd]/1.05={ans:.2f}元。"
        unit = "元"
    elif chapter == 7:
        fcfe = rng.randint(80, 1200)
        growth, required = rng.randrange(0, 61, 1) / 1000, rng.randrange(7, 16) / 100
        if required <= growth:
            required = growth + 0.04
        ans = fcfe * (1 + growth) / (required - growth)
        topic = "企业价值评估—股权现金流量折现模型"
        stem = f"某公司预计下一年股权现金流量为{fcfe:.2f}万元，此后按3%永续增长，股权资本成本为9%。股权价值为多少万元？"
        formula = f"股权价值=FCFE₁/(r_s−g)={fcfe:.2f}/(9%−3%)={ans:.2f}万元。"
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
        stem = f"面值{face:,.0f}元、票面利率{coupon:.0%}、每年付息一次、期限{n}年的债券，市场必要报酬率为{ytm:.0%}。债券价值为多少元？"
        formula = f"债券价值=Σ[票面利息/(1+r)^t]+面值/(1+r)^n={ans:,.2f}元。"
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
        if 20 <= len(fact) <= 190 and "|" not in fact and is_declarative_fact(fact) and not re.search(r"(?:例题|教材例题|题目|答案|解析|表格|计算结果如下|如下表|试卷Ⅰ|试卷Ⅱ|选项[A-D])", fact):
            fact = re.sub(r"^[A-D][.．、]\s*", "", fact)
            if re.match(r"^[A-D][.．、]", fact):
                continue
            facts.append({"text": fact, "section": row.get("section", "本章核心考点")})
    facts = list({x["text"]: x for x in facts}.values())
    if not facts:
        facts = [{"text": f"本章财务管理知识应结合具体条件分析，不能脱离题目给定的数据和假设。", "section": info["meta"]["title"]}]
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
    answers = [o["key"] for o, (_, wrong) in zip(options, options_raw) if wrong]
    perspectives = ["按定义理解", "结合适用条件", "从因果关系看", "对照讲义结论", "从指标口径看", "结合决策用途", "从计算关系看", "按本节要点判断"]
    frames = ["下列哪项表述颠倒了原意？", "下列判断中不符合讲义表述的是？", "下列选项中存在概念性错误的是？", "哪项把该考点的关系说反了？",
              "下列关于这一考点的表述错误的是？", "哪项与资料给出的结论相矛盾？", "下列表述中应予以排除的是？", "哪项不是该考点的准确表述？"]
    context_pool = [x["text"] for x in facts if x["section"] == target["section"] and x["text"] != target["text"]]
    if len(context_pool) < 2:
        context_pool = [x["text"] for x in facts if x["text"] != target["text"]]
    context_period = max(1, len(invertible) * len(frames))
    context_fact = context_pool[(serial // context_period) % len(context_pool)] if context_pool else "题目给定的条件应结合适用公式分析。"
    stem = f"讲义还指出：“{context_fact}”。{perspectives[serial // max(1, len(invertible)) % len(perspectives)]}，围绕「{target['section']}」中的观点“{target['text']}”，{frames[serial % len(frames)]}{'（多选）' if len(answers) > 1 else '（单选）'}"
    explanation = f"讲义对应考点的准确表述为：{target['text']}。错误选项{ '、'.join(answers) }{ '；'.join(reasons) }。"
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
    used_source_prompts: set[str] = set()
    used_all_prompts: set[str] = set()
    for cid in sorted(chapters, key=int):
        info = chapters[cid]
        chapter_num = int(cid)
        meta = info["meta"]
        questions: list[dict] = []
        for source_no, item in enumerate(info["sourceQuestions"]):
            options = item["options"][:4]
            if len(options) != 4 or len(item["answer"]) not in (1, 2, 3):
                continue
            prompt_signature = normalize(item["prompt"])
            if prompt_signature in used_source_prompts:
                continue
            # This 2025 bond-yield spread item tests credit/liquidity risk in capital cost,
            # so keep it in chapter 4 when it also appears in the chapter 3 source file.
            if chapter_num == 3 and "到期收益率" in item["prompt"] and "利率差" in item["prompt"]:
                continue
            used_source_prompts.add(prompt_signature)
            used_all_prompts.add(prompt_signature)
            qtype = "multiple" if len(item["answer"]) > 1 else "single"
            source_label = (f"{item['year']}年CPA财务成本管理考试题（讲义收录）" if item.get("year") else "闫华红《轻1·基础细讲班》教材例题")
            explanation = item.get("explanation") or f"参考答案为{'、'.join(item['answer'])}。请结合{item['topic']}的定义、适用条件和题干信息逐项核对。"
            q = {"id": f"fm-{cid}-{len(questions)+1:05d}", "chapterId": cid, "chapterTitle": meta["title"],
                 "topic": item["topic"], "type": qtype, "difficulty": "进阶", "sourceType": item["sourceType"],
                 "source": source_label, "year": item.get("year"), "page": item.get("page"), "stem": item["prompt"],
                 "options": options, "answer": item["answer"], "explanation": explanation,
                 "tags": [item["topic"]]}
            questions.append(q)
        target = quotas[cid]
        remaining = target - len(questions)
        rng = random.Random(260826 + chapter_num)
        calc_share = 0.42 if chapter_num > 1 else 0.0
        calc_count = min(remaining, round(remaining * calc_share))
        case_count = round(calc_count * 0.08) if chapter_num in {5, 11, 16, 18, 19, 20} else 0
        calc_count -= case_count
        for n in range(calc_count):
            q = next_unique_calculation(chapter_num, rng, used_all_prompts)
            q.update({"id": f"fm-{cid}-{len(questions)+1:05d}", "chapterId": cid, "chapterTitle": meta["title"],
                      "year": None, "page": None})
            questions.append(q)
        for n in range(case_count):
            calc = next_unique_calculation(chapter_num, rng, used_all_prompts)
            q = {"id": f"fm-{cid}-{len(questions)+1:05d}", "chapterId": cid, "chapterTitle": meta["title"],
                 "topic": calc["topic"], "type": "case", "difficulty": calc["difficulty"], "sourceType": "original",
                 "source": calc["source"], "year": None, "page": None,
                 "material": f"{meta['title']}案例：{calc['stem']}",
                 "questions": [{"prompt": "计算题干要求的指标，并写出主要计算步骤。", "answer": f"{calc['numericAnswer']} {calc['unit']}",
                                "numericAnswer": calc["numericAnswer"], "unit": calc["unit"], "points": [calc["explanation"]]},
                               {"prompt": "根据计算结果说明本题对应的管理或决策含义。", "answer": "按题干设定的评价口径，将计算结果与相应基准或备选方案比较后作出判断。",
                                "points": ["明确使用题干给定的比较基准", "结论与计算结果方向一致"]}],
                 "explanation": calc["explanation"], "tags": [calc["topic"]]}
            questions.append(q)
        concept_count = target - len(questions)
        for n in range(concept_count):
            for attempt in range(100):
                q = make_original_concept(cid, info, rng, n + attempt * max(1, len(info["topics"])))
                signature = normalize(q["stem"])
                if signature not in used_all_prompts:
                    used_all_prompts.add(signature)
                    break
            else:
                raise ValueError(f"第{cid}章原创概念题无法构造唯一题干")
            q.update({"id": f"fm-{cid}-{len(questions)+1:05d}", "chapterId": cid, "chapterTitle": meta["title"],
                      "year": None, "page": None})
            questions.append(q)
        # Fill chapter/topic page references where a phrase can be confirmed in the paired PDF.
        # Fail fast on repeated prompts rather than disguising them with a sequence suffix.
        seen: Counter[str] = Counter()
        for q in questions:
            signature = normalize(q.get("stem", q.get("material", "")))
            seen[signature] += 1
            if seen[signature] > 1:
                raise ValueError(f"重复题干：{q['id']} {q.get('stem') or q.get('material')}")
        OUT.mkdir(parents=True, exist_ok=True)
        path = OUT / f"chapter-{cid}.json"
        path.write_text(json.dumps({"chapterId": cid, "questions": questions}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        all_chapters.append({"id": cid, "title": meta["title"], "count": len(questions), "file": path.name,
                             "importance": round(len(questions) / 10000, 4),
                             "metrics": meta})
        flat_index.extend(questions)
    if sum(ch["count"] for ch in all_chapters) != 10000:
        raise ValueError(f"题目总数不等于10000：{sum(ch['count'] for ch in all_chapters)}")
    manifest = {"version": "2026.10.26-v1", "total": 10000,
                "methodology": "每章保底100题，剩余题量按50%讲义重点标注、30%近年真题频次、20%考点广度评分分配；最大余数法取整。",
                "chapters": all_chapters,
                "sourcePolicy": "资料中的教材例题与讲义收录的历年真题优先；其他题目为标注来源考点的原创题。",
                "quality": {"questionCount": len(flat_index), "sourceQuestions": sum(q["sourceType"] != "original" for q in flat_index)}}
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    create_review_workbook(manifest, flat_index)
    print(f"Generated {len(flat_index)} questions across {len(all_chapters)} chapters; review workbook created.")


if __name__ == "__main__":
    main()

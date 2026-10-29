# 知财｜CPA 财务成本管理

CPA 财务成本管理 20 章练习站，题库总量固定为 15,000 题。使用用户提供的轻1基础细讲班 Word 笔记版提取章节结构、考点、重要度与真题频次指标，并以配套 PDF 交叉核对；课程资料只作分析依据，公开题目均为按考点原创编写，不复刻讲义原题。题目参考中注协 2026 年考试大纲的理解、应用和综合运用能力层级。

**内容审查状态：未通过。** 现有题目中大量概念题沿用同一拼接模板；题干无完全重复不代表练习任务不同。`scripts/audit_question_quality.py --enforce` 会对数字替换、相同选项与答案、同一讲解目标等情况生成 `review/content-quality-audit.json`，并在未清理完模板题时以非零状态退出。第 2 章的 22 道计算题、36 道选择题和 8 道案例，第 9 章的 15 道计算题和 12 道选择题，第 19 章的 20 道计算题和 15 道选择题，第 20 章的 15 道计算题、8 道案例和 12 道选择题已由手写题替换，其余内容仍需逐章修订和复核。不要将结构校验通过解释为题目质量达标。

## 本地构建

需要 Python 3.12、`pypdf`、Node.js 和 `@oai/artifact-tool`：

```powershell
python scripts/build_bank.py
python scripts/audit_question_quality.py
node scripts/build_review_workbook.mjs
python scripts/validate_bank.py
python scripts/verify_visible_calculations.py
python scripts/build_static.py
```

发布前运行 `python scripts/audit_question_quality.py --enforce`；非零退出表示尚有待处理内容。审阅工作簿中的相同选项和相同考点分组仅为候选，需逐项核对，不能直接当成已确认重复。

`build_bank.py` 会从桌面资料目录读取笔记版 Word/PDF 压缩包并输出 20 个分章 JSON 文件；`build_review_workbook.mjs` 生成 `review/cpa-financial-management-question-review.xlsx`。原始讲义不复制到站点目录。生成章节配额：每章先分配 100 题，剩余题量按讲义重点标注 50%、近年真题频次 30%、考点广度 20%加权，并用最大余数法取整。

浏览器预览可用：

```powershell
python -m http.server 4173 --directory dist
```

打开 `http://127.0.0.1:4173/`。

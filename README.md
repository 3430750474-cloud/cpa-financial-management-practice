# 知财｜CPA 财务成本管理

CPA 财务成本管理 20 章练习站，题库总量固定为 15,000 题。使用用户提供的轻1基础细讲班 Word 笔记版提取章节结构、考点、重要度与真题频次指标，并以配套 PDF 交叉核对；课程资料只作分析依据，公开题目均为按考点原创编写，不复刻讲义原题。题目参考中注协 2026 年考试大纲的理解、应用和综合运用能力层级。

## 本地构建

需要 Python 3.12、`pypdf`、Node.js 和 `@oai/artifact-tool`：

```powershell
python scripts/build_bank.py
node scripts/build_review_workbook.mjs
python scripts/validate_bank.py
python scripts/build_static.py
```

`build_bank.py` 会从桌面资料目录读取笔记版 Word/PDF 压缩包并输出 20 个分章 JSON 文件；`build_review_workbook.mjs` 生成 `review/cpa-financial-management-question-review.xlsx`。原始讲义不复制到站点目录。生成章节配额：每章先分配 100 题，剩余题量按讲义重点标注 50%、近年真题频次 30%、考点广度 20%加权，并用最大余数法取整。

浏览器预览可用：

```powershell
python -m http.server 4173 --directory dist
```

打开 `http://127.0.0.1:4173/`。

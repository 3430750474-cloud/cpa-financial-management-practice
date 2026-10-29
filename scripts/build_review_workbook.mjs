import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = path.resolve(process.argv[2] || path.join(import.meta.dirname, ".."));
const dataDir = path.join(root, "dist", "data");
const reviewPath = path.join(root, "review", "cpa-financial-management-question-review.xlsx");
const manifest = JSON.parse(await fs.readFile(path.join(dataDir, "manifest.json"), "utf8"));
const questions = [];
const stats = new Map();
for (const chapter of manifest.chapters) {
  const bank = JSON.parse(await fs.readFile(path.join(dataDir, chapter.file), "utf8")).questions;
  const entry = { chapter, questions: bank, types: {}, sources: {} };
  for (const q of bank) {
    questions.push(q);
    entry.types[q.type] = (entry.types[q.type] || 0) + 1;
    entry.sources[q.sourceType] = (entry.sources[q.sourceType] || 0) + 1;
  }
  stats.set(chapter.id, entry);
}

const workbook = Workbook.create();
const summary = workbook.worksheets.add("章节配额");
const detail = workbook.worksheets.add("逐题核验");
const near = workbook.worksheets.add("近似重复候选");
const semantic = workbook.worksheets.add("选项及考点待审");
const summaryRows = [["章节", "计划题量", "实际题量", "重点标注信号", "真题频次指标", "考点广度", "单选", "多选", "计算", "综合", "原创"]];
for (const { chapter, types, sources, questions: bank } of stats.values()) {
  const meta = chapter.metrics;
  summaryRows.push([chapter.title, chapter.count, bank.length, meta.importanceSignals, meta.examFrequency, meta.topicBreadth,
    types.single || 0, types.multiple || 0, types.calculation || 0, types.case || 0, sources.original || 0]);
}
summaryRows.push(["合计", manifest.total, questions.length, null, null, null,
  ...["single", "multiple", "calculation", "case", "original"].map(key => questions.filter(q => key === "original" ? q.sourceType === key : q.type === key).length)]);
summary.getRangeByIndexes(0, 0, summaryRows.length, summaryRows[0].length).values = summaryRows;

const detailRows = [["题目ID", "章节", "考点", "题型", "难度", "能力等级", "来源类型", "来源", "年份", "页码", "题干/案例材料", "选项", "答案", "数值答案", "单位", "解析/步骤", "标签"]];
for (const q of questions) detailRows.push([
  q.id, q.chapterTitle, q.topic, q.type, q.difficulty, q.abilityLevel || "", q.sourceType, q.source, q.year || "", q.page || "",
  q.stem || q.material || "", JSON.stringify(q.options || [], null, 0), (q.answer || []).join("、"),
  q.numericAnswer ?? "", q.unit || "", q.type === "case"
    ? (q.questions || []).map((s, i) => `小问${i + 1}：${s.prompt}\n参考答案：${s.answer}\n评分要点：${(s.points || []).join("；")}`).join("\n\n")
    : q.explanation || "",
  (q.tags || []).join("；")
]);
detail.getRangeByIndexes(0, 0, detailRows.length, detailRows[0].length).values = detailRows;

const normalizeSkeleton = (text) => text
  .replace(/\d+(?:[,.，．]\d+)*(?:%|％)?/g, "<N>")
  .replace(/[甲乙丙丁]公司|某公司|某企业|某产品/g, "<CO>")
  .replace(/[\s，。；：、！？（）()“”‘’\-—×÷=+/%]/g, "");
const groups = new Map();
for (const q of questions) {
  const skeleton = normalizeSkeleton(q.stem || q.material || "");
  if (skeleton.length < 28) continue;
  const key = `${q.chapterId}|${q.type}|${skeleton}`;
  if (!groups.has(key)) groups.set(key, { chapter: q.chapterTitle, type: q.type, skeleton, ids: [] });
  groups.get(key).ids.push(q.id);
}
const nearRows = [["章节", "题型", "候选数量", "题目ID", "遮蔽数值后的题干骨架", "审阅说明"]];
for (const group of [...groups.values()].filter(g => g.ids.length > 1).sort((a, b) => b.ids.length - a.ids.length))
  nearRows.push([group.chapter, group.type, group.ids.length, group.ids.join("、"), group.skeleton.slice(0, 500), "数字或主体变体的自动候选；需按题意核验是否仅为参数替换"]);
near.getRangeByIndexes(0, 0, nearRows.length, nearRows[0].length).values = nearRows;

// These groups are review candidates, not an assertion that every item is a duplicate.
// Reading the same report as the release gate keeps the workbook in sync with the audit.
const audit = JSON.parse(await fs.readFile(path.join(root, "review", "content-quality-audit.json"), "utf8"));
if (audit.total !== questions.length || audit.version !== manifest.version) throw new Error("Quality audit does not match this bank");
const byId = new Map(questions.map(q => [q.id, q]));
const semanticRows = [["候选类型", "章节", "数量", "题目ID", "代表题干", "判定与处置"]];
for (const [key, label] of [["same_options_and_answer", "选项与答案相同"], ["same_teaching_target", "同一讲解考点"], ["cross_chapter_number_masked_stem", "跨章数值变体"], ["cross_chapter_same_options_and_answer", "跨章选项答案相同"], ["cross_chapter_same_numeric_inputs_and_answer", "跨章数值答案相同"]]) {
  for (const group of audit.checks[key].details) {
    const representative = byId.get(group.ids[0]);
    if (!representative || group.ids.some(id => !byId.has(id))) throw new Error(`Stale quality audit group ${group.fingerprint}`);
    const titles = [...new Set(group.ids.map(id => byId.get(id).chapterTitle))].join("、");
    semanticRows.push([label, titles, group.size, group.ids.join("、"), representative.stem || representative.material || "", "待逐项审阅：核对条件、任务与解法，重复题需替换；相同考点或数值本身不等于重复"]);
  }
}
semantic.getRangeByIndexes(0, 0, semanticRows.length, semanticRows[0].length).values = semanticRows;

for (const sheet of [summary, detail, near, semantic]) {
  sheet.showGridLines = false;
  sheet.freezePanes.freezeRows(1);
  const used = sheet.getUsedRange();
  used.format.wrapText = true;
  used.format.verticalAlignment = "top";
  const header = sheet.getRangeByIndexes(0, 0, 1, detailRows[0].length);
  header.format.fill = "#174F3B";
  header.format.font = { bold: true, color: "#FFFFFF" };
  header.format.rowHeight = 30;
}
summary.getRange("A:A").format.columnWidth = 34;
summary.getRange("B:K").format.columnWidth = 14;
for (const [column, width] of [["A:A", 18], ["B:B", 34], ["C:C", 28], ["D:G", 16], ["H:H", 46], ["I:I", 12], ["J:J", 10], ["K:K", 58], ["L:L", 54], ["M:M", 12], ["N:N", 16], ["O:O", 12], ["P:P", 72], ["Q:Q", 35]]) detail.getRange(column).format.columnWidth = width;
detail.getRange(`A2:Q${detailRows.length}`).format.rowHeight = 48;
for (let i = 0; i < questions.length; i++) {
  if (questions[i].type === "case") detail.getRange(`A${i + 2}:Q${i + 2}`).format.rowHeight = 180;
}
for (const [column, width] of [["A:A", 34], ["B:B", 16], ["C:C", 14], ["D:D", 62], ["E:E", 72], ["F:F", 54]]) near.getRange(column).format.columnWidth = width;
near.getRange(`A2:F${nearRows.length}`).format.rowHeight = 42;
for (const [column, width] of [["A:A", 24], ["B:B", 34], ["C:C", 14], ["D:D", 62], ["E:E", 72], ["F:F", 54]]) semantic.getRange(column).format.columnWidth = width;
semantic.getRange(`A2:F${semanticRows.length}`).format.rowHeight = 42;
await workbook.recalculate();
const previewDir = path.join(process.env.TEMP || ".", "zhicai-workbook-previews");
await fs.mkdir(previewDir, { recursive: true });
const firstCaseRow = questions.findIndex(q => q.type === "case") + 2;
for (const [sheetName, range, fileName] of [
  ["章节配额", "A1:K22", "summary.png"],
  ["逐题核验", "A1:Q6", "detail.png"],
  ["近似重复候选", "A1:F10", "near-duplicates.png"],
  ["选项及考点待审", "A1:F10", "semantic-candidates.png"],
  ["逐题核验", `J${firstCaseRow}:Q${firstCaseRow}`, "case-detail.png"],
]) {
  const preview = await workbook.render({ sheetName, range, scale: 1 });
  await fs.writeFile(path.join(previewDir, fileName), Buffer.from(await preview.arrayBuffer()));
}
await fs.mkdir(path.dirname(reviewPath), { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(reviewPath);
console.log(JSON.stringify({ workbook: reviewPath, questions: questions.length, chapters: manifest.chapters.length, summaryRows: summaryRows.length - 1, detailRows: detailRows.length - 1, nearDuplicateGroups: nearRows.length - 1, semanticCandidates: semanticRows.length - 1 }));

const main = document.querySelector("#main");
const toast = document.querySelector("#toast");
const STORE = "zhicai-cpa-financial-management-v1";
const empty = { answered: {}, favorites: [], last: null, dark: false };
let manifest;
let retiredIds = new Set();
let bank = [];
let view = { page: "home", chapter: null, index: 0, mode: "all", type: "all", source: "all", difficulty: "all", search: "" };
let state = loadState();
function loadState() { try { return { ...empty, ...JSON.parse(localStorage.getItem(STORE) || "{}") }; } catch { return { ...empty }; } }
function saveState() { localStorage.setItem(STORE, JSON.stringify(state)); }
function esc(v) { return String(v ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }
function toastMsg(msg) { toast.textContent = msg; toast.classList.add("show"); setTimeout(() => toast.classList.remove("show"), 1800); }
function typeName(type) { return ({ single: "单选题", multiple: "多选题", calculation: "计算题", case: "综合案例" })[type] || type; }
function levelName(level) { return ({ 1: "理解", 2: "应用", 3: "综合" })[level] || "应用"; }
function sourceName() { return "原创题"; }
function currentAnswers() { return Object.entries(state.answered).filter(([id]) => !retiredIds.has(id)); }
function allAnswered() { return currentAnswers().length; }
function correctCount() { return currentAnswers().filter(([, x]) => x.correct || x.rating === "mastered").length; }
function overallRate() { return allAnswered() ? Math.round(correctCount() / allAnswered() * 100) : 0; }
function chapterProgress(chapterId) {
  if (chapterId === "all") return { done: allAnswered(), rate: overallRate() };
  const prefix = `fm-${chapterId}-`;
  const items = currentAnswers().filter(([id]) => id.startsWith(prefix)).map(([, a]) => a);
  const correct = items.filter(a => a.correct || a.rating === "mastered").length;
  return { done: items.length, rate: items.length ? Math.round(correct / items.length * 100) : 0 };
}
function home() {
  view.page = "home";
  const done = allAnswered();
  const percent = Math.min(100, Math.round(done / manifest.total * 100));
  main.innerHTML = `<div class="shell">
    <section class="hero"><div class="hero-main"><div class="eyebrow">2026 · CPA FINANCIAL MANAGEMENT</div><h1>把计算，练成决策力。</h1><p>20 章、15,000 道训练题。覆盖财务分析、价值评估、资本预算、成本管理与业绩评价，练熟公式、判断和综合应用。</p><div class="hero-stats"><div><strong>${manifest.total.toLocaleString()}</strong><span>训练题目</span></div><div><strong>${done.toLocaleString()}</strong><span>已完成</span></div><div><strong>${overallRate()}%</strong><span>当前掌握率</span></div></div></div>
      <aside class="resume-card"><div><div class="ring" style="--p:${percent}" data-label="${percent}%"></div><h2>${state.last ? "继续上次学习" : "开始你的第一题"}</h2><p>${state.last ? esc(manifest.chapters.find(c => c.id === state.last.chapterId)?.title || "") : "答题进度保存在当前浏览器。"}</p></div><button class="primary" id="resume">${state.last ? "继续练习" : "从第一章开始"}</button></aside></section>
    <section class="global-search"><div class="section-head"><div><h2>全题库检索</h2><p>跨 20 章搜索题干、材料、选项、考点与解析</p></div></div><div class="search-bar"><input id="globalSearch" type="search" placeholder="搜索关键词，例如：资本成本、净现值、营运资本"><select id="globalChapter"><option value="all">全部章节</option>${manifest.chapters.map(c => `<option value="${c.id}">${esc(c.title)}</option>`).join("")}</select><select id="globalType"><option value="all">全部题型</option><option value="single">单选</option><option value="multiple">多选</option><option value="calculation">计算</option><option value="case">综合</option></select><select id="globalDifficulty"><option value="all">全部难度</option><option>基础</option><option>进阶</option><option>冲刺</option></select><select id="globalSource"><option value="all">全部来源</option><option value="original">原创题</option></select><button id="doGlobalSearch" class="primary">搜索全库</button></div><div id="globalResults" class="global-results" aria-live="polite"></div></section>
    <section><div class="section-head"><div><h2>训练方式</h2><p>选择当前最需要的复习路径</p></div></div><div class="modes"><button class="mode-card" data-mode="all"><b>章节练习</b><span>按章节系统学习</span></button><button class="mode-card" data-mode="wrong"><b>错题重练</b><span>${currentAnswers().filter(([, x]) => x.correct === false || x.rating === "weak").length} 道待巩固</span></button><button class="mode-card" data-mode="favorite"><b>我的收藏</b><span>${state.favorites.filter(id => !retiredIds.has(id)).length} 道已收藏</span></button><button class="mode-card" data-mode="unanswered"><b>只看未做</b><span>${Math.max(0, manifest.total - done).toLocaleString()} 道未完成</span></button></div></section>
    <section><div class="section-head"><div><h2>章节目录</h2><p>题量按讲义重点、近年题型频次与考点广度分配</p></div><span class="section-total">20 个章节</span></div><div class="chapters">${manifest.chapters.map((c, i) => { const p = chapterProgress(c.id); return `<button class="chapter-card" data-chapter="${c.id}"><div class="chapter-top"><div><span class="chapter-no">CHAPTER ${String(i + 1).padStart(2, "0")}</span><h3>${esc(c.title.replace(/^第.+?章\s*/, ""))}</h3></div><b>${c.count.toLocaleString()}</b></div><div class="progress"><i style="width:${Math.min(100, Math.round(p.done / c.count * 100))}%"></i></div><div class="chapter-meta"><span>${p.done}/${c.count} 已完成</span><span>正确率 ${p.rate}%</span></div></button>`; }).join("")}</div></section>
    <footer class="site-note">题库参考用户提供的 CPA 财管讲义提取章节、考点与重要度，公开题目均按考点原创编写，并按 2026 年考试大纲能力等级组织。<a href="question-review.xlsx" download>下载 15,000 题审阅工作簿</a>。请以最新考试大纲和法规为准。</footer>
  </div>`;
  document.querySelector("#resume").onclick = () => state.last?.chapterId === "all" ? openReviewMode(state.last.mode, state.last.index || 0) : openChapter(state.last?.chapterId || "01", state.last?.mode || "all", state.last?.index || 0);
  document.querySelectorAll("[data-chapter]").forEach(b => b.onclick = () => openChapter(b.dataset.chapter));
  document.querySelectorAll("[data-mode]").forEach(b => b.onclick = () => openReviewMode(b.dataset.mode));
  document.querySelector("#doGlobalSearch").onclick = runGlobalSearch;
  document.querySelector("#globalSearch").onkeydown = e => { if (e.key === "Enter") runGlobalSearch(); };
}
async function runGlobalSearch() {
  const query = document.querySelector("#globalSearch").value.trim().toLowerCase();
  const target = document.querySelector("#globalResults");
  if (!query) { target.innerHTML = `<p class="search-hint">输入关键词开始搜索。</p>`; return; }
  target.innerHTML = `<p class="search-hint">正在检索 ${manifest.chapters.length} 章题库…</p>`;
  try {
    const chosenChapter = document.querySelector("#globalChapter").value;
    const chapters = chosenChapter === "all" ? manifest.chapters : manifest.chapters.filter(ch => ch.id === chosenChapter);
    const banks = await Promise.all(chapters.map(async ch => {
      const response = await fetch(`data/${ch.file}`);
      if (!response.ok) throw new Error(`第${ch.id}章加载失败`);
      return { chapter: ch, questions: (await response.json()).questions };
    }));
    const hits = [];
    for (const {chapter, questions} of banks) for (const q of questions) {
      const haystack = [q.stem, q.material, q.topic, q.explanation, ...(q.tags || []), ...(q.options || []).map(o => o.text), ...(q.questions || []).flatMap(s => [s.prompt, s.answer, ...(s.points || [])])].join(" ").toLowerCase();
      const at = haystack.indexOf(query);
      if (at >= 0 && (document.querySelector("#globalType").value === "all" || q.type === document.querySelector("#globalType").value)
          && (document.querySelector("#globalDifficulty").value === "all" || q.difficulty === document.querySelector("#globalDifficulty").value)
          && (document.querySelector("#globalSource").value === "all" || q.sourceType === document.querySelector("#globalSource").value))
        hits.push({chapter, q, excerpt: (q.stem || q.material || q.topic).replace(/\s+/g, " ").slice(0, 150)});
    }
    const shown = hits.slice(0, 100);
    target.innerHTML = `<div class="search-summary">找到 ${hits.length.toLocaleString()} 道，显示前 ${shown.length} 道</div>${shown.length ? `<div class="search-hit-list">${shown.map((x, i) => `<button class="search-hit" data-hit="${i}"><span>${esc(x.chapter.title)} · ${typeName(x.q.type)} · ${esc(x.q.topic)}</span><b>${esc(x.excerpt)}</b></button>`).join("")}</div>` : `<p class="search-hint">没有匹配题目。试试更短的关键词。</p>`}`;
    target.querySelectorAll("[data-hit]").forEach(button => button.onclick = async () => {
      const hit = shown[Number(button.dataset.hit)];
      await openChapter(hit.chapter.id);
      const pos = bank.findIndex(q => q.id === hit.q.id);
      view.index = Math.max(0, pos); renderPractice();
    });
  } catch (error) { target.innerHTML = `<p class="search-hint">检索失败：${esc(error.message)}。请刷新后重试。</p>`; }
}
async function openChapter(id, mode = "all", index = 0) {
  view = { ...view, page: "practice", chapterId: id, index, mode, type: "all", source: "all", difficulty: "all", search: "" };
  try {
    const resp = await fetch(`data/chapter-${id}.json`);
    if (!resp.ok) throw new Error("章节题目暂时无法加载");
    bank = (await resp.json()).questions;
    renderPractice();
  } catch (error) {
    main.innerHTML = `<div class="shell"><section class="question-card empty"><h2>题库加载失败</h2><p>${esc(error.message)}，请刷新页面后重试。</p><button class="secondary" id="back">返回章节目录</button></section></div>`;
    document.querySelector("#back").onclick = home;
  }
}
async function openReviewMode(mode, index = 0) {
  const questionIds = mode === "wrong"
    ? currentAnswers().filter(([, a]) => a.correct === false || a.rating === "weak").map(([id]) => id)
    : mode === "favorite" ? state.favorites.filter(id => !retiredIds.has(id)) : [];
  const chapterIds = mode === "unanswered" ? manifest.chapters.map(c => c.id) : [...new Set(questionIds.map(id => id.slice(3, 5)))];
  view = { ...view, page: "practice", chapterId: "all", index, mode, type: "all", source: "all", difficulty: "all", search: "" };
  try {
    const banks = await Promise.all(chapterIds.map(async id => {
      const resp = await fetch(`data/chapter-${id}.json`);
      if (!resp.ok) throw new Error(`第${id}章题目暂时无法加载`);
      return (await resp.json()).questions;
    }));
    bank = banks.flat();
    renderPractice();
  } catch (error) {
    main.innerHTML = `<div class="shell"><section class="question-card empty"><h2>题库加载失败</h2><p>${esc(error.message)}，请刷新页面后重试。</p><button class="secondary" id="back">返回章节目录</button></section></div>`;
    document.querySelector("#back").onclick = home;
  }
}
function filtered() {
  return bank.filter(q => {
    const a = state.answered[q.id];
    const wrong = a && (a.correct === false || a.rating === "weak");
    if (view.mode === "wrong" && !wrong) return false;
    if (view.mode === "favorite" && !state.favorites.includes(q.id)) return false;
    if (view.mode === "unanswered" && a) return false;
    if (view.type !== "all" && q.type !== view.type) return false;
    if (view.source !== "all" && q.sourceType !== view.source) return false;
    if (view.difficulty !== "all" && q.difficulty !== view.difficulty) return false;
    if (view.search && !`${q.stem || q.material || ""} ${q.material || ""} ${q.topic} ${q.explanation || ""} ${(q.tags || []).join(" ")} ${(q.options || []).map(o => o.text).join(" ")}`.toLowerCase().includes(view.search.toLowerCase())) return false;
    return true;
  });
}
function renderPractice() {
  const list = filtered();
  if (view.index >= list.length) view.index = Math.max(0, list.length - 1);
  const q = list[view.index];
  const chapter = manifest.chapters.find(c => c.id === view.chapterId) || { title: view.mode === "wrong" ? "全部章节 · 错题重练" : view.mode === "favorite" ? "全部章节 · 我的收藏" : "全部章节 · 只看未做" };
  const prefix = view.mode === "all" ? "章节练习" : ({ wrong: "错题重练", favorite: "我的收藏", unanswered: "只看未做" })[view.mode];
  main.innerHTML = `<div class="shell practice-layout"><aside class="sidebar"><button class="back" id="back">← 返回章节</button><h2>${esc(chapter.title)}</h2><p class="mode-label">${prefix}</p><div class="filters">
    <label>题型<select id="type"><option value="all">全部题型</option><option value="single">单选题</option><option value="multiple">多选题</option><option value="calculation">计算题</option><option value="case">综合案例</option></select></label>
    <label>来源<select id="source"><option value="all">全部来源</option><option value="original">原创题</option></select></label>
    <label>难度<select id="difficulty"><option value="all">全部难度</option><option value="基础">基础</option><option value="进阶">进阶</option><option value="冲刺">冲刺</option></select></label>
    <label>检索<input id="search" type="search" placeholder="题干或考点" value="${esc(view.search)}"></label></div>
    <div class="mini-stats"><div><b>${list.length}</b><span>当前题目</span></div><div><b>${chapterProgress(view.chapterId).rate}%</b><span>本章掌握率</span></div></div>
    <div class="answer-grid" aria-label="答题卡">${list.slice(0, 240).map((item, i) => { const a = state.answered[item.id]; const cl = [i === view.index ? "current" : "", a ? "done" : "", a && (a.correct === false || a.rating === "weak") ? "wrong" : ""].join(" "); return `<button class="${cl}" data-jump="${i}" aria-label="第${i + 1}题">${i + 1}</button>`; }).join("")}</div>${list.length > 240 ? `<p class="grid-note">答题卡显示前 240 题，可用筛选缩小范围。</p>` : ""}
    </aside><section class="practice-main">${q ? questionCard(q, list) : `<div class="question-card empty"><h2>这里还没有匹配题目</h2><p>调整筛选条件，或切换到章节练习。</p><button class="secondary" id="clearFilters">清除筛选</button></div>`}</section></div>`;
  document.querySelector("#back").onclick = home;
  for (const id of ["type", "source", "difficulty"]) { const el = document.querySelector(`#${id}`); el.value = view[id]; el.onchange = () => { view[id] = el.value; view.index = 0; renderPractice(); }; }
  document.querySelector("#search").oninput = e => { view.search = e.target.value; view.index = 0; renderPractice(); };
  document.querySelectorAll("[data-jump]").forEach(b => b.onclick = () => { view.index = Number(b.dataset.jump); renderPractice(); });
  if (!q) { document.querySelector("#clearFilters").onclick = () => { view.type = view.source = view.difficulty = "all"; view.search = ""; renderPractice(); }; return; }
  wireQuestion(q, list);
}
function questionCard(q, list) {
  const a = state.answered[q.id];
  const fav = state.favorites.includes(q.id);
  const origin = `<div class="question-meta"><span class="tag type">${typeName(q.type)}</span><span class="tag">${sourceName(q.sourceType)}</span><span class="tag">${esc(q.difficulty)}</span><span class="tag">能力等级 ${q.abilityLevel || 2} · ${levelName(q.abilityLevel || 2)}</span><span class="tag topic-tag">${esc(q.topic)}</span><span class="source">${esc(q.source)}${q.year ? ` · ${q.year}年` : ""}${q.page ? ` · 第${q.page}页` : ""}</span></div>`;
  let body = "";
  if (q.type === "case") body = caseBody(q, a);
  else if (q.type === "calculation") body = calculationBody(q, a);
  else body = choiceBody(q, a);
  return `<article class="question-card">${origin}<div class="question-counter">${view.index + 1} / ${list.length}</div>${q.stem ? `<h1 class="question-title">${esc(q.stem)}</h1>` : ""}${body}<div class="question-actions"><div><button class="nav-btn" id="prev" ${view.index === 0 ? "disabled" : ""}>上一题</button><button class="nav-btn" id="next" ${view.index === list.length - 1 ? "disabled" : ""}>下一题</button></div><div><button class="nav-btn favorite ${fav ? "active" : ""}" id="favorite">${fav ? "★ 已收藏" : "☆ 收藏"}</button></div></div></article>`;
}
function choiceBody(q, a) {
  const selected = a?.choice || [];
  return `<div class="answers">${q.options.map(o => { let cl = selected.includes(o.key) && !a ? "selected" : ""; if (a) { if (q.answer.includes(o.key)) cl = "correct"; else if (selected.includes(o.key)) cl = "incorrect"; } return `<button class="answer ${cl}" data-option="${esc(o.key)}" ${a ? "disabled" : ""}><span class="letter">${esc(o.key)}</span><span>${esc(o.text)}</span></button>`; }).join("")}</div>${a ? feedback(q, a.correct) : `<button class="primary" id="submit" disabled>提交答案</button>`}`;
}
function calculationBody(q, a) {
  return `<div class="calc-input"><label for="numeric">你的答案 <span>单位：${esc(q.unit || "按题干")} · 按题意保留两位小数</span></label><div class="calc-row"><input id="numeric" inputmode="decimal" placeholder="输入数值" ${a ? "disabled" : ""} value="${a ? esc(a.value) : ""}"><button class="primary" id="submit" ${a ? "disabled" : ""}>提交计算</button></div></div>${a ? feedback(q, a.correct, a.value) : ""}`;
}
function caseBody(q, a) {
  return `<div class="case-material">${esc(q.material)}</div>${q.questions.map((sq, i) => `<section class="case-question"><h3>${i + 1}. ${esc(sq.prompt)}</h3><textarea data-draft="${i}" rows="3" placeholder="写下计算过程、结论或判断依据" ${a ? "disabled" : ""}>${esc(state.caseDrafts?.[q.id]?.[i] || "")}</textarea>${a ? `<div class="feedback"><h3>参考答案</h3><p>${esc(sq.answer)}</p><b>评分要点</b><ul>${(sq.points || []).map(p => `<li>${esc(p)}</li>`).join("")}</ul></div>` : ""}</section>`).join("")}${a ? `<div class="feedback"><h3>自评掌握程度</h3><div class="self-rate">${[["mastered", "已掌握"], ["fuzzy", "还不熟"], ["weak", "未掌握"]].map(([k, v]) => `<button class="status-btn ${a.rating === k ? "active" : ""}" data-rate="${k}">${v}</button>`).join("")}</div></div>` : `<button class="primary" id="reveal">提交并查看参考答案</button>`}`;
}
function feedback(q, correct, value) {
  const answer = q.type === "calculation" ? `${q.numericAnswer} ${q.unit || ""}` : q.answer.join("、");
  return `<div class="feedback ${correct ? "" : "bad"}"><h3>${correct ? "回答正确" : "回看关键步骤"}</h3><p><b>参考答案：</b>${esc(answer)}</p>${value !== undefined && !correct ? `<p>你的答案：${esc(value)} ${esc(q.unit || "")}</p>` : ""}<p>${esc(q.explanation)}</p></div>`;
}
function wireQuestion(q, list) {
  let selected = [];
  document.querySelectorAll("[data-option]").forEach(b => b.onclick = () => {
    if (q.type === "single") { selected = [b.dataset.option]; document.querySelectorAll("[data-option]").forEach(x => x.classList.toggle("selected", x === b)); }
    else { const key = b.dataset.option; selected = selected.includes(key) ? selected.filter(x => x !== key) : [...selected, key]; b.classList.toggle("selected"); }
    document.querySelector("#submit").disabled = !selected.length;
  });
  document.querySelector("#submit")?.addEventListener("click", () => {
    let correct, result = {};
    if (q.type === "calculation") {
      const raw = String(document.querySelector("#numeric").value).replace(/[,，\s]/g, "");
      const value = Number(raw);
      if (!raw || !Number.isFinite(value)) { toastMsg("请输入有效数值"); return; }
      const target = Number(q.numericAnswer);
      correct = Math.abs(value - target) <= 0.005 + Number.EPSILON * Math.max(1, Math.abs(target)) * 4;
      result = { value: document.querySelector("#numeric").value };
    } else {
      correct = [...selected].sort().join("") === q.answer.slice().sort().join("");
      result = { choice: selected };
    }
    state.answered[q.id] = { ...result, correct, at: Date.now() };
    state.last = { chapterId: view.chapterId, index: view.index, mode: view.mode };
    saveState(); renderPractice();
  });
  document.querySelectorAll("[data-draft]").forEach(t => t.oninput = () => { state.caseDrafts ??= {}; state.caseDrafts[q.id] ??= {}; state.caseDrafts[q.id][t.dataset.draft] = t.value; saveState(); });
  document.querySelector("#reveal")?.addEventListener("click", () => { state.answered[q.id] = { rating: "fuzzy", at: Date.now() }; state.last = { chapterId: view.chapterId, index: view.index, mode: view.mode }; saveState(); renderPractice(); });
  document.querySelectorAll("[data-rate]").forEach(b => b.onclick = () => { state.answered[q.id] = { rating: b.dataset.rate, at: Date.now() }; saveState(); renderPractice(); });
  document.querySelector("#favorite").onclick = () => { state.favorites = state.favorites.includes(q.id) ? state.favorites.filter(id => id !== q.id) : [...state.favorites, q.id]; saveState(); renderPractice(); };
  document.querySelector("#prev").onclick = () => { view.index--; renderPractice(); };
  document.querySelector("#next").onclick = () => { view.index++; state.last = { chapterId: view.chapterId, index: view.index, mode: view.mode }; saveState(); renderPractice(); };
}
document.querySelector("#brand").onclick = home;
document.querySelector("#themeBtn").onclick = () => { state.dark = !state.dark; saveState(); document.body.classList.toggle("dark", state.dark); };
document.querySelector("#resetBtn").onclick = () => { if (confirm("确定清除全部答题进度、收藏和案例草稿吗？")) { const dark = state.dark; state = { ...empty, dark }; saveState(); home(); toastMsg("学习进度已重置"); } };
document.addEventListener("keydown", e => { if (view.page !== "practice" || e.target.matches("input,textarea,select")) return; if (e.key === "ArrowLeft") document.querySelector("#prev")?.click(); if (e.key === "ArrowRight") document.querySelector("#next")?.click(); });
manifest = await fetch("data/manifest.json").then(r => r.json());
retiredIds = new Set(manifest.retiredIds || []);
document.body.classList.toggle("dark", state.dark);
home();
const intro = document.querySelector("#intro");
const closeIntro = () => { intro.classList.add("intro-exit"); sessionStorage.setItem("zhicai-intro-seen", "1"); setTimeout(() => intro.remove(), 650); };
document.querySelectorAll("#skipIntro,#skipIntroAlt").forEach(button => button.addEventListener("click", closeIntro));
if (sessionStorage.getItem("zhicai-intro-seen") || matchMedia("(prefers-reduced-motion: reduce)").matches) intro.remove();
else setTimeout(closeIntro, 3600);

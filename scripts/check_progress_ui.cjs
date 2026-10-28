const { chromium } = require('playwright');
const assert = require('node:assert/strict');

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe' });
  try {
    const context = await browser.newContext({ reducedMotion: 'reduce' });
    await context.addInitScript(() => {
      if (!localStorage.getItem('zhicai-cpa-financial-management-v1')) localStorage.setItem('zhicai-cpa-financial-management-v1', JSON.stringify({
        answered: { 'fm-02-00001': { correct: false }, 'fm-09-00001': { correct: false }, 'fm-01-00001': { correct: false } },
        favorites: ['fm-02-00001', 'fm-09-00001', 'fm-01-00001'], last: null, dark: false
      }));
    });
    const page = await context.newPage();
    await page.goto('http://127.0.0.1:4173/', { waitUntil: 'networkidle' });
    assert.equal(await page.locator('.hero-stats strong').nth(1).innerText(), '1');
    assert.match(await page.locator('[data-mode="wrong"]').innerText(), /1 道待巩固/);
    assert.match(await page.locator('[data-mode="favorite"]').innerText(), /1 道已收藏/);
    await page.locator('[data-chapter="02"]').click();
    assert.match(await page.locator('.question-title').innerText(), /速动比率/);
    await page.locator('#numeric').fill('1.2');
    await page.locator('#submit').click();
    assert.match(await page.locator('.feedback').innerText(), /回答正确/);
    await page.locator('#favorite').click();
    assert.match(await page.locator('#favorite').innerText(), /已收藏/);
    const saved = await page.evaluate(() => JSON.parse(localStorage.getItem('zhicai-cpa-financial-management-v1')));
    assert.equal(saved.answered['fm-02-authored-001'].correct, true);
    assert.ok(saved.answered['fm-02-00001']);
    assert.ok(saved.favorites.includes('fm-02-authored-001'));
    await page.reload({ waitUntil: 'networkidle' });
    assert.equal(await page.locator('.hero-stats strong').nth(1).innerText(), '2');
    await page.locator('[data-chapter="09"]').click();
    await page.locator('#search').fill('五年期借款合同');
    await page.locator('.answer').filter({ hasText: '限制性条款可能约束后续融资与利润分配' }).click();
    await page.locator('#submit').click();
    assert.match(await page.locator('.feedback').innerText(), /回答正确/);
    await page.locator('#back').click();
    await page.locator('[data-chapter="19"]').click();
    assert.match(await page.locator('.question-title').innerText(), /可控成本预算/);
    await page.locator('#numeric').fill('-6');
    await page.locator('#submit').click();
    assert.match(await page.locator('.feedback').innerText(), /回答正确/);
    await page.locator('#next').click();
    assert.match(await page.locator('.question-title').innerText(), /总部统一决定保险方案/);
    await page.locator('#search').fill('总部统一决定保险方案');
    await page.locator('.answer').filter({ hasText: '作为经理不可控成本，单独列示' }).click();
    await page.locator('#submit').click();
    assert.match(await page.locator('.feedback').innerText(), /回答正确/);
    console.log('Browser progress migration, reload, calculation, choice, search and favorite checks passed');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });

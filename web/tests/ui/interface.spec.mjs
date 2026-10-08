import { test, expect } from '@playwright/test';
const code = 'local-ui-test-access-code-2026';
function tone() {
  const rate = 22050, count = rate, buffer = Buffer.alloc(44 + count * 2);
  buffer.write('RIFF'); buffer.writeUInt32LE(buffer.length - 8, 4); buffer.write('WAVEfmt ', 8); buffer.writeUInt32LE(16, 16); buffer.writeUInt16LE(1, 20); buffer.writeUInt16LE(1, 22); buffer.writeUInt32LE(rate, 24); buffer.writeUInt32LE(rate * 2, 28); buffer.writeUInt16LE(2, 32); buffer.writeUInt16LE(16, 34); buffer.write('data', 36); buffer.writeUInt32LE(count * 2, 40);
  for (let i = 0; i < count; i++) buffer.writeInt16LE(Math.round(Math.sin(i / rate * 440 * Math.PI * 2) * 12000), 44 + i * 2);
  return buffer;
}
async function connect(page) {
  await page.goto('/'); await expect(page.locator('.ai-core')).toBeVisible();
  await page.locator('#access').fill(code); await page.locator('#gate-form button').click();
  await expect(page.locator('#gate')).toBeHidden();
}
test('access gate, real status endpoint, responsive controls and persistent settings', async ({ page }, info) => {
  const errors = []; page.on('pageerror', e => errors.push(e.message));
  const blocked = await page.request.post('/api/chat', { data: { message: 'Merhaba' } }); expect(blocked.status()).toBe(401);
  await connect(page); await expect(page.locator('#pc-status')).toHaveText('Windows JARVIS çevrimdışı');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  if(info.project.name==='desktop'){await expect(page.getByRole('button',{name:'⌁Chrome’u aç',exact:true})).toBeInViewport({ratio:0.99});await expect(page.getByText('İşlem modu',{exact:true})).toBeInViewport({ratio:0.99})}
  await page.screenshot({ path: `test-results/jarvis-live-${info.project.name}.png`, fullPage: true });
  await page.getByRole('button', { name: 'Ayarlar', exact: true }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.getByLabel('3D çekirdek ve animasyon', { exact: false }).uncheck();
  await page.getByLabel('Efekt yoğunluğu').selectOption('low');
  await page.locator('#close-voice-modal').click(); await page.reload();
  await expect(page.locator('.core-fallback')).toBeVisible();
  await page.getByRole('button', { name: 'Ayarlar', exact: true }).click();
  await expect(page.getByLabel('Efekt yoğunluğu')).toHaveValue('low');
  await page.locator('#close-voice-modal').click();
  await page.screenshot({ path: `test-results/jarvis-${info.project.name}.png`, fullPage: true });
  expect(errors).toEqual([]);
});
test('chat retains history, proposals require approval, measured audio drives speaking and replay', async ({ page }) => {
  let jobs = 0, history;
  await page.route('**/api/chat', async route => {
    history = route.request().postDataJSON().history;
    await new Promise(r => setTimeout(r, 250));
    await route.fulfill({ json: { text: 'Merhaba. Chrome açmayı önerebilirim.', actions: [{ name: 'open_app', args: { name: 'chrome' } }] } });
  });
  await page.route('**/api/voice', route => route.fulfill({ contentType: 'audio/wav', body: tone() }));
  await page.route('**/api/jobs', route => { jobs++; return route.fulfill({ status: 409, json: { error: 'Windows çevrimdışı.' } }); });
  await connect(page);
  await page.evaluate(() => { window.measuredPeak = 0; addEventListener('jarvis:audio', e => { window.measuredPeak = Math.max(window.measuredPeak, e.detail.level); }); });
  await page.locator('#prompt').fill('Chrome aç'); await page.locator('#send').click();
  await expect(page.locator('.ai-core')).toHaveAttribute('data-state', 'thinking');
  await expect(page.locator('#messages')).toContainText('Chrome açmayı önerebilirim');
  await expect.poll(() => page.evaluate(() => window.measuredPeak)).toBeGreaterThan(0.05);
  await expect(page.locator('.ai-core')).toHaveAttribute('data-state', 'idle');
  expect(jobs).toBe(0); expect(history).toEqual([]);
  await page.evaluate(() => { window.measuredPeak = 0; }); await page.locator('#replay').click();
  await expect.poll(() => page.evaluate(() => window.measuredPeak)).toBeGreaterThan(0.05);
  await expect(page.locator('.ai-core')).toHaveAttribute('data-state', 'idle');
  await page.locator('#proposals button').click(); expect(jobs).toBe(1);
  await page.locator('#prompt').fill('Teşekkürler'); await page.locator('#send').click();
  await expect.poll(() => history.length).toBe(2);
});
test('API failure exposes ERROR, reduced motion keeps static core and usable chat', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.route('**/api/chat', route => route.fulfill({ status: 429, json: { error: 'Gemini kullanım sınırına ulaşıldı.' } }));
  await connect(page); await expect(page.locator('.core-fallback')).toBeVisible();
  await page.locator('#prompt').fill('Merhaba'); await page.locator('#send').click();
  await expect(page.locator('.ai-core')).toHaveAttribute('data-state', 'error');
  await expect(page.locator('#messages')).toContainText('Gemini kullanım sınırına ulaşıldı');
});
test('listening is driven by speech recognition lifecycle, unsupported WebGL falls back', async ({ page }) => {
  await page.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function(kind, ...args) { return kind.startsWith('webgl') ? null : original.call(this, kind, ...args); };
    window.SpeechRecognition = class { start() { this.onstart(); } stop() { this.onend(); } };
  });
  await connect(page); await expect(page.locator('.core-fallback')).toBeVisible();
  await page.locator('.core-listen').click(); await expect(page.locator('.ai-core')).toHaveAttribute('data-state', 'listening');
  await page.locator('.core-listen').click(); await expect(page.locator('.ai-core')).toHaveAttribute('data-state', 'idle');
});

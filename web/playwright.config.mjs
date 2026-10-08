import { defineConfig, devices } from '@playwright/test';
export default defineConfig({
  testDir: './tests/ui', workers: 1, timeout: 30000,
  use: { baseURL: 'http://127.0.0.1:3000', headless: true, launchOptions: { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || undefined, args: ['--autoplay-policy=no-user-gesture-required', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] } },
  projects: [{ name: 'desktop', use: { viewport: { width: 1440, height: 1000 } } }, { name: 'mobile', use: { ...devices['iPhone 13'], defaultBrowserType: 'chromium' } }],
  webServer: { command: 'npm run dev', url: 'http://127.0.0.1:3000', reuseExistingServer: false, env: { JARVIS_ACCESS_CODE: 'local-ui-test-access-code-2026' } }
});

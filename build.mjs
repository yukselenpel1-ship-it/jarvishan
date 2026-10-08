import { buildWeb } from './web/build.mjs';
await buildWeb(new URL('./public', import.meta.url).pathname);

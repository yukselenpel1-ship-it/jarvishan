import { mkdir, copyFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { build } from 'esbuild';
const root = path.dirname(fileURLToPath(import.meta.url));
export async function buildWeb(output = path.join(root, 'public')) {
  await mkdir(output, { recursive: true });
  await Promise.all(['index.html', 'client.js', 'audio-meter.js'].map(file => copyFile(path.join(root, file), path.join(output, file))));
  await build({ entryPoints: [path.join(root, 'src/ui.tsx')], bundle: true, minify: true, sourcemap: true, target: ['es2022'], format: 'esm', outfile: path.join(output, 'ui.js'), jsx: 'automatic', define: { 'process.env.NODE_ENV': '"production"' } });
  await copyFile(path.join(root, 'src/reactbits/LICENSE.md'), path.join(output, 'reactbits-license.txt'));
}
if (process.argv[1] === fileURLToPath(import.meta.url)) await buildWeb();

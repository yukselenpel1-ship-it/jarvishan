import {mkdir,copyFile} from 'node:fs/promises';
await mkdir('public',{recursive:true});
await copyFile('web/index.html','public/index.html');
await copyFile('web/client.js','public/client.js');

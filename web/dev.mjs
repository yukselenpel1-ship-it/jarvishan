import http from 'node:http';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';

const root=path.dirname(fileURLToPath(import.meta.url));
const routes={chat:()=>import('./api/chat.js'),jobs:()=>import('./api/jobs.js'),bridge:()=>import('./api/bridge.js'),status:()=>import('./api/status.js')};
const server=http.createServer(async(req,res)=>{
  const url=new URL(req.url,'http://localhost:3000');
  const send=(code,data)=>{res.writeHead(code,{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'});res.end(JSON.stringify(data))};
  if(url.pathname.startsWith('/api/')){
    const name=url.pathname.slice(5);
    if(!routes[name])return send(404,{error:'Adres bulunamadı.'});
    let body='';for await(const chunk of req){body+=chunk;if(body.length>20000)return send(413,{error:'İstek çok uzun.'})}
    try{req.body=body?JSON.parse(body):{};req.query=Object.fromEntries(url.searchParams);res.status=n=>{res.statusCode=n;return res};res.json=data=>send(res.statusCode||200,data);await(await routes[name]()).default(req,res)}
    catch{if(!res.writableEnded)send(400,{error:'İstek okunamadı.'})}
    return;
  }
  if(!['/','/index.html','/client.js'].includes(url.pathname)){res.writeHead(404);return res.end('Not found')}
  const file=url.pathname==='/client.js'?'client.js':'index.html';
  const data=await readFile(path.join(root,file));res.writeHead(200,{'Content-Type':file.endsWith('.js')?'text/javascript; charset=utf-8':'text/html; charset=utf-8','Cache-Control':'no-store'});res.end(data);
});
server.listen(3000,'127.0.0.1',()=>console.log('JARVIS Web: http://localhost:3000'));

import test from 'node:test';
import assert from 'node:assert/strict';
import chat from '../api/chat.js';
import jobs from '../api/jobs.js';
import bridge from '../api/bridge.js';
import {safeAction} from '../lib/server.js';

function response(){return {statusCode:200,headers:{},status(n){this.statusCode=n;return this},setHeader(k,v){this.headers[k]=v;return this},json(data){this.data=data;return this}}}
test('mobile actions reject unsafe or malformed computer commands',()=>{
  assert.equal(safeAction({name:'press_keys',args:{keys:['ctrl','v']}}),null);
  assert.equal(safeAction({name:'open_app',args:{name:'powershell'}}),null);
  assert.deepEqual(safeAction({name:'open_app',args:{name:'chrome',command:'del *'}}),{name:'open_app',args:{name:'chrome'}});
});
test('Gemini text and safe action are proposed, without execution',async()=>{
  const oldKey=process.env.GEMINI_API_KEY,oldCode=process.env.JARVIS_ACCESS_CODE,oldFetch=global.fetch;
  process.env.GEMINI_API_KEY='test';process.env.JARVIS_ACCESS_CODE='a-safe-access-code-for-tests';
  let payload;
  global.fetch=async(url,options)=>{payload=JSON.parse(options.body);return {ok:true,json:async()=>({candidates:[{content:{parts:[{text:'Chrome açmayı önerebilirim.'},{functionCall:{name:'open_app',args:{name:'chrome'}}},{functionCall:{name:'press_keys',args:{keys:['ctrl','v']}}}]}}]})}};
  try{
    const res=response();await chat({method:'POST',headers:{authorization:'Bearer a-safe-access-code-for-tests'},body:{message:'Chrome aç',history:[]}},res);
    assert.equal(res.statusCode,200);assert.deepEqual(res.data.actions,[{name:'open_app',args:{name:'chrome'}}]);
    assert.equal(payload.contents.at(-1).parts[0].text,'Chrome aç');
    assert.equal(payload.tools[0].functionDeclarations.some(x=>x.name==='press_keys'),false);
  }finally{global.fetch=oldFetch;if(oldKey===undefined)delete process.env.GEMINI_API_KEY;else process.env.GEMINI_API_KEY=oldKey;if(oldCode===undefined)delete process.env.JARVIS_ACCESS_CODE;else process.env.JARVIS_ACCESS_CODE=oldCode}
});
test('unknown configured model retries the supported Gemini model',async()=>{
  const old={key:process.env.GEMINI_API_KEY,code:process.env.JARVIS_ACCESS_CODE,model:process.env.GEMINI_MODEL,fetch:global.fetch};
  process.env.GEMINI_API_KEY='test';process.env.JARVIS_ACCESS_CODE='a-safe-access-code-for-tests';process.env.GEMINI_MODEL='unknown-model';
  const urls=[];
  global.fetch=async url=>{urls.push(url);return urls.length===1?{ok:false,status:404}:{ok:true,json:async()=>({candidates:[{content:{parts:[{text:'İyiyim, teşekkürler.'}]}}]})}};
  try{
    const res=response();await chat({method:'POST',headers:{authorization:'Bearer a-safe-access-code-for-tests'},body:{message:'Nasılsın?'}},res);
    assert.equal(res.statusCode,200);assert.equal(res.data.text,'İyiyim, teşekkürler.');
    assert.match(urls[1],/models\/gemini-2\.5-flash:generateContent$/);
  }finally{
    global.fetch=old.fetch;
    for(const [key,value] of [['GEMINI_API_KEY',old.key],['JARVIS_ACCESS_CODE',old.code],['GEMINI_MODEL',old.model]]){if(value===undefined)delete process.env[key];else process.env[key]=value}
  }
});
test('persistent 404 checks models available to the API key',async()=>{
  const old={key:process.env.GEMINI_API_KEY,code:process.env.JARVIS_ACCESS_CODE,model:process.env.GEMINI_MODEL,fetch:global.fetch};
  process.env.GEMINI_API_KEY='test';process.env.JARVIS_ACCESS_CODE='a-safe-access-code-for-tests';process.env.GEMINI_MODEL='unknown-model';
  const urls=[];
  global.fetch=async url=>{urls.push(url);
    if(url.includes('pageSize='))return {ok:true,json:async()=>({models:[{name:'models/gemini-3.5-flash',supportedGenerationMethods:['generateContent']}]})};
    return urls.length===4?{ok:true,json:async()=>({candidates:[{content:{parts:[{text:'Merhaba!'}]}}]})}:{ok:false,status:404};
  };
  try{
    const res=response();await chat({method:'POST',headers:{authorization:'Bearer a-safe-access-code-for-tests'},body:{message:'Merhaba'}},res);
    assert.equal(res.statusCode,200);assert.equal(res.data.text,'Merhaba!');
    assert.match(urls[3],/models\/gemini-3\.5-flash:generateContent$/);
  }finally{
    global.fetch=old.fetch;
    for(const [key,value] of [['GEMINI_API_KEY',old.key],['JARVIS_ACCESS_CODE',old.code],['GEMINI_MODEL',old.model]]){if(value===undefined)delete process.env[key];else process.env[key]=value}
  }
});
test('job enqueue rejects unauthenticated requests before Redis',async()=>{
  const previous=process.env.JARVIS_ACCESS_CODE;process.env.JARVIS_ACCESS_CODE='a-safe-access-code-for-tests';
  try{const res=response();await jobs({method:'POST',headers:{authorization:'Bearer wrong'},body:{action:{name:'open_app',args:{name:'chrome'}}}},res);assert.equal(res.statusCode,401)}
  finally{if(previous===undefined)delete process.env.JARVIS_ACCESS_CODE;else process.env.JARVIS_ACCESS_CODE=previous}
});
test('approved job travels to Windows bridge and returns a result',async()=>{
  const old={code:process.env.JARVIS_ACCESS_CODE,bridge:process.env.JARVIS_BRIDGE_TOKEN,url:process.env.UPSTASH_REDIS_REST_URL,token:process.env.UPSTASH_REDIS_REST_TOKEN,fetch:global.fetch};
  process.env.JARVIS_ACCESS_CODE='a-safe-access-code-for-tests';process.env.JARVIS_BRIDGE_TOKEN='a-different-bridge-token';process.env.UPSTASH_REDIS_REST_URL='https://redis.example';process.env.UPSTASH_REDIS_REST_TOKEN='redis-test';
  const data=new Map([['jarvis:heartbeat',String(Date.now())]]),queue=[];
  global.fetch=async(_,options)=>{const [cmd,...args]=JSON.parse(options.body);let result=null;
    if(cmd==='GET')result=data.get(args[0])||null;
    if(cmd==='SET'){data.set(args[0],args[1]);result='OK'}
    if(cmd==='RPUSH'){queue.push(args[1]);result=queue.length}
    if(cmd==='LPOP')result=queue.shift()||null;
    return {ok:true,json:async()=>({result})};
  };
  try{
    const issued=response();await jobs({method:'POST',headers:{authorization:'Bearer a-safe-access-code-for-tests'},body:{action:{name:'system_info',args:{}}}},issued);
    assert.equal(issued.statusCode,201);
    const pulled=response();await bridge({method:'GET',headers:{authorization:'Bearer a-different-bridge-token'}},pulled);
    assert.equal(pulled.data.job.action.name,'system_info');
    const completed=response();await bridge({method:'POST',headers:{authorization:'Bearer a-different-bridge-token'},body:{id:issued.data.id,result:'CPU %25'}},completed);
    assert.equal(completed.data.ok,true);
    const checked=response();await jobs({method:'GET',headers:{authorization:'Bearer a-safe-access-code-for-tests'},query:{id:issued.data.id}},checked);
    assert.equal(checked.data.result,'CPU %25');
  }finally{
    global.fetch=old.fetch;
    for(const [key,value] of [['JARVIS_ACCESS_CODE',old.code],['JARVIS_BRIDGE_TOKEN',old.bridge],['UPSTASH_REDIS_REST_URL',old.url],['UPSTASH_REDIS_REST_TOKEN',old.token]]){if(value===undefined)delete process.env[key];else process.env[key]=value}
  }
});

import { timingSafeEqual, randomUUID } from 'node:crypto';

export function json(res,status,data){res.status(status).setHeader('Cache-Control','no-store').json(data)}
export function same(a,b){if(typeof a!=='string'||typeof b!=='string'||!b)return false;const x=Buffer.from(a),y=Buffer.from(b);return x.length===y.length&&timingSafeEqual(x,y)}
export function authorized(req,kind='access'){
  const expected=process.env[kind==='bridge'?'JARVIS_BRIDGE_TOKEN':'JARVIS_ACCESS_CODE'];
  if(!expected||expected.length<16)return false;
  return same(req.headers.authorization?.replace(/^Bearer\s+/i,'')||'',expected);
}
const memData = new Map();
const memQueue = [];

export function configured(){
  if (Boolean(process.env.UPSTASH_REDIS_REST_URL&&process.env.UPSTASH_REDIS_REST_TOKEN)) return true;
  return process.env.NODE_ENV !== 'production' || process.env.JARVIS_LOCAL_BRIDGE === 'true';
}

export async function redis(...command){
  if (process.env.UPSTASH_REDIS_REST_URL&&process.env.UPSTASH_REDIS_REST_TOKEN) {
    const response=await fetch(process.env.UPSTASH_REDIS_REST_URL,{method:'POST',
      headers:{Authorization:'Bearer '+process.env.UPSTASH_REDIS_REST_TOKEN,'Content-Type':'application/json'},
      body:JSON.stringify(command),signal:AbortSignal.timeout(8000)});
    if(!response.ok)throw Error('Köprü veritabanına ulaşılamadı.');
    const payload=await response.json();
    if(payload.error)throw Error('Köprü veritabanı hatası.');
    return payload.result;
  }
  if (!configured()) throw Error('Köprü veritabanı ayarlı değil.');
  const [cmd, ...args] = command;
  if (cmd === 'GET') return memData.get(args[0]) || null;
  if (cmd === 'SET') { memData.set(args[0], args[1]); return 'OK'; }
  if (cmd === 'RPUSH') { memQueue.push(args[1]); return memQueue.length; }
  if (cmd === 'LPOP') return memQueue.shift() || null;
  return null;
}
export const safeTools=[
  {name:'open_app',description:'Kullanıcının istediği programı Windows bilgisayarında aç',parameters:{type:'OBJECT',properties:{name:{type:'STRING',enum:['chrome','not defteri','hesap makinesi','gezgin']}},required:['name']}},
  {name:'search_web',description:'Windows bilgisayarında web araması aç',parameters:{type:'OBJECT',properties:{query:{type:'STRING'}},required:['query']}},
  {name:'system_info',description:'Windows bilgisayarının işlemci ve RAM bilgisini oku',parameters:{type:'OBJECT',properties:{},required:[]}},
  {name:'find_file',description:'Windows bilgisayarında dosya adına göre ara',parameters:{type:'OBJECT',properties:{name:{type:'STRING'}},required:['name']}},
  {name:'add_note',description:'Windows bilgisayarında yerel not oluştur',parameters:{type:'OBJECT',properties:{text:{type:'STRING'}},required:['text']}},
  {name:'remind_me',description:'Windows bilgisayarında dakika sonra hatırlatma oluştur',parameters:{type:'OBJECT',properties:{minutes:{type:'INTEGER'},text:{type:'STRING'}},required:['minutes','text']}}
];
export function safeAction(action){
  if(!action||typeof action!=='object'||!safeTools.some(x=>x.name===action.name)||!action.args||typeof action.args!=='object')return null;
  const {name,args}=action;
  if(name==='open_app'&&!['chrome','not defteri','hesap makinesi','gezgin'].includes(args.name))return null;
  if(name==='open_app')return {name,args:{name:args.name}};
  if(name==='system_info')return {name,args:{}};
  const key=name==='search_web'?'query':name==='find_file'?'name':'text';
  if(name==='remind_me'&&(!Number.isInteger(args.minutes)||args.minutes<1||args.minutes>525600))return null;
  if(typeof args[key]!=='string'||args[key].trim().length<1||args[key].length>(name==='add_note'?1000: name==='remind_me'?500:200))return null;
  return {name,args:name==='remind_me'?{minutes:args.minutes,text:args.text}:name==='open_app'?{name:args.name}:{[key]:args[key]}};
}
export function jobId(){return randomUUID()}
export function jobKey(id){return 'jarvis:job:'+id}
export const queueKey='jarvis:queue';
export const heartbeatKey='jarvis:heartbeat';

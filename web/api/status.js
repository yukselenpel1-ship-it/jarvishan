import {authorized,configured,json,redis,heartbeatKey} from './_lib.js';
export default async function handler(req,res){
  if(!authorized(req))return json(res,401,{error:'Erişim kodu hatalı.'});
  if(req.method!=='GET')return json(res,405,{error:'GET gerekli.'});
  if(!configured())return json(res,200,{bridge:'not_configured'});
  try{
    const last=Number(await redis('GET',heartbeatKey));
    return json(res,200,{bridge:last&&Date.now()-last<40000?'online':'offline'});
  }catch{return json(res,503,{bridge:'offline',error:'Bağlantı kontrol edilemedi.'})}
}

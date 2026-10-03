import {authorized,configured,json,redis,jobKey,queueKey,heartbeatKey} from '../lib/server.js';

export default async function handler(req,res){
  if(!authorized(req,'bridge'))return json(res,401,{error:'Köprü erişimi reddedildi.'});
  if(!configured())return json(res,503,{error:'Köprü veritabanı ayarlı değil.'});
  try{
    if(req.method==='GET'){
      await redis('SET',heartbeatKey,String(Date.now()),'EX',40);
      const id=await redis('LPOP',queueKey);
      if(!id)return json(res,200,{job:null});
      const raw=await redis('GET',jobKey(id));
      if(!raw)return json(res,200,{job:null});
      const job=JSON.parse(raw);
      if(job.status!=='queued')return json(res,200,{job:null});
      job.status='processing';
      await redis('SET',jobKey(id),JSON.stringify(job),'EX',600);
      return json(res,200,{job:{id:job.id,action:job.action}});
    }
    if(req.method==='POST'){
      const {id,result}=req.body||{};
      if(typeof id!=='string'||!/^[0-9a-f-]{36}$/.test(id)||typeof result!=='string'||result.length>4000)return json(res,400,{error:'İşlem sonucu geçersiz.'});
      const raw=await redis('GET',jobKey(id));
      if(!raw)return json(res,404,{error:'İşlem süresi doldu.'});
      const job=JSON.parse(raw);
      if(job.status!=='processing')return json(res,409,{error:'İşlem durumu geçersiz.'});
      job.status='done';job.result=result;
      await redis('SET',jobKey(id),JSON.stringify(job),'EX',600);
      return json(res,200,{ok:true});
    }
    return json(res,405,{error:'GET veya POST gerekli.'});
  }catch{return json(res,503,{error:'Köprü veritabanına ulaşılamadı.'})}
}

import {authorized,configured,json,redis,safeAction,jobId,jobKey,queueKey,heartbeatKey} from '../lib/server.js';

export default async function handler(req,res){
  if(!authorized(req))return json(res,401,{error:'Erişim kodu hatalı.'});
  if(!configured())return json(res,503,{error:'Uzak bilgisayar köprüsü henüz kurulmadı.'});
  try{
    if(req.method==='POST'){
      const action=safeAction(req.body?.action);
      if(!action)return json(res,400,{error:'Bu bilgisayar işlemi izinli değil.'});
      const last=Number(await redis('GET',heartbeatKey));
      if(!last||Date.now()-last>40000)return json(res,409,{error:'Windows JARVIS çevrimdışı. Uygulamayı açıp bağlantıyı kontrol et.'});
      const id=jobId(),job={id,action,status:'queued',created:Date.now()};
      await redis('SET',jobKey(id),JSON.stringify(job),'EX',600);
      await redis('RPUSH',queueKey,id);
      return json(res,201,{id,status:'queued'});
    }
    if(req.method==='GET'){
      const id=req.query?.id;
      if(typeof id!=='string'||!/^[0-9a-f-]{36}$/.test(id))return json(res,400,{error:'İşlem kimliği geçersiz.'});
      const raw=await redis('GET',jobKey(id));
      if(!raw)return json(res,404,{error:'İşlem bulunamadı veya süresi doldu.'});
      const job=JSON.parse(raw);
      return json(res,200,{id:job.id,status:job.status,result:job.result||''});
    }
    return json(res,405,{error:'GET veya POST gerekli.'});
  }catch{return json(res,503,{error:'Köprüye ulaşılamadı.'})}
}

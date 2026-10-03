import {authorized,json,safeTools,safeAction} from './_lib.js';

export default async function handler(req,res){
  if(!authorized(req))return json(res,401,{error:'Erişim kodu hatalı veya sunucuda ayarlı değil.'});
  if(req.method!=='POST')return json(res,405,{error:'POST gerekli.'});
  const {message,history=[]}=req.body||{};
  if(typeof message!=='string'||!message.trim()||message.length>3000||!Array.isArray(history))return json(res,400,{error:'Mesaj geçersiz.'});
  if(!process.env.GEMINI_API_KEY)return json(res,503,{error:'Vercel üzerinde GEMINI_API_KEY ayarlanmadı.'});
  const model=process.env.GEMINI_MODEL||'gemini-3.8-flash';
  if(!/^[a-zA-Z0-9._-]+$/.test(model))return json(res,500,{error:'Model adı geçersiz.'});
  const contents=history.slice(-12).filter(x=>['user','model'].includes(x?.role)&&typeof x.text==='string'&&x.text.length<=3000)
    .map(x=>({role:x.role,parts:[{text:x.text}]}));
  contents.push({role:'user',parts:[{text:message}]});
  const body={systemInstruction:{parts:[{text:'Sen JARVIS adlı Türkçe kişisel asistansın. Doğal ve kısa konuş. Bilgisayar işlemini sadece kullanıcı açıkça isterse araç olarak öner. Araç henüz çalışmadan yapılmış gibi söyleme. Windows bilgisayar çevrimdışı olabilir. Özel bilgileri kendiliğinden gönderme.'}]},
    contents,tools:[{functionDeclarations:safeTools}],generationConfig:{maxOutputTokens:1024,temperature:0.55}};
  try{
    const response=await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`,
      {method:'POST',headers:{'Content-Type':'application/json','x-goog-api-key':process.env.GEMINI_API_KEY},
       body:JSON.stringify(body),signal:AbortSignal.timeout(28000)});
    if(!response.ok)return json(res,response.status===429?429:502,{error:response.status===429?'Gemini kullanım sınırına ulaşıldı.':`Gemini yanıt vermedi (${response.status}). Model adını ve API anahtarını kontrol et.`});
    const data=await response.json(),parts=data.candidates?.[0]?.content?.parts||[];
    const text=parts.filter(x=>!x.thought&&typeof x.text==='string').map(x=>x.text).join('\n').trim();
    const actions=parts.map(x=>x.functionCall).filter(Boolean).map(x=>safeAction({name:x.name,args:x.args||{}})).filter(Boolean).slice(0,3);
    return json(res,200,{text:text|| (actions.length?'Bilgisayar işlemini önerebilirim. Onaylarsan gönderirim.':'Yanıt oluşturulamadı; tekrar dene.'),actions});
  }catch{return json(res,504,{error:'Gemini bağlantısı zaman aşımına uğradı. Tekrar dene.'})}
}

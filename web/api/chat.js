import {authorized,json,safeTools,safeAction} from '../lib/server.js';

export default async function handler(req,res){
  if(!authorized(req))return json(res,401,{error:'Erişim kodu hatalı veya sunucuda ayarlı değil.'});
  if(req.method!=='POST')return json(res,405,{error:'POST gerekli.'});
  const {message,history=[]}=req.body||{};
  if(typeof message!=='string'||!message.trim()||message.length>3000||!Array.isArray(history))return json(res,400,{error:'Mesaj geçersiz.'});
  if(!process.env.GEMINI_API_KEY)return json(res,503,{error:'Vercel üzerinde GEMINI_API_KEY ayarlanmadı.'});
  const model=process.env.GEMINI_MODEL||'gemini-2.5-flash';
  if(!/^[a-zA-Z0-9._-]+$/.test(model))return json(res,500,{error:'Model adı geçersiz.'});
  const contents=history.slice(-12).filter(x=>['user','model'].includes(x?.role)&&typeof x.text==='string'&&x.text.length<=3000)
    .map(x=>({role:x.role,parts:[{text:x.text}]}));
  contents.push({role:'user',parts:[{text:message}]});
  const body={systemInstruction:{parts:[{text:'Sen JARVIS adlı Türkçe kişisel asistansın. Doğal ve kısa konuş. Bilgisayar işlemini sadece kullanıcı açıkça isterse araç olarak öner. Araç henüz çalışmadan yapılmış gibi söyleme. Windows bilgisayar çevrimdışı olabilir. Özel bilgileri kendiliğinden gönderme.'}]},
    contents,tools:[{functionDeclarations:safeTools}],generationConfig:{maxOutputTokens:1024,temperature:0.55}};
  try{
    const generate=name=>fetch(`https://generativelanguage.googleapis.com/v1beta/models/${name}:generateContent`,
      {method:'POST',headers:{'Content-Type':'application/json','x-goog-api-key':process.env.GEMINI_API_KEY},
       body:JSON.stringify(body),signal:AbortSignal.timeout(13000)});
    const attempted=[model];
    let response=await generate(model);
    if(response.status===404&&model!=='gemini-2.5-flash'){
      attempted.push('gemini-2.5-flash');
      response=await generate('gemini-2.5-flash');
    }
    if(response.status===404){
      const listed=await fetch('https://generativelanguage.googleapis.com/v1beta/models?pageSize=1000',
        {headers:{'x-goog-api-key':process.env.GEMINI_API_KEY},signal:AbortSignal.timeout(8000)});
      if(listed.ok){
        const catalogue=await listed.json();
        const available=(catalogue.models||[]).filter(x=>/^models\/gemini-[a-zA-Z0-9._-]+$/.test(x.name)&&
          (x.supportedGenerationMethods||x.supportedActions||[]).includes('generateContent')).map(x=>x.name.slice(7));
        const choices=available.filter(x=>!attempted.includes(x)&&/flash/.test(x)&&!/live|image|tts|preview/.test(x))
          .sort((a,b)=>b.localeCompare(a,undefined,{numeric:true})).slice(0,2);
        for(const choice of choices){
          attempted.push(choice);
          response=await generate(choice);
          if(response.status!==404)break;
        }
        if(response.status===404){
          let detail='';
          try{detail=String((await response.json()).error?.message||'').toLowerCase()}catch{}
          const reason=/project.*not active|project.*inactive/.test(detail)?'Google, anahtarın bağlı olduğu projeyi etkin görmüyor.':
            /not found for api version|not supported for generatecontent/.test(detail)?'Bu model generateContent için kullanılamıyor.':
            /leak|block/.test(detail)?'Google API anahtarını engellemiş.':'Google isteği 404 ile reddetti.';
          return json(res,502,{error:`${reason} Model listesi: ${available.length} sohbet modeli. Denenenler: ${attempted.join(', ')}. Google AI Studio’da projenin ve Gemini API erişiminin durumunu kontrol et.`});
        }
      }else return json(res,502,{error:'Gemini API anahtarıyla model listesi alınamadı. Google AI Studio’da anahtarın etkin ve Gemini API erişimine açık olduğunu kontrol et.'});
    }
    if(!response.ok)return json(res,response.status===429?429:502,{error:response.status===429?'Gemini kullanım sınırına ulaşıldı.':`Gemini yanıt vermedi (${response.status}). Google AI Studio’da API anahtarının durumunu kontrol et.`});
    const data=await response.json(),parts=data.candidates?.[0]?.content?.parts||[];
    const text=parts.filter(x=>!x.thought&&typeof x.text==='string').map(x=>x.text).join('\n').trim();
    const actions=parts.map(x=>x.functionCall).filter(Boolean).map(x=>safeAction({name:x.name,args:x.args||{}})).filter(Boolean).slice(0,3);
    return json(res,200,{text:text|| (actions.length?'Bilgisayar işlemini önerebilirim. Onaylarsan gönderirim.':'Yanıt oluşturulamadı; tekrar dene.'),actions});
  }catch{return json(res,504,{error:'Gemini bağlantısı zaman aşımına uğradı. Tekrar dene.'})}
}

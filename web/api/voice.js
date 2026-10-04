import {authorized,json} from '../lib/server.js';

const VOICE_ID='IKne3meq5aSn9XLyUdCD';
const MAX_AUDIO_BYTES=6*1024*1024;

export default async function handler(req,res){
  if(!authorized(req))return json(res,401,{error:'Erişim kodu hatalı.'});
  if(req.method!=='POST')return json(res,405,{error:'POST gerekli.'});
  const text=req.body?.text;
  if(typeof text!=='string'||!text.trim()||text.length>1600)
    return json(res,400,{error:'Seslendirme metni 1–1600 karakter olmalı.'});
  const key=process.env.ELEVENLABS_API_KEY?.trim()||(typeof req.headers['x-elevenlabs-key']==='string'?req.headers['x-elevenlabs-key'].trim():'')||(typeof req.body?.apiKey==='string'?req.body.apiKey.trim():'');
  if(!key)return json(res,503,{error:'ElevenLabs API anahtarı ayarlanmadı.'});
  try{
    const response=await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}?output_format=mp3_44100_128`,{
      method:'POST',headers:{'xi-api-key':key,'Content-Type':'application/json','Accept':'audio/mpeg'},
      body:JSON.stringify({text:text.trim(),model_id:'eleven_multilingual_v2'}),
      signal:AbortSignal.timeout(28000)
    });
    if(!response.ok){
      const message=response.status===401?'ElevenLabs API anahtarı geçersiz.':
        response.status===402||response.status===429?'ElevenLabs kullanım hakkı veya sınırı doldu.':
        response.status===404?'ElevenLabs ses kimliği bu hesapta bulunamadı.':'ElevenLabs ses oluşturamadı.';
      return json(res,502,{error:message});
    }
    if(Number(response.headers.get('content-length'))>MAX_AUDIO_BYTES)
      return json(res,502,{error:'Üretilen ses çok büyük.'});
    const audio=Buffer.from(await response.arrayBuffer());
    if(!audio.length||audio.length>MAX_AUDIO_BYTES)return json(res,502,{error:'Üretilen ses geçersiz veya çok büyük.'});
    res.status(200).setHeader('Content-Type','audio/mpeg').setHeader('Cache-Control','no-store').end(audio);
  }catch{return json(res,504,{error:'ElevenLabs bağlantısı zaman aşımına uğradı.'})}
}

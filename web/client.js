import {createAudioMeter} from './audio-meter.js';
const audioMeter=createAudioMeter(detail=>window.dispatchEvent(new CustomEvent('jarvis:audio',{detail})));
let coreMode='idle';
const $=s=>document.querySelector(s);
const state={code:sessionStorage.getItem('jarvisAccess')||'',busy:false,history:[]};
function bubble(who,text){const row=document.createElement('div');row.className='msg'+(who==='SEN'?' me':'');const name=document.createElement('small');name.textContent=(who==='SEN'?'SEN':'JARVIS')+' //' ;row.append(name,document.createTextNode(String(text)));$('#messages').append(row);$('#messages').scrollTop=$('#messages').scrollHeight}
function mode(value){coreMode=value;const labels={idle:['BEKLEME MODU','KONUŞMAYA HAZIR ◦ J.A.R.V.I.S.'],listening:['DİNLENİYOR','MİKROFON AKTİF'],thinking:['İŞLENİYOR','YANIT HAZIRLANIYOR'],speaking:['JARVIS KONUŞUYOR','SES AKIŞI AKTİF ◦ TÜRKÇE'],error:['BAĞLANTI HATASI','LÜTFEN YENİDEN DENE']};$('#orb').classList.toggle('speaking',value==='speaking');$('#stateLabel').textContent=labels[value][0];$('#stateSub').textContent=labels[value][1];window.dispatchEvent(new CustomEvent('jarvis:state',{detail:value}));}

let currentAudio=null,voiceRequest=null,voiceUrl=null,lastSpoken='';
function stopVoice(){audioMeter.stop(true);if(voiceRequest)voiceRequest.abort();voiceRequest=null;if(currentAudio){currentAudio.pause();currentAudio=null}if(voiceUrl){URL.revokeObjectURL(voiceUrl);voiceUrl=null}if('speechSynthesis'in window)speechSynthesis.cancel()}
function browserVoice(text){if(!('speechSynthesis'in window)){mode('idle');return}const utterance=new SpeechSynthesisUtterance(text.slice(0,1200));utterance.lang='tr-TR';utterance.volume=Number($('#volume').value)/100;utterance.rate=1.04;const voice=speechSynthesis.getVoices().find(v=>v.lang.toLowerCase().startsWith('tr'));if(voice)utterance.voice=voice;utterance.onstart=()=>mode('speaking');utterance.onend=()=>mode('idle');utterance.onerror=()=>mode('idle');speechSynthesis.speak(utterance)}
async function speak(text){stopVoice();lastSpoken=String(text);$('#replay').hidden=false;if(Number($('#volume').value)===0){mode('idle');return}mode('thinking');$('#voice-status').textContent='ElevenLabs sesi hazırlanıyor…';const controller=new AbortController();voiceRequest=controller;try{const headers={'Content-Type':'application/json',Authorization:'Bearer '+state.code};const userKey=localStorage.getItem('jarvisElevenLabsKey')?.trim();if(userKey)headers['x-elevenlabs-key']=userKey;const response=await fetch('/api/voice',{method:'POST',headers,body:JSON.stringify({text:lastSpoken.slice(0,1600)}),signal:controller.signal});if(controller.signal.aborted)return;if(!response.ok){let data={};try{data=await response.json()}catch{}throw Error(data.error||'Ses oluşturulamadı.')}const blob=await response.blob();if(controller.signal.aborted)return;voiceUrl=URL.createObjectURL(blob);currentAudio=new Audio(voiceUrl);currentAudio.volume=Number($('#volume').value)/100;currentAudio.onplay=()=>{mode('speaking');$('#voice-status').textContent='ElevenLabs · JARVIS konuşuyor'};currentAudio.onended=()=>{audioMeter.stop();mode('idle');$('#voice-status').textContent='ElevenLabs sesi hazır'};currentAudio.onerror=()=>{audioMeter.stop();mode('error');$('#voice-status').textContent='Ses oynatılamadı; yeniden dene.'};await audioMeter.start('playback',currentAudio);if(controller.signal.aborted)return;await currentAudio.play()}catch(error){if(controller.signal.aborted)return;if(error.name==='NotAllowedError'){$('#voice-status').textContent='Sesi başlatmak için “Tekrar oynat” düğmesine dokun.';mode('idle');return}$('#voice-status').textContent=(error.message||'ElevenLabs kullanılamıyor.')+' Yerel ses kullanılıyor.';browserVoice(lastSpoken)}finally{if(voiceRequest===controller)voiceRequest=null}}

async function api(path,method='GET',body){const r=await fetch('/api/'+path,{method,headers:{'Content-Type':'application/json',Authorization:'Bearer '+state.code},body:body?JSON.stringify(body):undefined});let data;try{data=await r.json()}catch{throw Error('Sunucu yanıtı okunamadı.')}if(!r.ok)throw Error(data.error||'Bağlantı hatası.');return data}
async function status(){if(!state.code)return;try{const data=await api('status');$('#pc-status').textContent=({online:'Windows JARVIS bağlı',offline:'Windows JARVIS çevrimdışı',not_configured:'PC köprüsü ayarlanmadı'})[data.bridge]||'PC durumu bilinmiyor';$('#pc-dot').classList.toggle('green',data.bridge==='online');$('#ai-status').textContent='SOHBETE HAZIR'}catch(e){$('#pc-status').textContent=e.message;$('#pc-dot').classList.remove('green');$('#ai-status').textContent='BAĞLANTI HATASI';if(!state.busy)mode('error')}}
const labels={open_app:a=>`${a.name} uygulamasını aç`,search_web:a=>`Web’de ara: ${a.query}`,system_info:()=>`Sistem bilgilerini oku`,find_file:a=>`Dosya ara: ${a.name}`,add_note:a=>`Not kaydet: ${a.text}`,remind_me:a=>`${a.minutes} dakika sonra hatırlat: ${a.text}`};
function proposals(actions){$('#proposals').replaceChildren();for(const action of actions){if(!labels[action.name])continue;const card=document.createElement('div');card.className='proposal';const label=document.createElement('div');label.textContent='Windows işlemi: '+labels[action.name](action.args);const button=document.createElement('button');button.textContent='ONAYLA VE BİLGİSAYARA GÖNDER';button.onclick=async()=>{button.disabled=true;try{const job=await api('jobs','POST',{action});bubble('JARVIS','İşlem bilgisayara gönderildi. Yanıt bekleniyor...');await waitJob(job.id)}catch(e){bubble('JARVIS',e.message)}finally{card.remove()}};card.append(label,button);$('#proposals').append(card)}}
async function waitJob(id){for(let attempt=0;attempt<36;attempt++){await new Promise(r=>setTimeout(r,2000));try{const job=await api('jobs?id='+encodeURIComponent(id));if(job.status==='done'){bubble('JARVIS','Bilgisayar sonucu: '+job.result);return}}catch(e){bubble('JARVIS',e.message);return}}bubble('JARVIS','Bilgisayar yanıt vermedi. Windows uygulamasının açık olduğunu kontrol et.')}
async function send(text){text=text.trim();if(!text||state.busy)return;stopVoice();state.busy=true;$('#send').disabled=true;mode('thinking');bubble('SEN',text);$('#proposals').replaceChildren();try{const data=await api('chat','POST',{message:text,history:state.history});bubble('JARVIS',data.text);state.history.push({role:'user',text},{role:'model',text:data.text});state.history=state.history.slice(-12);proposals(data.actions||[]);speak(data.text)}catch(e){bubble('JARVIS',e.message);mode('error')}finally{state.busy=false;$('#send').disabled=false}}
$('#form').onsubmit=e=>{e.preventDefault();const field=$('#prompt');const value=field.value;if(state.busy)return;field.value='';send(value)};
document.querySelectorAll('[data-text]').forEach(button=>button.onclick=()=>send(button.dataset.text));
$('#gate-form').onsubmit=async e=>{e.preventDefault();state.code=$('#access').value.trim();try{await api('status');sessionStorage.setItem('jarvisAccess',state.code);$('#gate').hidden=true;$('#gate-error').textContent='';bubble('JARVIS','Merhaba! Buradan sohbet edebilir, Windows JARVIS bağlıysa izinli işlemleri onaylayarak gönderebilirsin.');status()}catch(e){state.code='';$('#gate-error').textContent=e.message}};
if(state.code){$('#gate').hidden=true;bubble('JARVIS','Merhaba! Nasıl yardımcı olabilirim?');status()}setInterval(status,18000);
$('#demo').onclick=()=>speak('Merhaba. Ben JARVIS. Tüm sistemler hazır. Nasıl yardımcı olabilirim?');$('#replay').onclick=async()=>{if(currentAudio&&currentAudio.paused&&voiceUrl){await audioMeter.start('playback',currentAudio);currentAudio.play().catch(()=>speak(lastSpoken))}else if(lastSpoken)speak(lastSpoken)};
$('#volume').value=localStorage.getItem('jarvisVolume')??'70';$('#volumeText').textContent=$('#volume').value+'%';$('#volume').oninput=e=>{$('#volumeText').textContent=e.target.value+'%';localStorage.setItem('jarvisVolume',e.target.value);if(currentAudio)currentAudio.volume=Number(e.target.value)/100;if(e.target.value==='0'){stopVoice();mode('idle')}};
const bars=$('#bars');for(let n=0;n<24;n++)bars.append(document.createElement('i'));
window.addEventListener('jarvis:audio',e=>bars.querySelectorAll('i').forEach((bar,n)=>{bar.style.height=(2+(e.detail.frequencies[n]||0)*24)+'px'}));
function clock(){$('#clock').textContent=new Date().toLocaleTimeString('tr-TR',{timeZone:'Europe/Istanbul'})}clock();setInterval(clock,1000);

$('#open-voice-modal').onclick=()=>{
  $('#eleven-key').value=localStorage.getItem('jarvisElevenLabsKey')||'';
  $('#voice-modal-status').textContent='';
  $('#voice-gate').hidden=false;
};
$('#close-voice-modal').onclick=()=>{$('#voice-gate').hidden=true};
$('#save-voice-modal').onclick=async()=>{
  const val=$('#eleven-key').value.trim();
  if(val){
    localStorage.setItem('jarvisElevenLabsKey',val);
    $('#voice-modal-status').textContent='Anahtar kaydedildi. JARVIS sesi test ediliyor...';
    try{
      await speak('Jarvis ses sistemi doğrulandı efendim. Sistemler emrinizde.');
      $('#voice-modal-status').textContent='Ses doğrulandı! IKne3meq5aSn9XLyUdCD sesi aktif.';
    }catch(err){
      $('#voice-modal-status').textContent='Hata: '+(err.message||'Ses oluşturulamadı.');
    }
  }else{
    localStorage.removeItem('jarvisElevenLabsKey');
    $('#voice-modal-status').textContent='Anahtar kaldırıldı. Varsayılan ses kullanılacak.';
  }
};
$('#clear-voice-modal').onclick=()=>{
  localStorage.removeItem('jarvisElevenLabsKey');
  $('#eleven-key').value='';
  $('#voice-modal-status').textContent='Anahtar temizlendi.';
};

const micIcon='<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="9" y="3" width="6" height="11" rx="3"/><path d="M6 10v2a6 6 0 0 0 12 0v-2M12 18v3m-3 0h6"/></svg>';
$('#mic-btn').innerHTML=micIcon;
const SpeechRecognition=window.SpeechRecognition||window.webkitSpeechRecognition;
let recognition=null,recognizing=false;
if(SpeechRecognition){
  recognition=new SpeechRecognition();
  recognition.continuous=false;
  recognition.interimResults=true;
  recognition.lang='tr-TR';
  recognition.onstart=()=>{
    recognizing=true;mode('listening');void audioMeter.start('microphone');
    $('#mic-btn').classList.add('listening');
    $('#mic-btn').textContent='⏹';
    $('#prompt').placeholder='Dinleniyor... Konuşun...';
  };
  recognition.onresult=e=>{
    let transcript='';
    for(let i=0;i<e.results.length;i++) transcript+=e.results[i][0].transcript;
    $('#prompt').value=transcript;
    if(e.results[0].isFinal){
      recognition.stop();
      send(transcript);
    }
  };
  recognition.onend=()=>{
    if(coreMode==='listening'){audioMeter.stop();mode('idle')}
    recognizing=false;
    $('#mic-btn').classList.remove('listening');
    $('#mic-btn').innerHTML=micIcon;
    $('#prompt').placeholder='JARVIS’e bir şey söyle...';
  };
  recognition.onerror=()=>{
    audioMeter.stop();mode('error');
    recognizing=false;
    $('#mic-btn').classList.remove('listening');
    $('#mic-btn').innerHTML=micIcon;
    $('#prompt').placeholder='JARVIS’e bir şey söyle...';
  };
  $('#mic-btn').onclick=()=>{
    if(recognizing) recognition.stop();
    else{stopVoice();try{recognition.start()}catch{}}
  };
}else{
  $('#mic-btn').disabled=true;$('#mic-btn').title='Bu tarayıcı ses tanımayı desteklemiyor.';const listen=document.querySelector('.core-listen');if(listen){listen.disabled=true;listen.title='Ses tanıma için Chrome veya Safari kullan.'}const hint=$('#core-mic-hint');if(hint)hint.textContent='Bu tarayıcıda mesaj yazarak konuşabilirsin.';
}

// Modal remains the original voice settings flow; keyboard focus is contained.
let settingsOpener=null;
const openSettings=$('#open-voice-modal').onclick;
$('#open-voice-modal').onclick=()=>{settingsOpener=document.activeElement;openSettings();$('#voice-gate').querySelector('input')?.focus()};
$('#close-voice-modal').onclick=()=>{$('#voice-gate').hidden=true;settingsOpener?.focus()};
$('#voice-gate').addEventListener('keydown',e=>{
  if(e.key==='Escape'){$('#close-voice-modal').click();return}
  if(e.key!=='Tab')return;
  const controls=[...$('#voice-gate').querySelectorAll('button,input,select')].filter(el=>!el.disabled&&!el.hidden);
  const first=controls[0],last=controls.at(-1);
  if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}
  else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}
});
window.addEventListener('pagehide',()=>audioMeter.stop(true));

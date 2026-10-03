"""Natural Turkish conversation and bounded model-proposed computer actions."""
import base64
import json
import urllib.error
import urllib.request

from .computer import valid_action


def tool(name, description, properties=None, required=None):
    return {'type':'function','function':{'name':name,'description':description,
            'parameters':{'type':'object','properties':properties or {},'required':required or []}}}


STRING=lambda description: {'type':'string','description':description}
TOOLS=[
    tool('open_app','Kullanıcının açıkça istediği uygulamayı aç.',{'name':{'type':'string','enum':['chrome','not defteri','hesap makinesi','gezgin']}},['name']),
    tool('search_web','Kullanıcının istediği konuyu Google üzerinde ara.',{'query':STRING('Aranacak konu')},['query']),
    tool('system_info','Bilgisayarın işlemci ve RAM durumunu öğren.'),
    tool('find_file','Masaüstü, Belgeler ve İndirilenler içinde dosya adı ara.',{'name':STRING('Dosya adının bir kısmı')},['name']),
    tool('add_note','Kullanıcının açıkça kaydetmek istediği notu yaz.',{'text':STRING('Not metni')},['text']),
    tool('remind_me','Dakika cinsinden hatırlatma kaydet.',{'minutes':{'type':'integer'},'text':STRING('Hatırlatma metni')},['minutes','text']),
    tool('write_document','Kullanıcının istediği yeni TXT belgesini Belgeler/Jarvis klasörüne oluştur. Var olan dosyanın üzerine yazılmaz.',{'title':STRING('Uzantısız kısa dosya adı'),'text':STRING('Belge içeriği')},['title','text']),
    tool('type_text','Kullanıcının belirttiği tek satırlık metni önceki etkin pencereye yaz. Onay ister.',{'text':STRING('Yazılacak metin, yeni satır olmadan')},['text']),
    tool('press_keys','Önceki etkin pencerede izinli tuşlara bas. Onay ister.',{'keys':{'type':'array','items':{'type':'string'}}},['keys']),
    tool('click_screen','Ekran görüntüsündeki hedefi fiziksel ekran koordinatlarıyla tıkla. Onay ister.',{'x':{'type':'integer'},'y':{'type':'integer'}},['x','y']),
]

SYSTEM=('Sen JARVIS adlı Türkçe kişisel asistansın. Kullanıcıyla doğal ve samimi ama kısa konuş. '
        'Kullanıcı soru sorarsa yanıtla. Bilgisayar işleminden açıkça söz ederse uygun araç öner. '
        'Araç çalışmadan iş yapılmış gibi davranma. Ekran görüntüsü yoksa koordinat tahmin ederek tıklama. '
        'Kullanıcı istemeden özel bilgileri araştırma veya gönderme. Komut kabuğu ve keyfi kod çalıştırma aracın yok. '
        'Arayüz Türkçe; açıklamaları Türkçe yaz. Verilmeyen bilgiyi uydurma.')


class Agent:
    def __init__(self):
        self.key=''
        self.provider='auto'
        self.openai_model='gpt-4.1-mini'
        self.local_model='qwen3:4b'
        self.history=[]

    def selected_provider(self):
        if self.provider=='openai': return 'openai' if self.key else None
        if self.provider=='ollama': return 'ollama' if self._ollama_running() else None
        if self.key: return 'openai'
        return 'ollama' if self._ollama_running() else None

    @staticmethod
    def _ollama_running():
        try:
            with urllib.request.urlopen('http://127.0.0.1:11434/api/tags',timeout=0.5) as response:
                return response.status==200
        except OSError:
            return False

    def ask(self, text, image=None, screen_size=None):
        provider=self.selected_provider()
        if not provider:
            return {'text':'Sohbet motoru bağlı değil. Ayarlar’dan OpenAI API anahtarı gir veya Ollama’yı kurup qwen3:4b modelini indir. Böylece benimle doğal sohbet edebilirsin.', 'actions':[]}
        if image and provider!='openai':
            return {'text':'Ekran analizi için görüntü destekli OpenAI bağlantısını seç.', 'actions':[]}
        content=text
        if image:
            content=[{'type':'text','text':text+f' Ekran boyutu: {screen_size[0]}x{screen_size[1]}. '
                      'Görüntü küçültülmüş olabilir; tıklama koordinatlarını fiziksel ekran boyutuna göre ver.'},
                     {'type':'image_url','image_url':{'url':'data:image/jpeg;base64,'+base64.b64encode(image).decode()}}]
        messages=[{'role':'system','content':SYSTEM}]+self.history[-12:]+[{'role':'user','content':content}]
        payload={'model':self.openai_model if provider=='openai' else self.local_model,
                 'messages':messages,'tools':TOOLS,'stream':False}
        if provider=='ollama': payload['think']=False
        url='https://api.openai.com/v1/chat/completions' if provider=='openai' else 'http://127.0.0.1:11434/api/chat'
        headers={'Content-Type':'application/json'}
        if provider=='openai': headers['Authorization']='Bearer '+self.key
        request=urllib.request.Request(url,data=json.dumps(payload).encode(),headers=headers)
        try:
            with urllib.request.urlopen(request,timeout=120 if provider=='ollama' else 45) as response:
                data=json.load(response)
            message=data['choices'][0]['message'] if provider=='openai' else data['message']
            actions=[]
            for call in (message.get('tool_calls') or [])[:5]:
                function=call.get('function',{})
                args=function.get('arguments',{})
                if isinstance(args,str): args=json.loads(args)
                action=valid_action(function.get('name'),args)
                if action['name']=='click_screen' and not image:
                    continue
                actions.append(action)
            answer=message.get('content') or ''
            if not isinstance(answer,str): answer=''
            self.history.extend([{'role':'user','content':text},
                                 {'role':'assistant','content':answer or ('İşlem önerisi: '+', '.join(a['name'] for a in actions))}])
            self.history=self.history[-16:]
            return {'text':answer.strip(), 'actions':actions}
        except urllib.error.HTTPError as exc:
            detail={401:'API anahtarı geçersiz.',404:'Model bulunamadı; Ayarlar’daki model adını kontrol et.',
                    429:'API kotası veya hız sınırına ulaşıldı.'}.get(exc.code,f'AI servisi HTTP {exc.code} hatası verdi.')
        except (OSError,ValueError,KeyError,IndexError,TypeError):
            detail='Sohbet motoruna erişilemedi. Bağlantıyı ve model ayarını kontrol et.'
        return {'text':detail,'actions':[]}

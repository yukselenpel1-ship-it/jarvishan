"""Outbound-only Windows bridge for the optional Vercel web app."""
import json
import threading
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

from .core import Assistant
from .computer import valid_action, perform


REMOTE_ACTIONS = {'open_app','search_web','system_info','find_file','add_note','remind_me'}


def valid_url(url):
    parsed=urlparse(url)
    return (parsed.scheme=='https' and bool(parsed.netloc) and not parsed.username and not parsed.password
            and not parsed.path.strip('/') and not parsed.query and not parsed.fragment) or (
            parsed.scheme=='http' and parsed.hostname in ('127.0.0.1','localhost')
            and not parsed.username and not parsed.password and not parsed.path.strip('/') and not parsed.query)


class RemoteBridge:
    def __init__(self,url,token,events):
        if not valid_url(url) or not isinstance(token,str) or len(token)<16:
            raise ValueError('Köprü adresi veya anahtarı geçersiz.')
        self.url=url.rstrip('/')
        self.token=token
        self.events=events
        self.stop=threading.Event()
        self.assistant=Assistant()
        self.last_notice=0
        self.thread=threading.Thread(target=self.run,daemon=True)

    def start(self): self.thread.start()
    def close(self): self.stop.set()

    def request(self,method,path,body=None):
        data=json.dumps(body).encode() if body is not None else None
        headers={'Authorization':'Bearer '+self.token,'Content-Type':'application/json'}
        req=urllib.request.Request(self.url+path,data=data,headers=headers,method=method)
        with urllib.request.urlopen(req,timeout=12) as response:
            return json.load(response)

    def process(self,job):
        action=job.get('action') or {}
        if action.get('name') not in REMOTE_ACTIONS:
            return 'Bu işlem uzaktan kullanıma açık değil.'
        try:
            validated=valid_action(action['name'],action.get('args'))
            return str(perform(validated,self.assistant))[:4000]
        except (ValueError,TypeError,KeyError,OSError):
            return 'İşlem Windows üzerinde tamamlanamadı.'

    def run(self):
        while not self.stop.is_set():
            try:
                response=self.request('GET','/api/bridge')
                job=response.get('job')
                if job and isinstance(job.get('id'),str):
                    result=self.process(job)
                    self.request('POST','/api/bridge',{'id':job['id'],'result':result})
                    self.events.put(('notice','Mobil istek: '+result[:160]))
            except Exception as exc:
                # Network failures do not stop the desktop application.
                if time.monotonic()-self.last_notice>60:
                    reason='Köprü anahtarı reddedildi.' if isinstance(exc,urllib.error.HTTPError) and exc.code==401 else 'Mobil köprüye erişilemedi. Vercel adresini ve interneti kontrol et.'
                    self.events.put(('notice',reason))
                    self.last_notice=time.monotonic()
            self.stop.wait(3)

import math
import queue
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox

from .core import Assistant, HELP
from .voice import Voice

BG = '#080d17'
PANEL = '#111b2b'
CYAN = '#67e8f9'
TEXT = '#e6edf7'
MUTED = '#8496b1'


class JarvisApp:
    def __init__(self, root):
        self.root = root
        self.assistant = Assistant()
        self.events = queue.Queue()
        self.voice = Voice(self.events)
        self.busy = False
        self.wake = False
        self.voice_consent = False
        self.phase = 0
        root.title('J.A.R.V.I.S. • Personal Intelligence / v0.1')
        root.geometry('1180x800')
        root.minsize(840, 680)
        root.configure(bg=BG)
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)
        side = tk.Frame(root, bg=PANEL, width=225)
        side.grid(row=0, column=0, sticky='nsew')
        side.grid_propagate(False)
        tk.Label(side, text='J /', font=('Segoe UI', 36, 'bold'), bg=PANEL, fg=CYAN).pack(anchor='w', padx=24, pady=(26, 0))
        tk.Label(side, text='J.A.R.V.I.S.', font=('Segoe UI', 19, 'bold'), bg=PANEL, fg=TEXT).pack(anchor='w', padx=24)
        tk.Label(side, text='PERSONAL INTELLIGENCE', font=('Segoe UI', 8), bg=PANEL, fg=MUTED).pack(anchor='w', padx=24, pady=(5, 28))
        self.button(side, '◈  Komut merkezi', lambda: self.entry.focus_set()).pack(fill='x', padx=16, pady=5)
        self.button(side, '▤  Yerel hafıza', lambda: self.submit('notlarım')).pack(fill='x', padx=16, pady=5)
        self.button(side, '▦  Sistem bilgileri', lambda: self.submit('sistem bilgisi')).pack(fill='x', padx=16, pady=5)
        self.button(side, '⚙  AI ayarları', self.settings).pack(fill='x', padx=16, pady=5)
        self.button(side, '?  Komut rehberi', lambda: self.add('JARVIS', HELP)).pack(fill='x', padx=16, pady=5)
        self.tts = tk.BooleanVar(value=True)
        tk.Checkbutton(side, text='Sesli yanıt', variable=self.tts, command=self.toggle_tts,
                       bg=PANEL, fg=TEXT, selectcolor=BG, activebackground=PANEL,
                       activeforeground=CYAN).pack(anchor='w', padx=19, pady=(30, 8))
        self.wake_button = self.button(side, '○  Jarvis modu: kapalı', self.toggle_wake)
        self.wake_button.pack(fill='x', padx=16, pady=5)
        self.clock = tk.Label(side, text='', font=('Segoe UI', 22), fg=TEXT, bg=PANEL)
        self.clock.pack(side='bottom', anchor='w', padx=24, pady=30)
        tk.Label(side, text='v0.1.0  /  WINDOWS\nYerel komut motoru', font=('Segoe UI', 9), fg=MUTED, bg=PANEL,
                 justify='left').pack(side='bottom', anchor='w', padx=24)
        main = tk.Frame(root, bg=BG)
        main.grid(row=0, column=1, sticky='nsew', padx=28, pady=22)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(4, weight=1)
        tk.Label(main, text='KOMUT MERKEZİ', fg=MUTED, bg=BG, font=('Segoe UI', 10, 'bold')).grid(row=0, sticky='w')
        self.status = tk.Label(main, text='●  HAZIR', fg=CYAN, bg=BG, font=('Segoe UI', 10))
        self.status.grid(row=0, sticky='e')
        tk.Label(main, text='İyi ki geldin. Hazırım.', font=('Segoe UI', 26, 'bold'), fg=TEXT, bg=BG).grid(row=1, sticky='w', pady=(18, 0))
        hero = tk.Frame(main, bg=BG)
        hero.grid(row=2, sticky='ew', pady=5)
        hero.columnconfigure(1, weight=1)
        self.orb = tk.Canvas(hero, width=225, height=205, bg=BG, highlightthickness=0)
        self.orb.grid(row=0, column=0)
        detail = tk.Frame(hero, bg=BG)
        detail.grid(row=0, column=1, sticky='w', padx=18)
        tk.Label(detail, text='SEN SÖYLE.\nJARVIS HALLETSİN.', font=('Segoe UI', 17, 'bold'), fg=TEXT, bg=BG,
                 justify='left').pack(anchor='w')
        tk.Label(detail, text='Uygulamalar · Arama · Hafıza\nTürkçe sesli ve yazılı komutlar', font=('Segoe UI', 10),
                 fg=MUTED, bg=BG, justify='left').pack(anchor='w', pady=12)
        quick = tk.Frame(main, bg=BG)
        quick.grid(row=3, sticky='ew', pady=(0, 14))
        for i, (title, cmd) in enumerate([('SquadCraft ↗', 'SquadCraft aç'), ('Saati söyle', 'saat kaç'), ('Notlarım', 'notlarım')]):
            quick.columnconfigure(i, weight=1)
            self.button(quick, title, lambda c=cmd: self.submit(c)).grid(row=0, column=i, sticky='ew', padx=(0, 6))
        self.log = tk.Text(main, bg=PANEL, fg=TEXT, insertbackground=CYAN, wrap='word', relief='flat',
                           padx=18, pady=16, font=('Segoe UI', 11), state='disabled', height=10)
        self.log.grid(row=4, sticky='nsew')
        self.log.tag_configure('label', foreground=CYAN, font=('Segoe UI', 9, 'bold'))
        row = tk.Frame(main, bg=PANEL)
        row.grid(row=5, sticky='ew', pady=(14, 0))
        row.columnconfigure(0, weight=1)
        self.entry = tk.Entry(row, bg=PANEL, fg=TEXT, insertbackground=CYAN, relief='flat', font=('Segoe UI', 12))
        self.entry.grid(row=0, column=0, sticky='ew', padx=15, pady=16)
        self.entry.bind('<Return>', lambda e: self.send())
        self.button(row, 'Mikrofon', self.listen).grid(row=0, column=1, padx=4)
        self.button(row, 'Gönder →', self.send, accent=True).grid(row=0, column=2, padx=8)
        tk.Label(main, text='Ses tanıma: Google / internet gerekir · AI sohbeti: isteğe bağlı API',
                 fg=MUTED, bg=BG, font=('Segoe UI', 9)).grid(row=6, sticky='w', pady=(12, 0))
        self.add('JARVIS', 'Komut merkezi hazır. “Yardım” yazarak başlayabilirsin.\nÖrnek: not al yarın SquadCraft üzerinde çalış')
        self.entry.focus_set()
        self.animate()
        self.poll()
        self.tick()

    def button(self, parent, text, command, accent=False):
        return tk.Button(parent, text=text, command=command, bg=CYAN if accent else '#1b2b42',
                         fg=BG if accent else TEXT, activebackground='#3c7184', activeforeground=TEXT,
                         font=('Segoe UI', 10), relief='flat', bd=0, cursor='hand2', padx=12, pady=11)

    def add(self, who, text):
        self.log.configure(state='normal')
        self.log.insert('end', f'{who}  /  {datetime.now():%H:%M}\n', 'label')
        self.log.insert('end', text + '\n\n')
        self.log.configure(state='disabled')
        self.log.see('end')

    def send(self):
        text = self.entry.get().strip()
        if text and not self.busy:
            self.entry.delete(0, 'end')
            self.submit(text)

    def submit(self, text):
        if self.busy:
            self.add('SİSTEM', 'Önceki komut tamamlanıyor; birazdan tekrar deneyebilirsin.')
            return
        self.busy = True
        self.status.configure(text='●  İŞLENİYOR')
        self.add('SEN', text)
        def work():
            try:
                result = self.assistant.execute(text).text
            except Exception:
                result = 'Komut tamamlanamadı. Ayarları kontrol edip tekrar deneyebilirsin.'
            self.events.put(('result', result))
        threading.Thread(target=work, daemon=True).start()

    def consent(self):
        if self.voice_consent:
            return True
        self.voice_consent = messagebox.askokcancel('Mikrofon kullanımı',
            'Sesini metne çevirmek için kayıtlar Google ses tanıma servisine gönderilir. '
            'Jarvis modu açıkken duyulan cümleler de bu servise gönderilir.\n\n'
            'Bu sürümde çevrimdışı uyandırma modeli yoktur. Mikrofon kullanımına devam edilsin mi?')
        return self.voice_consent

    def listen(self):
        if self.consent():
            self.voice.listen()

    def toggle_wake(self):
        if not self.wake:
            if not self.consent():
                return
            if self.voice.listener and self.voice.listener.is_alive():
                self.add('SİSTEM', 'Mevcut dinleme tamamlandıktan sonra Jarvis modunu aç.')
                return
            self.wake = True
            self.voice.listen(continuous=True)
        else:
            self.wake = False
            self.voice.stop_listening()
        self.wake_button.configure(text='●  Jarvis modu: açık' if self.wake else '○  Jarvis modu: kapalı')

    def toggle_tts(self):
        self.voice.enabled = self.tts.get()

    def settings(self):
        win = tk.Toplevel(self.root)
        win.title('AI ayarları')
        win.configure(bg=PANEL)
        win.geometry('510x360')
        win.transient(self.root)
        tk.Label(win, text='AI sohbet bağlantısı', bg=PANEL, fg=TEXT, font=('Segoe UI', 18, 'bold')).pack(anchor='w', padx=24, pady=20)
        tk.Label(win, text='API anahtarı (yalnızca bu oturumda tutulur)', bg=PANEL, fg=MUTED).pack(anchor='w', padx=24)
        key = tk.Entry(win, show='•', bg=BG, fg=TEXT, insertbackground=CYAN, relief='flat')
        key.insert(0, self.assistant.api_key)
        key.pack(fill='x', padx=24, pady=8, ipady=8)
        tk.Label(win, text='Model', bg=PANEL, fg=MUTED).pack(anchor='w', padx=24)
        model = tk.Entry(win, bg=BG, fg=TEXT, insertbackground=CYAN, relief='flat')
        model.insert(0, self.assistant.model)
        model.pack(fill='x', padx=24, pady=8, ipady=8)
        tk.Label(win, text='AI sohbet metni OpenAI’ye gönderilir. API kullanımı ayrı ücretlidir.\n'
                 'Yerel notlar otomatik gönderilmez. Anahtar diske yazılmaz.',
                 bg=PANEL, fg=MUTED, justify='left', wraplength=465).pack(anchor='w', padx=24, pady=8)
        def save():
            if self.busy:
                messagebox.showinfo('Bekleyen komut', 'Komut tamamlandıktan sonra ayarları kaydet.', parent=win)
                return
            self.assistant.api_key = key.get().strip()
            self.assistant.model = model.get().strip() or 'gpt-4.1-mini'
            self.assistant.history.clear()
            win.destroy()
            self.add('SİSTEM', 'AI ayarları güncellendi. Sohbet bağlamı temizlendi.')
        self.button(win, 'Kaydet', save, True).pack(anchor='e', padx=24)

    def poll(self):
        try:
            while True:
                kind, text = self.events.get_nowait()
                if kind == 'result':
                    self.busy = False
                    self.add('JARVIS', text)
                    self.voice.say(text)
                    self.status.configure(text='●  HAZIR')
                elif kind == 'command':
                    self.submit(text)
                elif kind == 'status':
                    if not self.busy:
                        self.status.configure(text='●  ' + text.upper())
                    if text == 'Hazır' and self.wake:
                        self.wake = False
                        self.wake_button.configure(text='○  Jarvis modu: kapalı')
                else:
                    self.add('SİSTEM', text)
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

    def tick(self):
        self.clock.configure(text=datetime.now().strftime('%H:%M\n%d.%m.%Y'))
        try:
            for _, text in self.assistant.memory.due():
                self.add('HATIRLATMA', text)
                self.voice.say('Hatırlatma: ' + text)
        except Exception:
            self.add('SİSTEM', 'Hatırlatmalar okunamadı. Yerel veri klasörünün yazılabilir olduğunu kontrol et.')
        self.root.after(1000, self.tick)

    def animate(self):
        self.phase += 0.045
        c = self.orb
        c.delete('all')
        cx, cy = 112, 102
        pulse = 4 * math.sin(self.phase * 2)
        for radius, color in [(91, '#152b43'), (77, '#20526b'), (63 + pulse, '#40bcd3')]:
            c.create_oval(cx-radius, cy-radius, cx+radius, cy+radius, outline=color, width=2)
        for i in range(36):
            a = i * math.tau / 36 + self.phase
            r = 85
            c.create_line(cx+math.cos(a)*r, cy+math.sin(a)*r,
                          cx+math.cos(a)*(r+5), cy+math.sin(a)*(r+5), fill='#5ba6c6')
        for i in range(3):
            c.create_arc(cx-73, cy-73, cx+73, cy+73, start=(self.phase*45+i*120)%360,
                         extent=60, style='arc', outline=CYAN, width=3)
        c.create_text(cx, cy-6, text='J', fill=CYAN, font=('Segoe UI', 40, 'bold'))
        c.create_text(cx, cy+30, text='ACTIVE' if self.busy or self.voice.speaking.is_set() else 'ONLINE',
                      fill=MUTED, font=('Segoe UI', 8))
        self.root.after(40, self.animate)

    def close(self):
        self.voice.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    JarvisApp(root)
    root.mainloop()

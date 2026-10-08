import { Component, useEffect, useRef, useState, type ReactNode } from 'react';
import { createRoot } from 'react-dom/client';
import { flushSync } from 'react-dom';
import Aurora from './reactbits/Aurora';
import Particles from './reactbits/Particles';
import Orb from './reactbits/Orb';
import DecryptedText from './reactbits/DecryptedText';
import BlurText from './reactbits/BlurText';
import SpotlightCard from './reactbits/SpotlightCard';
import Magnet from './reactbits/Magnet';
import StarBorder from './reactbits/StarBorder';
import AnimatedContent from './reactbits/AnimatedContent';
import './ui.css';

type CoreState = 'idle' | 'listening' | 'thinking' | 'speaking' | 'error';
type Preferences = { motion: boolean; particles: boolean; intensity: 'low' | 'full' };
const labels: Record<CoreState, string> = { idle: 'KONUŞMAYA HAZIR', listening: 'SENİ DİNLİYORUM', thinking: 'ANALİZ EDİLİYOR', speaking: 'JARVIS KONUŞUYOR', error: 'BAĞLANTIYI KONTROL ET' };
const systemMotion = matchMedia('(prefers-reduced-motion: reduce)');
function loadPreferences(): Preferences {
  try { return { motion: true, particles: true, intensity: 'full', ...JSON.parse(localStorage.getItem('jarvisUI') || '{}') }; }
  catch { return { motion: true, particles: true, intensity: 'full' }; }
}
let preferences = loadPreferences();
function usePreferences() {
  const [value, setValue] = useState(preferences);
  const [reduced, setReduced] = useState(systemMotion.matches);
  useEffect(() => {
    const change = () => setValue({ ...preferences });
    const media = () => setReduced(systemMotion.matches);
    window.addEventListener('jarvis:preferences', change); systemMotion.addEventListener('change', media);
    return () => { window.removeEventListener('jarvis:preferences', change); systemMotion.removeEventListener('change', media); };
  }, []);
  return { ...value, animate: value.motion && !reduced };
}
function savePreferences(patch: Partial<Preferences>) {
  preferences = { ...preferences, ...patch };
  localStorage.setItem('jarvisUI', JSON.stringify(preferences));
  document.documentElement.dataset.motion = preferences.motion && !systemMotion.matches ? 'on' : 'off';
  window.dispatchEvent(new Event('jarvis:preferences'));
}
function supportsWebGL() {
  try {
    const gl = document.createElement('canvas').getContext('webgl2');
    if (!gl) return false;
    gl.getExtension('WEBGL_lose_context')?.loseContext(); return true;
  } catch { return false; }
}
const webgl = supportsWebGL();
class EffectBoundary extends Component<{ children: ReactNode; fallback?: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() { return this.state.failed ? this.props.fallback ?? null : this.props.children; }
}
const colors = ['#00e5ff', '#008cff', '#9cf8ff'];
function Ambient() {
  const { animate, particles, intensity } = usePreferences();
  const [mobile, setMobile] = useState(matchMedia('(max-width: 760px)').matches);
  const [visible, setVisible] = useState(!document.hidden);
  const [slow, setSlow] = useState(false);
  useEffect(() => {
    const query = matchMedia('(max-width: 760px)');
    const resize = () => setMobile(query.matches);
    const visibility = () => setVisible(!document.hidden);
    query.addEventListener('change', resize); document.addEventListener('visibilitychange', visibility);
    // Sample a short window once; shed background GPU work if sustained FPS is low.
    let frame = 0, samples = 0, start = 0, raf = 0;
    const sample = (t: number) => {
      if (document.hidden) { start = 0; samples = 0; }
      else { if (!start) start = t; samples++; if (t - start > 3500) { setSlow(samples / ((t - start) / 1000) < 35); return; } }
      if (++frame < 900) raf = requestAnimationFrame(sample);
    };
    raf = requestAnimationFrame(sample);
    return () => { cancelAnimationFrame(raf); query.removeEventListener('change', resize); document.removeEventListener('visibilitychange', visibility); };
  }, []);
  const effects = animate && visible && webgl;
  return <div className="ambient" aria-hidden="true">
    <div className="ambient-grid" />
    {effects && !mobile && !slow && intensity === 'full' && <EffectBoundary><div className="aurora-layer"><Aurora colorStops={colors} speed={0.15} amplitude={0.65} blend={0.75} /></div></EffectBoundary>}
    {effects && particles && <EffectBoundary><div className="particle-layer"><Particles particleColors={colors} particleCount={mobile || slow || intensity === 'low' ? 28 : 110} particleBaseSize={35} alphaParticles speed={0.045} pixelRatio={1} /></div></EffectBoundary>}
  </div>;
}
function Core() {
  const { animate } = usePreferences();
  const [status, setStatus] = useState<CoreState>('idle');
  const [gpu, setGpu] = useState(webgl);
  const signal = useRef({ state: 'idle', level: 0 });
  const root = useRef<HTMLDivElement>(null);
  const meter = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const state = (event: Event) => {
      const next = (event as CustomEvent<CoreState>).detail;
      signal.current.state = next; setStatus(next);
    };
    const audio = (event: Event) => {
      const detail = (event as CustomEvent<{ level: number; frequencies: number[] }>).detail;
      signal.current.level = detail.level;
      root.current?.style.setProperty('--level', String(detail.level));
      meter.current?.querySelectorAll<HTMLElement>('i').forEach((bar, n) => { bar.style.height = `${2 + (detail.frequencies[n] ?? 0) * 28}px`; });
    };
    const container = root.current;
    const lost = (event: Event) => { event.preventDefault(); setGpu(false); };
    container?.addEventListener('webglcontextlost', lost, true);
    window.addEventListener('jarvis:state', state); window.addEventListener('jarvis:audio', audio);
    return () => { container?.removeEventListener('webglcontextlost', lost, true); window.removeEventListener('jarvis:state', state); window.removeEventListener('jarvis:audio', audio); };
  }, []);
  const fallback = <div className="core-fallback" />;
  return <div ref={root} className={`ai-core state-${status}`} data-state={status}>
    <div className="core-eyebrow">J.A.R.V.I.S. / NEURAL INTERFACE</div>
    <div className="core-stage">
      <div className="core-ring ring-one" /><div className="core-ring ring-two" /><div className="core-ring ring-three" />
      <div className="core-orb" aria-hidden="true">{gpu && animate ? <EffectBoundary fallback={fallback}><Orb hue={0} signalRef={signal} hoverIntensity={0.7} rotateOnHover backgroundColor="#02060b" /></EffectBoundary> : fallback}</div>
      <div className="core-heart" aria-hidden="true"><span>J</span></div>
      <div className="core-coordinates"><span>01 / NEURAL CORE</span><span>TR / VOICE LINK</span></div>
    </div>
    <div className="core-caption" role="status"><span className="state-code">{status.toUpperCase()}</span><h1>{labels[status]}</h1><p>Seninle düşünen. Seninle konuşan.</p></div>
    <div className="signal-meter" ref={meter} aria-hidden="true">{Array.from({ length: 24 }, (_, n) => <i key={n} />)}</div>
    <Magnet disabled={!animate || matchMedia('(pointer: coarse)').matches} padding={12} magnetStrength={12}>
      <StarBorder color="#00e5ff" speed="9s" backgroundColor="#071522" borderColor="#164153" textColor="#eafbff" type="button" className="core-listen" onClick={() => document.getElementById('mic-btn')?.click()}><span>◉</span> {status === 'listening' ? 'DİNLEMEYİ DURDUR' : 'SESLİ KONUŞ'}</StarBorder>
    </Magnet>
    <small className="core-hint" id="core-mic-hint">Mikrofon veya mesaj alanıyla başlayabilirsin.</small>
  </div>;
}
function Brand() {
  const { animate } = usePreferences();
  return <><strong aria-label="JARVIS">{animate ? <DecryptedText text="JARVIS" animateOn="view" sequential speed={65} characters="JARVIS01" /> : 'JARVIS'}</strong><small>KİŞİSEL YAPAY ZEKÂ SİSTEMİ</small></>;
}
function Introduction() {
  const { animate } = usePreferences();
  const content = <><div className="intro-tag">KOMUT MERKEZİ / 01</div>{animate ? <BlurText text="İyi fikirler, birlikte başlar." delay={55} stepDuration={0.15} className="intro-title" /> : <p className="intro-title">İyi fikirler, birlikte başlar.</p>}<p className="intro-copy">Sor, planla, konuş. Bilgisayar işlemleri her zaman senin onayınla.</p></>;
  return animate ? <AnimatedContent distance={12} duration={0.6} animateOpacity>{content}</AnimatedContent> : content;
}
function Sidebar() {
  const [active, setActive] = useState('core');
  const navigate = (target: string) => {
    setActive(target);
    if (target === 'settings') { document.getElementById('open-voice-modal')?.click(); return; }
    document.getElementById(target)?.scrollIntoView({ behavior: systemMotion.matches ? 'instant' : 'smooth', block: 'center' });
    if (target === 'chat-panel') document.getElementById('prompt')?.focus({ preventScroll: true });
  };
  return <nav className="sidebar" aria-label="JARVIS gezinme"><a href="#core" className="sidebar-logo" aria-label="Ana merkez">J</a><div className="nav-items">{[['core','◈','Ana merkez'],['chat-panel','⌁','Sohbet'],['system-panel','▤','Sistem'],['audio-panel','♫','Ses sistemi'],['settings','⚙','Ayarlar']].map(([id, icon, title]) => <button type="button" key={id} className={active === id ? 'active' : ''} aria-label={title} aria-current={active === id ? 'page' : undefined} onClick={() => navigate(id)}><span aria-hidden="true">{icon}</span><span className="nav-label">{title}</span></button>)}</div><span className="sidebar-bottom">J / 01</span></nav>;
}
function Settings() {
  const value = usePreferences();
  return <section className="ui-settings"><div className="settings-section-label">ARAYÜZ & PERFORMANS</div><label className="setting-row"><span>3D çekirdek ve animasyon<small>Sisteminin Reduced Motion tercihi korunur.</small></span><input type="checkbox" checked={value.motion} onChange={e => savePreferences({ motion: e.target.checked })} /></label><label className="setting-row"><span>Parçacık alanı<small>Mobil cihazda otomatik olarak azaltılır.</small></span><input type="checkbox" checked={value.particles} onChange={e => savePreferences({ particles: e.target.checked })} /></label><label className="setting-row"><span>Efekt yoğunluğu</span><select value={value.intensity} onChange={e => savePreferences({ intensity: e.target.value as Preferences['intensity'] })}><option value="full">Sinematik</option><option value="low">Hafif</option></select></label><div className="settings-notice">{!webgl ? 'WebGL bulunamadı. Hafif çekirdek etkin.' : systemMotion.matches ? 'Sistem tercihi: azaltılmış hareket.' : 'GPU yükünde arka plan efektleri otomatik azaltılır.'}</div></section>;
}
function mount(id: string, node: ReactNode) {
  const el = document.getElementById(id); if (el) flushSync(() => createRoot(el).render(node));
}
// Progressive enhancement: the original forms, IDs and backend contracts stay intact.
// Static legacy panel markup is mounted once, before client.js binds its handlers.
for (const panel of document.querySelectorAll<HTMLElement>('.panel')) {
  const markup = panel.innerHTML;
  panel.classList.add('enhanced-panel');
  flushSync(() => createRoot(panel).render(<SpotlightCard spotlightColor="rgba(0, 229, 255, 0.06)"><div className="legacy-panel" dangerouslySetInnerHTML={{ __html: markup }} /></SpotlightCard>));
}
savePreferences({});
mount('ambient-root', <Ambient />); mount('brand-root', <Brand />); mount('core-root', <Core />);
mount('intro-root', <Introduction />); mount('sidebar-root', <Sidebar />); mount('ui-settings-root', <Settings />);

document.documentElement.dataset.ui = "ready";

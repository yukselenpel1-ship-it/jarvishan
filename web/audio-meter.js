// Real RMS and frequency bins only. No synthetic speech amplitude.
export function createAudioMeter(onSample) {
  let context, source, stream, playback, analyserNode, frame = 0, generation = 0;
  const zero = () => onSample({ level: 0, frequencies: Array(24).fill(0) });
  function stop(release = false) {
    generation++; cancelAnimationFrame(frame);
    source?.disconnect(); source = null;
    analyserNode?.disconnect(); analyserNode = null;
    stream?.getTracks().forEach(track => track.stop()); stream = null;
    const old = context; context = null;
    if (old && old.state !== 'closed') {
      if (old === playback?.context && !release) void old.suspend().catch(() => {});
      else void old.close().catch(() => {});
    }
    if (release && playback) {
      if (playback.context !== old && playback.context.state !== 'closed') void playback.context.close().catch(() => {});
      playback = null;
    }
    zero();
  }
  async function start(kind, audio) {
    stop(); const token = generation;
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;
    try {
      if (kind === 'microphone') {
        const acquired = await navigator.mediaDevices.getUserMedia({ audio: true });
        if (token !== generation) { acquired.getTracks().forEach(track => track.stop()); return; }
        stream = acquired;
      }
      if (kind === 'playback' && playback && playback.audio !== audio) { void playback.context.close().catch(() => {}); playback = null; }
      const ctx = kind === 'playback' && playback ? playback.context : new AudioContext(); context = ctx;
      await ctx.resume();
      if (token !== generation) return;
      const analyser = ctx.createAnalyser(); analyserNode = analyser; analyser.fftSize = 256; analyser.smoothingTimeConstant = 0.6;
      source = kind === 'microphone' ? ctx.createMediaStreamSource(stream) : playback?.source || ctx.createMediaElementSource(audio);
      if (kind === 'playback') playback = { audio, context: ctx, source };
      source.connect(analyser);
      if (kind === 'playback') analyser.connect(ctx.destination);
      const wave = new Uint8Array(analyser.fftSize), bins = new Uint8Array(analyser.frequencyBinCount);
      let last = 0;
      const tick = t => {
        if (token !== generation) return;
        frame = requestAnimationFrame(tick);
        if (document.hidden || t - last < 32) return;
        last = t; analyser.getByteTimeDomainData(wave); analyser.getByteFrequencyData(bins);
        let sum = 0; for (const sample of wave) sum += ((sample - 128) / 128) ** 2;
        const volume = kind === 'playback' ? audio.volume : 1;
        onSample({ level: Math.min(1, Math.sqrt(sum / wave.length) * volume), frequencies: Array.from({ length: 24 }, (_, n) => bins[n * 3] / 255 * volume) });
      };
      frame = requestAnimationFrame(tick);
    } catch { if (token === generation) stop(); } // Permission denial never blocks speech recognition/playback.
  }
  return { start, stop };
}

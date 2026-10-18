import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from './api.js';
import Board from './components/Board.jsx';
import Keyboard from './components/Keyboard.jsx';

function getUserId() {
  try {
    const existing = localStorage.getItem('wordle-user-id');
    if (existing) return existing;
    const id = crypto.randomUUID();
    localStorage.setItem('wordle-user-id', id);
    return id;
  } catch { return crypto.randomUUID(); }
}
export default function App() {
  const [userId] = useState(getUserId);
  const [gameId, setGameId] = useState(null);
  const [guesses, setGuesses] = useState([]);
  const [draft, setDraft] = useState('');
  const [status, setStatus] = useState('idle');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [answer, setAnswer] = useState('');
  const [uncertain, setUncertain] = useState(false);
  const inFlight = useRef(false);
  const active = status === 'en_curso';

  async function start() {
    if (inFlight.current) return;
    inFlight.current = true; setBusy(true); setError('');
    try {
      const data = await api.start(userId);
      if (!data.partida_id) throw new Error('El servidor no devolvió una partida válida.');
      setGameId(data.partida_id); setGuesses([]); setDraft(''); setAnswer(''); setUncertain(false); setStatus('en_curso');
    } catch (err) { setError(err.message); }
    finally { inFlight.current = false; setBusy(false); }
  }

  const onKey = useCallback(async (key) => {
    if (!active || inFlight.current || uncertain || guesses.length >= 6) return;
    if (key === 'Backspace') { setDraft(value => value.slice(0, -1)); setError(''); return; }
    if (key !== 'Enter') {
      if (/^[A-ZÑ]$/.test(key)) { setDraft(value => value.length < 5 ? value + key : value); setError(''); }
      return;
    }
    if (draft.length !== 5) { setError('Escribe una palabra de cinco letras.'); return; }
    inFlight.current = true; setBusy(true); setError('');
    try {
      const data = await api.guess(gameId, userId, draft);
      if (!Array.isArray(data.resultado) || data.resultado.length !== 5 || !['en_curso', 'ganada', 'perdida'].includes(data.estado)) {
        const invalid = new Error('Respuesta inesperada. Recupera el estado de la partida.'); invalid.uncertain = true; throw invalid;
      }
      setGuesses(previous => [...previous, data.resultado]); setDraft(''); setStatus(data.estado); setAnswer(data.palabra_secreta || '');
    } catch (err) { setError(err.message); if (err.uncertain) setUncertain(true); }
    finally { inFlight.current = false; setBusy(false); }
  }, [active, uncertain, guesses.length, draft, gameId, userId]);

  async function recover() {
    if (inFlight.current) return;
    inFlight.current = true; setBusy(true); setError('');
    try {
      const data = await api.get(gameId);
      if (!data.partida || !Array.isArray(data.intentos)) throw new Error('No se pudo recuperar la partida.');
      setGuesses(data.intentos.map(attempt => attempt.resultado)); setStatus(data.partida.estado);
      setAnswer(data.partida.palabra_secreta || ''); setDraft(''); setUncertain(false);
    } catch (err) { setError(err.message); }
    finally { inFlight.current = false; setBusy(false); }
  }

  useEffect(() => {
    const handler = event => {
      if (event.ctrlKey || event.metaKey || event.altKey || event.isComposing) return;
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(event.target?.tagName) || event.target?.isContentEditable) return;
      // Let focused buttons handle Enter themselves.
      if (event.key === 'Enter' && event.target?.tagName === 'BUTTON') return;
      if (event.key === 'Enter' || event.key === 'Backspace' || /^[a-zñ]$/i.test(event.key)) {
        event.preventDefault(); onKey(event.key.length === 1 ? event.key.toUpperCase() : event.key);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onKey]);

  const message = busy ? 'Conectando…' : status === 'ganada' ? `¡Lo has conseguido! ${guesses.length} de 6 intentos.` : status === 'perdida' ? `Fin de la partida.${answer ? ` La palabra era ${answer}.` : ''}` : active ? `Intento ${Math.min(guesses.length + 1, 6)} de 6` : 'Una palabra. Cinco letras. Seis oportunidades.';
  return <main className="app">
    <header><div className="brand-mark" aria-hidden="true">W</div><div><p className="eyebrow">EL RETO DE LAS CINCO LETRAS</p><h1>Wordle<span className="version">v1.0</span></h1></div><span className="language">ES</span></header>
    <section className="game" aria-label="Juego Wordle" aria-busy={busy}>
      <div className="game-heading"><h2>Encuentra la palabra.</h2><p>Cada intento te acerca un poco más.</p></div>
      <p className={`status ${status === 'ganada' ? 'success' : ''}`} role="status" aria-live="polite">{message}</p>
      <Board guesses={guesses} draft={draft} active={active} />
      <div className="feedback"><p role="alert">{error}</p></div>
      {uncertain && <div className="recovery"><p>El intento podría haberse guardado. Recupera la partida antes de continuar.</p><button className="primary" disabled={busy} onClick={recover}>Recuperar partida</button></div>}
      <Keyboard guesses={guesses} onKey={onKey} disabled={!active || busy || uncertain} />
      {(!active || uncertain) && <button className="primary start" onClick={start} disabled={busy}>{gameId ? 'Nueva partida' : 'Empezar partida'}</button>}
    </section>
    <section className="guide" aria-label="Cómo jugar"><h2>Cada color es una pista</h2><div className="legend"><span><i className="correcto" />Letra y posición</span><span><i className="presente" />Otra posición</span><span><i className="ausente" />No está</span></div><p>Escribe con tu teclado o toca las letras. Pulsa Enviar para probar.</p></section>
    <footer><span>WORDLE · ESPAÑOL</span><span>Versión 1.0</span></footer>
  </main>;
}

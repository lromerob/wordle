const rows = ['QWERTYUIOP', 'ASDFGHJKLÑ', 'ZXCVBNM'];
const priority = { ausente: 1, presente: 2, correcto: 3 };
export function keyStates(guesses) {
  const states = {};
  for (const result of guesses.flat()) {
    if ((priority[result.estado] || 0) > (priority[states[result.letra]] || 0)) states[result.letra] = result.estado;
  }
  return states;
}
export default function Keyboard({ guesses, onKey, disabled }) {
  const states = keyStates(guesses);
  const key = (label, value = label) => <button type="button" key={label} disabled={disabled} className={`key ${states[label] || ''} ${label.length > 1 ? 'wide' : ''}`} onClick={() => onKey(value)} aria-label={label === '⌫' ? 'Borrar letra' : label}>{label}</button>;
  return <div className="keyboard" aria-label="Teclado virtual">
    {rows.map((row, index) => <div className="key-row" key={row}>
      {index === 2 && key('Enviar', 'Enter')}{[...row].map(letter => key(letter))}{index === 2 && key('⌫', 'Backspace')}
    </div>)}
  </div>;
}

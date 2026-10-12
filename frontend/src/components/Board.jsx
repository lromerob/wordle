const labels = { correcto: 'correcta', presente: 'en otra posición', ausente: 'ausente' };
export default function Board({ guesses, draft, active }) {
  return <div className="board" role="group" aria-label="Tablero de seis filas y cinco columnas">
    {Array.from({ length: 6 }, (_, row) => <div className="board-row" role="group" aria-label={`Intento ${row + 1}`} key={row}>
      {Array.from({ length: 5 }, (_, col) => {
        const result = guesses[row]?.[col];
        const letter = result?.letra || (active && row === guesses.length ? draft[col] : '') || '';
        return <span key={col} className={`tile ${result?.estado || (letter ? 'filled' : '')}`} aria-label={`${letter || 'vacía'}${result ? `, ${labels[result.estado]}` : ''}`}>{letter}</span>;
      })}
    </div>)}
  </div>;
}

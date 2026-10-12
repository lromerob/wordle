import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App.jsx';
import Board from './components/Board.jsx';
import { keyStates } from './components/Keyboard.jsx';
import { api } from './api.js';

const result = (word, state = 'ausente') => [...word].map(letra => ({ letra, estado: state }));
const response = (data, status = 200) => ({ ok: status < 400, status, json: async () => data });
function mockFetch(...replies) {
  const fetch = vi.fn();
  for (const reply of replies) fetch.mockResolvedValueOnce(reply);
  fetch.mockRejectedValue(new Error('Unexpected request: external network forbidden'));
  vi.stubGlobal('fetch', fetch);
  return fetch;
}
async function start() {
  const user = userEvent.setup();
  render(<App />);
  await user.click(screen.getByRole('button', { name: 'Empezar partida' }));
  await screen.findByText('Intento 1 de 6');
  return user;
}
function type(word) { for (const key of word) fireEvent.keyDown(window, { key }); }
function submit() { fireEvent.keyDown(window, { key: 'Enter' }); }

describe('Wordle v1.0', () => {
  it('renders six rows, five cells each, and an inactive keyboard', () => {
    mockFetch(); render(<App />);
    const board = screen.getByRole('group', { name: 'Tablero de seis filas y cinco columnas' });
    const rows = within(board).getAllByRole('group');
    expect(rows).toHaveLength(6);
    rows.forEach(row => expect(row.children).toHaveLength(5));
    expect(screen.getByRole('button', { name: 'A', exact: true })).toBeDisabled();
    expect(screen.getByText('v1.0')).toBeInTheDocument();
  });

  it('starts with the API query contract, accepts physical keys, wins and disables input', async () => {
    const fetch = mockFetch(response({ partida_id: 'g1' }), response({ resultado: result('CASAS', 'correcto'), estado: 'ganada', intentos_usados: 1, palabra_secreta: null }));
    await start(); type('casas'); submit();
    await screen.findByText('¡Lo has conseguido! 1 de 6 intentos.');
    expect(fetch.mock.calls[0][0]).toContain('/game/nueva?usuario_id=');
    expect(fetch.mock.calls[0][1].method).toBe('POST');
    const body = JSON.parse(fetch.mock.calls[1][1].body);
    expect(body).toEqual({ partida_id: 'g1', usuario_id: localStorage.getItem('wordle-user-id'), palabra: 'CASAS' });
    expect(screen.getByRole('button', { name: 'A', exact: true })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Nueva partida' })).toBeEnabled();
  });

  it('supports virtual letters, deletion and client-side length validation', async () => {
    const fetch = mockFetch(response({ partida_id: 'g1' }));
    const user = await start();
    await user.click(screen.getByRole('button', { name: 'A', exact: true }));
    expect(screen.getByLabelText('Intento 1').textContent).toBe('A');
    await user.click(screen.getByRole('button', { name: 'Borrar letra' }));
    expect(screen.getByLabelText('Intento 1').textContent).toBe('');
    await user.click(screen.getByRole('button', { name: 'Enviar' }));
    expect(screen.getByRole('alert')).toHaveTextContent('cinco letras');
    expect(fetch).toHaveBeenCalledTimes(1);
  });

  it('keeps an invalid API guess editable without consuming a row', async () => {
    const fetch = mockFetch(response({ partida_id: 'g1' }), response({ detail: 'Palabra no válida' }, 400));
    await start(); type('ZZZZZ'); submit();
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Palabra no válida'));
    expect(screen.getByText('Intento 1 de 6')).toBeInTheDocument();
    expect(screen.getByLabelText('Intento 1').textContent).toBe('ZZZZZ');
    fireEvent.keyDown(window, { key: 'Backspace' });
    expect(screen.getByLabelText('Intento 1').textContent).toBe('ZZZZ');
    expect(fetch).toHaveBeenCalledTimes(2);
  });

  it('renders server evaluation colors and accessible descriptions', () => {
    render(<Board active={false} draft="" guesses={[[{ letra: 'C', estado: 'correcto' }, { letra: 'A', estado: 'presente' }, { letra: 'S', estado: 'ausente' }]]} />);
    expect(screen.getByLabelText('C, correcta')).toHaveClass('correcto');
    expect(screen.getByLabelText('A, en otra posición')).toHaveClass('presente');
    expect(screen.getByLabelText('S, ausente')).toHaveClass('ausente');
  });

  it('never downgrades keyboard evidence for repeated letters', () => {
    expect(keyStates([[{ letra: 'A', estado: 'correcto' }, { letra: 'A', estado: 'ausente' }], [{ letra: 'A', estado: 'presente' }]])).toEqual({ A: 'correcto' });
  });

  it('loses on the sixth guess, reveals the backend answer, and starts fresh', async () => {
    const replies = [response({ partida_id: 'g1' })];
    for (let n = 1; n <= 6; n++) replies.push(response({ resultado: result('PERRO'), estado: n === 6 ? 'perdida' : 'en_curso', intentos_usados: n, palabra_secreta: n === 6 ? 'CASAS' : null }));
    replies.push(response({ partida_id: 'g2' }));
    const fetch = mockFetch(...replies);
    const user = await start();
    for (let n = 1; n <= 6; n++) {
      type('PERRO'); submit();
      await screen.findByText(n === 6 ? 'Fin de la partida. La palabra era CASAS.' : `Intento ${n + 1} de 6`);
    }
    expect(screen.getByRole('button', { name: 'Enviar' })).toBeDisabled();
    submit(); expect(fetch).toHaveBeenCalledTimes(7);
    await user.click(screen.getByRole('button', { name: 'Nueva partida' }));
    await screen.findByText('Intento 1 de 6');
    expect(screen.getByLabelText('Intento 1').textContent).toBe('');
  });

  it('locks input and prevents duplicate requests while submitting', async () => {
    let release;
    const fetch = mockFetch(response({ partida_id: 'g1' }));
    await start();
    fetch.mockImplementationOnce(() => new Promise(resolve => { release = resolve; }));
    type('PERRO'); submit(); submit();
    expect(screen.getByRole('button', { name: 'Enviar' })).toBeDisabled();
    expect(fetch).toHaveBeenCalledTimes(2);
    release(response({ resultado: result('PERRO'), estado: 'en_curso', intentos_usados: 1, palabra_secreta: null }));
    await screen.findByText('Intento 2 de 6');
  });

  it('recovers uncertain writes by reading the game instead of replaying the guess', async () => {
    const fetch = mockFetch(response({ partida_id: 'g1' }));
    const user = await start();
    fetch.mockRejectedValueOnce(new TypeError('offline'));
    type('PERRO'); submit();
    await screen.findByRole('button', { name: 'Recuperar partida' });
    expect(screen.getByRole('button', { name: 'Enviar' })).toBeDisabled();
    fetch.mockResolvedValueOnce(response({ partida: { estado: 'en_curso', intentos_usados: 1 }, intentos: [{ resultado: result('PERRO') }] }));
    await user.click(screen.getByRole('button', { name: 'Recuperar partida' }));
    await screen.findByText('Intento 2 de 6');
    expect(fetch.mock.calls[2][0]).toContain('/game/g1');
    expect(fetch.mock.calls[2][1].method).toBeUndefined();
  });

  it('shows a start error and permits retry', async () => {
    mockFetch(response({ detail: 'No hay palabras disponibles' }, 500));
    const user = userEvent.setup(); render(<App />);
    await user.click(screen.getByRole('button', { name: 'Empezar partida' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('No hay palabras disponibles');
    expect(screen.getByRole('button', { name: 'Empezar partida' })).toBeEnabled();
  });

  it('ignores shortcuts and limits physical input to five Spanish letters', async () => {
    mockFetch(response({ partida_id: 'g1' })); await start();
    fireEvent.keyDown(window, { key: 'a', ctrlKey: true }); type('ñ123CASASX');
    expect(screen.getByLabelText('Intento 1').textContent).toBe('ÑCASA');
  });

  it('sends no Supabase secrets or authentication headers', async () => {
    const fetch = mockFetch(response({ partida_id: 'g1' }));
    await api.start('test-user');
    expect(fetch.mock.calls[0][1].headers).toBeUndefined();
    expect(fetch.mock.calls[0][0]).toContain('usuario_id=test-user');
  });
});

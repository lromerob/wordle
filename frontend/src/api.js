const base = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/+$/, '');
export class ApiError extends Error {
  constructor(message, uncertain = false) { super(message); this.uncertain = uncertain; }
}
async function request(path, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 12000);
  try {
    const response = await fetch(`${base}${path}`, { ...options, signal: controller.signal });
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      throw new ApiError(typeof data?.detail === 'string' ? data.detail : `Error del servidor (${response.status}).`, response.status >= 500);
    }
    if (!data) throw new ApiError('Respuesta del servidor no válida.', true);
    return data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError('No se pudo conectar con el servidor. Comprueba la conexión.', true);
  } finally { clearTimeout(timeout); }
}
export const api = {
  start: (userId) => request(`/game/nueva?${new URLSearchParams({ usuario_id: userId })}`, { method: 'POST' }),
  guess: (gameId, userId, word) => request('/game/intento', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ partida_id: gameId, usuario_id: userId, palabra: word }),
  }),
  get: (gameId) => request(`/game/${encodeURIComponent(gameId)}`),
};

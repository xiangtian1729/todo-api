/**
 * Thin in-memory token store that decouples the axios interceptor from
 * Zustand's internal localStorage structure.
 *
 * On module load we hydrate from the persisted Zustand auth-storage so that
 * page refreshes work without waiting for a React render cycle.
 */

function readPersistedToken(): string | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem('auth-storage');
    if (raw) {
      const parsed = JSON.parse(raw);
      return parsed?.state?.token ?? null;
    }
  } catch {
    // ignore parse errors
  }
  return null;
}

let _token: string | null = readPersistedToken();

export function getToken(): string | null {
  return _token;
}

export function setToken(token: string | null): void {
  _token = token;
}

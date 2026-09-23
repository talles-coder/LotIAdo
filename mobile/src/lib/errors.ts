import { isAxiosError } from 'axios';

/** Extrai uma mensagem amigável de um erro de API, priorizando o `detail` (409/422) do backend. */
export function getErrorMessage(err: unknown, fallback: string): string {
  if (isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    if (typeof detail === 'string') {
      return detail;
    }
  }
  return fallback;
}

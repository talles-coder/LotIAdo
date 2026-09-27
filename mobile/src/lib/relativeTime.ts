/** Formata um timestamp (ms epoch) como tempo relativo curto em pt-BR, ex.: "há 12 min". */
export function formatRelativeTime(timestampMs: number): string {
  const diffMin = Math.round((Date.now() - timestampMs) / 60000);
  if (diffMin < 1) return 'agora mesmo';
  if (diffMin < 60) return `há ${diffMin} min`;
  const diffHours = Math.round(diffMin / 60);
  if (diffHours < 24) return `há ${diffHours} h`;
  const diffDays = Math.round(diffHours / 24);
  return `há ${diffDays} d`;
}

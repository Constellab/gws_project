/** Format ISO date string (YYYY-MM-DD) to short readable format (e.g. "Feb 25") */
export function formatDate(isoDate: string): string {
  const d = new Date(isoDate + 'T00:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

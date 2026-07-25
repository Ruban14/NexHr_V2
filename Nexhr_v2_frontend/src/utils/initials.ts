/** First visible letter/digit for avatar / logo fallbacks. */
export function getInitial(
  ...candidates: Array<string | null | undefined>
): string {
  for (const candidate of candidates) {
    const trimmed = (candidate || '').trim();
    if (!trimmed) continue;
    const match = trimmed.match(/[\p{L}\p{N}]/u);
    if (match) return match[0].toUpperCase();
  }
  return 'N';
}

/** Treat blank / whitespace logo URLs as unset. */
export function hasLogoUrl(logo: string | null | undefined): boolean {
  return Boolean((logo || '').trim());
}

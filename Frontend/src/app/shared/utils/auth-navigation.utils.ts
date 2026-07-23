/**
 * Resolve a safe post-authentication redirect target.
 */
export function resolvePostAuthRedirect(url: string | null | undefined, fallback = '/app'): string {
  if (!url) {
    return fallback;
  }

  try {
    const parsed = new URL(url, 'http://local');
    const path = parsed.pathname;
    const suffix = `${parsed.search}${parsed.hash}`;

    if (path.startsWith('/app')) {
      return `${path}${suffix}`;
    }

    if (path === '/auth/login' || path === '/auth/register') {
      return `${path}${suffix}`;
    }

    return fallback;
  } catch {
    return fallback;
  }
}

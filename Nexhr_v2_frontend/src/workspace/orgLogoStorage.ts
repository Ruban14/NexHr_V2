/** Helpers for organization logo upload (backend-persisted for now). */

export function isDataUrl(value: string): boolean {
  return value.trim().toLowerCase().startsWith('data:image/');
}

export function isHttpUrl(value: string): boolean {
  const trimmed = value.trim().toLowerCase();
  return trimmed.startsWith('http://') || trimmed.startsWith('https://');
}

export function readImageFileAsDataUrl(file: File, maxBytes = 750_000): Promise<string> {
  return new Promise((resolve, reject) => {
    if (!file.type.startsWith('image/')) {
      reject(new Error('Please choose an image file (PNG, JPG, or WebP).'));
      return;
    }
    if (file.size > maxBytes) {
      reject(new Error('Image must be under 750 KB.'));
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const result = typeof reader.result === 'string' ? reader.result : '';
      if (!result.startsWith('data:image/')) {
        reject(new Error('Unable to read that image.'));
        return;
      }
      resolve(result);
    };
    reader.onerror = () => reject(new Error('Unable to read that image.'));
    reader.readAsDataURL(file);
  });
}

/** Clear legacy browser-only logos from earlier localStorage approach. */
export function clearLegacyOrgLogoCache(organizationId: string | null | undefined) {
  if (!organizationId) return;
  try {
    localStorage.removeItem(`nexhr_org_logo_${organizationId}`);
  } catch {
    // ignore
  }
}

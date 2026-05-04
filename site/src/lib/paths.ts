/** Безопасная склейка пути к статике в `public/` (учитывает base с/без завершающего «/»). */
export function siteAsset(relativePath: string): string {
  const b = import.meta.env.BASE_URL;
  const base = b.endsWith('/') ? b : `${b}/`;
  const path = relativePath.replace(/^\//, '');
  return `${base}${path}`;
}

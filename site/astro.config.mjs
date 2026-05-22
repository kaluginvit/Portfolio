// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

/** GitHub Project Pages: site is served from /Portfolio/ */
export default defineConfig({
  site: 'https://kaluginvit.github.io',
  base: '/Portfolio/',
  trailingSlash: 'ignore',
  integrations: [sitemap()],
});

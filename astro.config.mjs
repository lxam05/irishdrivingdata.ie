// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://www.irishdrivingdata.ie',
  output: 'static',
  trailingSlash: 'always',
  build: {
    format: 'directory',
  },
  redirects: {
    '/explorer/': '/charts/',
  },
  integrations: [sitemap()],
});

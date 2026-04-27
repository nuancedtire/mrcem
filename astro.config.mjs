import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import pagefind from 'astro-pagefind';

import cloudflare from '@astrojs/cloudflare';

export default defineConfig({
  integrations: [pagefind()],

  vite: {
    plugins: [tailwindcss()],
    server: {
      allowedHosts: ['ocode.exe.xyz'],
    },
  },

  build: {
    format: 'directory',
  },

  adapter: cloudflare(),
});
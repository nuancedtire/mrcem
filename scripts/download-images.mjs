/**
 * Downloads all CDN images referenced in the notes into public/images/
 * Run once: node scripts/download-images.mjs
 * Resumable: skips already-downloaded files.
 */

import { readFileSync, existsSync, mkdirSync, createWriteStream } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import https from 'https';
import http from 'http';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');
const CDN_HOST = 'd20g8jnrcgqmxh.cloudfront.net';
const OUT_DIR = join(ROOT, 'public', 'images');

console.log('Reading notes…');
const notes = JSON.parse(readFileSync(join(ROOT, 'data', '_all_notes.json'), 'utf8'));

const urlSet = new Set();
for (const note of notes) {
  for (const [, path] of note.body_html.matchAll(
    /https?:\/\/d20g8jnrcgqmxh\.cloudfront\.net([^\s"'<>]+)/g,
  )) {
    urlSet.add(`https://${CDN_HOST}${path}`);
  }
}

const urls = [...urlSet];
console.log(`Found ${urls.length} unique image URLs`);

function download(url) {
  const parsed = new URL(url);
  const outPath = join(OUT_DIR, parsed.pathname);
  const outDir = dirname(outPath);

  if (existsSync(outPath)) return Promise.resolve({ url, status: 'skip' });

  mkdirSync(outDir, { recursive: true });

  return new Promise(resolve => {
    const file = createWriteStream(outPath);
    const lib = url.startsWith('https') ? https : http;
    const req = lib.get(url, res => {
      if (res.statusCode === 301 || res.statusCode === 302) {
        file.close();
        return resolve(download(res.headers.location));
      }
      if (res.statusCode !== 200) {
        file.close();
        return resolve({ url, status: `http-${res.statusCode}` });
      }
      res.pipe(file);
      file.on('finish', () => { file.close(); resolve({ url, status: 'ok' }); });
    });
    req.on('error', err => { file.close(); resolve({ url, status: 'err', msg: err.message }); });
    req.setTimeout(15000, () => { req.destroy(); resolve({ url, status: 'timeout' }); });
  });
}

const CONCURRENCY = 12;
let done = 0, skipped = 0, errors = 0;

for (let i = 0; i < urls.length; i += CONCURRENCY) {
  const batch = urls.slice(i, i + CONCURRENCY);
  const results = await Promise.all(batch.map(download));
  done += batch.length;
  for (const r of results) {
    if (r.status === 'skip') skipped++;
    else if (r.status !== 'ok') { errors++; console.error(`  ✗ ${r.status} ${r.url}`); }
  }
  const pct = Math.round((done / urls.length) * 100);
  process.stdout.write(`\r  ${done}/${urls.length} (${pct}%)  skipped: ${skipped}  errors: ${errors}  `);
}

console.log(`\n\nDone! Downloaded ${done - skipped - errors}, skipped ${skipped}, errors ${errors}`);
console.log(`Images saved to: ${OUT_DIR}`);

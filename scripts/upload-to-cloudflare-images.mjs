/**
 * Upload all local images from public/images/ to Cloudflare Images.
 *
 * Usage:
 *   CF_ACCOUNT_ID=your_account_id \
 *   CF_API_TOKEN=your_api_token \
 *   node scripts/upload-to-cloudflare-images.mjs
 *
 * Images are uploaded with custom IDs so delivery URLs are predictable:
 *   https://imagedelivery.net/gceaQ8-ViunV02vSblnRWQ/mrcem-notes/{path}/public
 *
 * Metadata attached:
 *   { source, original_url, filename, path }
 *
 * The script is resumable — it lists existing images and skips already-uploaded ones.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const ACCOUNT_ID = process.env.CF_ACCOUNT_ID;
const API_TOKEN = process.env.CF_API_TOKEN;
const IMAGES_DIR = path.join(__dirname, '..', 'public', 'images');
const CUSTOM_ID_PREFIX = 'mrcem-notes';
const CDN_ORIGIN = 'https://d20g8jnrcgqmxh.cloudfront.net';

const BASE_API = (accountId) => `https://api.cloudflare.com/client/v4/accounts/${accountId}/images/v1`;

if (!ACCOUNT_ID || !API_TOKEN) {
  console.error('Error: CF_ACCOUNT_ID and CF_API_TOKEN must be set.');
  process.exit(1);
}

/* ------------------------------------------------------------------ */
/*  Helpers                                                           */
/* ------------------------------------------------------------------ */

function getMimeType(filename) {
  const ext = path.extname(filename).toLowerCase();
  const map = {
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
    '.svg': 'image/svg+xml',
    '.bmp': 'image/bmp',
    '.ico': 'image/x-icon',
  };
  return map[ext] || 'application/octet-stream';
}

async function cfFetch(url, options = {}) {
  const res = await fetch(url, {
    ...options,
    headers: {
      Authorization: `Bearer ${API_TOKEN}`,
      ...options.headers,
    },
  });

  if (res.status === 429) {
    const retryAfter = parseInt(res.headers.get('Retry-After') || '5', 10);
    console.warn(`  Rate limited. Retrying after ${retryAfter}s…`);
    await sleep(retryAfter * 1000);
    return cfFetch(url, options);
  }

  return res;
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function listAllImages() {
  const existing = new Set();
  let page = 1;
  let perPage = 100;

  while (true) {
    const url = `${BASE_API(ACCOUNT_ID)}?page=${page}&per_page=${perPage}`;
    const res = await cfFetch(url);
    const json = await res.json();

    if (!json.success) {
      console.error('Failed to list images:', json.errors);
      break;
    }

    const images = json.result.images || [];
    if (images.length === 0) break;

    for (const img of images) {
      existing.add(img.id);
    }

    if (images.length < perPage) break;
    page++;
  }

  return existing;
}

async function uploadImage(filePath, customId, metadata) {
  const fileBuffer = fs.readFileSync(filePath);
  const mimeType = getMimeType(filePath);
  const blob = new Blob([fileBuffer], { type: mimeType });

  const form = new FormData();
  form.append('file', blob, path.basename(filePath));
  form.append('id', customId);
  form.append('metadata', JSON.stringify(metadata));

  const res = await cfFetch(`${BASE_API(ACCOUNT_ID)}`, {
    method: 'POST',
    body: form,
  });

  const json = await res.json();
  return json;
}

function getAllImageFiles(dir, base = dir, files = []) {
  const entries = fs.readdirSync(dir);
  for (const entry of entries) {
    const fullPath = path.join(dir, entry);
    const stat = fs.statSync(fullPath);
    if (stat.isDirectory()) {
      getAllImageFiles(fullPath, base, files);
    } else {
      const relPath = path.relative(base, fullPath).replace(/\\/g, '/');
      files.push({ fullPath, relPath });
    }
  }
  return files;
}

/* ------------------------------------------------------------------ */
/*  Main                                                              */
/* ------------------------------------------------------------------ */

async function main() {
  console.log('Scanning local images…');
  const localImages = getAllImageFiles(IMAGES_DIR);
  console.log(`Found ${localImages.length} local images.`);

  console.log('Fetching existing Cloudflare Images…');
  const existingIds = await listAllImages();
  console.log(`Found ${existingIds.size} images already in Cloudflare Images.`);

  let uploaded = 0;
  let skipped = 0;
  let failed = 0;
  const failures = [];

  for (let i = 0; i < localImages.length; i++) {
    const { fullPath, relPath } = localImages[i];
    const customId = `${CUSTOM_ID_PREFIX}/${relPath}`;
    const filename = path.basename(relPath);

    const prefix = `[${i + 1}/${localImages.length}]`;

    if (existingIds.has(customId)) {
      console.log(`${prefix} SKIP (already exists) ${customId}`);
      skipped++;
      continue;
    }

    console.log(`${prefix} UPLOAD ${customId}`);

    const metadata = {
      source: 'mrcem-notes',
      original_url: `${CDN_ORIGIN}/${relPath}`,
      filename,
      path: relPath,
    };

    const uploadRes = await uploadImage(fullPath, customId, metadata);
    if (!uploadRes.success) {
      console.error(`  Upload failed:`, uploadRes.errors);
      failed++;
      failures.push({ customId, error: uploadRes.errors });
      continue;
    }

    uploaded++;
    await sleep(250); // ~4 req/s to stay well under rate limits
  }

  console.log('\n========================================');
  console.log('Done!');
  console.log(`  Uploaded : ${uploaded}`);
  console.log(`  Skipped  : ${skipped}`);
  console.log(`  Failed   : ${failed}`);
  console.log('========================================');

  if (failures.length > 0) {
    console.log('\nFailures:');
    for (const f of failures) {
      console.log(`  - ${f.customId}: ${JSON.stringify(f.error)}`);
    }
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});

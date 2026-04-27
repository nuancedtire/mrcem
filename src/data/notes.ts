const modules = import.meta.glob('../../data/**/*.json', { eager: true });
const rawNotes = Object.values(modules)
  .map((m: any) => m.default)
  .filter((n: any) => n && n.nid) as RawNote[];

interface RawNote {
  nid: string;
  title: string;
  body_html: string;
  category: string;
  sort_order?: number;
  related_nids?: string[];
}

export interface TocHeading {
  text: string;
  level: number;
  id: string;
}

export interface Note {
  nid: string;
  title: string;
  bodyHtml: string;
  headings: TocHeading[];
  categoryNum: number;
  categoryName: string;
  categorySlug: string;
  subcategoryNum: number;
  subcategoryName: string;
  subcategorySlug: string;
  sortOrder: number;
  relatedNids: string[];
}

export interface Subcategory {
  num: number;
  name: string;
  slug: string;
  count: number;
}

export interface Category {
  num: number;
  name: string;
  slug: string;
  count: number;
  subcategories: Subcategory[];
}

export interface CategoryMeta {
  icon: string;
  tint: string;
  tintDark: string;
}

export const CATEGORY_META: Record<string, CategoryMeta> = {
  'anatomy': {
    icon: '<path d="M17 10c.7-.7 1.69 0 2.5 0a2.5 2.5 0 1 0 0-5 .5.5 0 0 1-.5-.5 2.5 2.5 0 1 0-5 0c0 .81.7 1.8 0 2.5l-7 7c-.7.7-1.69 0-2.5 0a2.5 2.5 0 0 0 0 5c.28 0 .5.22.5.5a2.5 2.5 0 1 0 5 0c0-.81-.7-1.8 0-2.5Z"/>',
    tint: '#FDF2F4',
    tintDark: '#1A060A',
  },
  'physiology': {
    icon: '<path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"/>',
    tint: '#EFF6FF',
    tintDark: '#080E1C',
  },
  'pharmacology': {
    icon: '<path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"/><path d="m8.5 8.5 7 7"/>',
    tint: '#ECFDF5',
    tintDark: '#06140E',
  },
  'microbiology': {
    icon: '<path d="M12 20v-9"/><path d="M14 7a4 4 0 0 1 4 4v3a6 6 0 0 1-12 0v-3a4 4 0 0 1 4-4z"/><path d="M14.12 3.88 16 2"/><path d="M21 21a4 4 0 0 0-3.81-4"/><path d="M21 5a4 4 0 0 1-3.55 3.97"/><path d="M22 13h-4"/><path d="M3 21a4 4 0 0 1 3.81-4"/><path d="M3 5a4 4 0 0 0 3.55 3.97"/><path d="M6 13H2"/><path d="m8 2 1.88 1.88"/>',
    tint: '#FFFBEB',
    tintDark: '#141008',
  },
  'pathology': {
    icon: '<path d="M11 2v2"/><path d="M5 2v2"/><path d="M5 3H4a2 2 0 0 0-2 2v4a6 6 0 0 0 12 0V5a2 2 0 0 0-2-2h-1"/><path d="M8 15a6 6 0 0 0 12 0v-3"/><circle cx="20" cy="10" r="2"/>',
    tint: '#F5F3FF',
    tintDark: '#0C061A',
  },
  'evidenced-based-medicine': {
    icon: '<path d="M3 3v16a2 2 0 0 0 2 2h16"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/>',
    tint: '#F1F5F9',
    tintDark: '#070B14',
  },
  'embryology': {
    icon: '<path d="M10 16c.5.3 1.2.5 2 .5s1.5-.2 2-.5"/><path d="M15 12h.01"/><path d="M19.38 6.813A9 9 0 0 1 20.8 10.2a2 2 0 0 1 0 3.6 9 9 0 0 1-17.6 0 2 2 0 0 1 0-3.6A9 9 0 0 1 12 3c2 0 3.5 1.1 3.5 2.5s-.9 2.5-2 2.5c-.8 0-1.5-.4-1.5-1"/><path d="M9 12h.01"/>',
    tint: '#FDF2F8',
    tintDark: '#1A0610',
  },
};

const DEFAULT_META: CategoryMeta = {
  icon: '<circle cx="12" cy="12" r="10"/>',
  tint: '#F1F5F9',
  tintDark: '#070B14',
};

const CDN_ORIGIN = 'https://d20g8jnrcgqmxh.cloudfront.net';
const CDN_URL_RE = new RegExp(
  CDN_ORIGIN.replace(/\./g, '\\.') + '(/[^"\'\\s>]*)',
  'g'
);
const CF_IMAGES_BASE = 'https://imagedelivery.net/gceaQ8-ViunV02vSblnRWQ/mrcem-notes';
const META_DIV_RE = /<div id="(?:categorynum|categoryname|subcategorynum|subcategoryname)">[^<]*<\/div>/g;

const CLUTTER_PATTERNS = [
  // Rate button tables (entire table with like/dislike buttons)
  /<table\s+style\s*=\s*['"]\s*width\s*:\s*100%[\s\S]*?<\/table>/gi,
  // Magnifying glass links
  /<a[^>]*magglass[^>]*>[\s\S]*?<\/a>/gi,
  // Wikipedia source attribution spans + link
  /<span\s+style\s*=\s*['"][^'"]*font-size\s*:\s*11px[^'"]*['"][^>]*>[\s\S]*?<\/span>\s*<a\s+href\s*=\s*['"]http:\/\/en\.wikipedia[^>]*>[\s\S]*?<\/a>/gi,
  // Alternative Wikipedia attribution (just the span)
  /<span\s+style\s*=\s*['"][^'"]*font-size\s*:\s*11px[^'"]*['"][^>]*>Image sourced from\s*<\/span>/gi,
  // Media links (YouTube embeds etc.) — replaced with iframe below, not stripped
  // /<a[^>]*media_link[^>]*>[\s\S]*?<\/a>/gi,
  // Inline rate buttons with SVG icons
  /<button[^>]*rate-link[^>]*>[\s\S]*?<\/button>/gi,
  // Rate count spans
  /<span[^>]*link_good_count[^>]*>[\s\S]*?<\/span>/gi,
  /<span[^>]*link_bad_count[^>]*>[\s\S]*?<\/span>/gi,
  // Generic btn-sm in table (often rating buttons)
  /<button[^>]*btn-sm[^>]*>[\s\S]*?<\/button>/gi,
  // Media rating buttons (thumbs up/down)
  /<button[^>]*rate-media[^>]*>[\s\S]*?<\/button>/gi,
  // Media good/bad count spans
  /<span[^>]*media_good_count[^>]*>[\s\S]*?<\/span>/gi,
  /<span[^>]*media_bad_count[^>]*>[\s\S]*?<\/span>/gi,
  // Leftover media_link text anchors (not the thumbnail ones)
  /<a[^>]*media_link[^>]*>[\s\S]*?<\/a>/gi,
];

const MALFORMED_PATTERNS: [RegExp, string][] = [
  // Fix: <td></li></ul>Content</td> -> <td>Content</td>
  [/<td>\s*<\/li>\s*<\/ul>/gi, '<td>'],
  // Fix: <td></ul>Content</td> -> <td>Content</td>
  [/<td>\s*<\/ul>/gi, '<td>'],
];

function slugify(s: string): string {
  return s.toLowerCase().replace(/&/g, 'and').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

function headingId(text: string, used: Set<string>): string {
  let id = slugify(text);
  if (!id) id = 'section';
  let unique = id;
  let counter = 1;
  while (used.has(unique)) {
    unique = `${id}-${counter++}`;
  }
  used.add(unique);
  return unique;
}

function extractHeadings(html: string): { headings: TocHeading[]; html: string } {
  const headings: TocHeading[] = [];
  const usedIds = new Set<string>();

  // 1. Extract semantic <h1>–<h4>
  html = html.replace(/<(h[1-4])(?:\s+[^>]*)?>(.*?)<\/\1>/gi, (_full: string, tag: string, text: string) => {
    const level = parseInt(tag[1]);
    const cleanText = text.replace(/<[^>]+>/g, '').trim();
    if (!cleanText) return _full;
    const id = headingId(cleanText, usedIds);
    headings.push({ text: cleanText, level, id });
    return `<${tag} id="${id}">${text}</${tag}>`;
  });

  // 2. Extract <b> tags that look like headings:
  //    – followed by <br within 12 chars
  //    – text only (no nested tags), ≤40 chars
  //    – NOT inside <td>, <li>, <th>
  html = html.replace(/<b\b[^>]*>([^<]{1,40})<\/b>(\s*<br\s*\/?>)/gi, (_full: string, text: string, br: string) => {
    const cleanText = text.trim();
    if (!cleanText) return _full;
    // Skip if it looks like it might be inside a table cell or list item
    // (heuristic: check preceding context for <td or <li)
    const idx = html.indexOf(_full);
    const preceding = html.substring(Math.max(0, idx - 200), idx);
    if (/<td\b|<li\b|<th\b/i.test(preceding)) {
      // Additional check: if the <b> is the only content in the td/li, allow it
      const sinceLastTag = preceding.match(/<[^>]+>[^<]*$/);
      if (sinceLastTag && !sinceLastTag[0].startsWith('<td') && !sinceLastTag[0].startsWith('<li') && !sinceLastTag[0].startsWith('<th')) {
        return _full;
      }
    }
    const id = headingId(cleanText, usedIds);
    headings.push({ text: cleanText, level: 2, id });
    return `<h2 id="${id}">${cleanText}</h2>`;
  });

  headings.sort((a, b) => {
    const idxA = html.indexOf(`id="${a.id}"`);
    const idxB = html.indexOf(`id="${b.id}"`);
    return idxA - idxB;
  });

  return { headings, html };
}

export function getCategoryMeta(slug: string): CategoryMeta {
  return CATEGORY_META[slug] ?? DEFAULT_META;
}

function extractMeta(html: string) {
  const get = (id: string) =>
    html.match(new RegExp(`<div id="${id}">(.*?)<\\/div>`))?.[1]?.trim() ?? '';
  return {
    categoryNum: parseInt(get('categorynum')) || 0,
    categoryName: get('categoryname'),
    subcategoryNum: parseInt(get('subcategorynum')) || 0,
    subcategoryName: get('subcategoryname'),
  };
}

function extractRawContent(html: string): string {
  // Take everything before <div id="mybody"> — this contains the full note
  // content without the malformed mybody/body_content wrapper divs
  const marker = '<div id="mybody">';
  const idx = html.indexOf(marker);
  if (idx === -1) return html;
  return html.substring(0, idx);
}

function fixTableCells(html: string): string {
  // Fix unclosed <ul> and <li> tags inside <td> elements.
  // Source data has patterns like <td><ul><li>Content</td> with missing </li></ul>
  return html.replace(/<(td[^>]*)>([\s\S]*?)<\/td>/gi, (_full: string, tdAttrs: string, inner: string) => {
    let fixed = inner;
    // Count open <li> without matching </li>
    const liOpens = (fixed.match(/<li[^>]*>/gi) || []).length;
    const liCloses = (fixed.match(/<\/li>/gi) || []).length;
    for (let i = liCloses; i < liOpens; i++) {
      fixed += '</li>';
    }
    // Count open <ul> without matching </ul>
    const ulOpens = (fixed.match(/<ul[^>]*>/gi) || []).length;
    const ulCloses = (fixed.match(/<\/ul>/gi) || []).length;
    for (let i = ulCloses; i < ulOpens; i++) {
      fixed += '</ul>';
    }
    return `<${tdAttrs}>${fixed}</td>`;
  });
}

function makeVideoEmbed(url: string): string {
  const videoId = url.match(/(?:embed\/|v=|\/v\/)([a-zA-Z0-9_-]{11})/)?.[1];
  if (!videoId) return '';
  return `<div class="video-wrapper"><iframe src="https://www.youtube.com/embed/${videoId}" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen loading="lazy"></iframe></div>`;
}

function embedYouTubeVideos(html: string): string {
  // Convert media_link anchors that contain an <img> (the actual video thumbnails)
  const mediaLinkRe = /<a[^>]*class\s*=\s*['"][^'"]*media_link[^'"]*['"][^>]*data-url\s*=\s*['"]([^'"]+)['"][^>]*>\s*<img[\s\S]*?<\/a>/gi;
  html = html.replace(mediaLinkRe, (_full: string, url: string) => makeVideoEmbed(url));

  // Also handle the pattern where data-url comes before class
  const mediaLinkRe2 = /<a[^>]*data-url\s*=\s*['"]([^'"]+)['"][^>]*class\s*=\s*['"][^'"]*media_link[^'"]*['"][^>]*>\s*<img[\s\S]*?<\/a>/gi;
  html = html.replace(mediaLinkRe2, (_full: string, url: string) => makeVideoEmbed(url));

  // Wrap existing bare iframes in responsive container (strip width/height attributes)
  html = html.replace(
    /<iframe\s+[^>]*src\s*=\s*['"]([^'"]*)['"][^>]*>\s*<\/iframe>/gi,
    (_full: string, src: string) => {
      if (src.includes('youtube.com') || src.includes('youtu.be')) {
        return `<div class="video-wrapper"><iframe src="${src}" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen loading="lazy"></iframe></div>`;
      }
      return _full;
    }
  );

  // Collapse accidentally nested video-wrapper divs
  html = html.replace(/<div class="video-wrapper">\s*<div class="video-wrapper">/gi, '<div class="video-wrapper">');
  html = html.replace(/<\/iframe><\/div>\s*<\/div>/gi, '</iframe></div>');

  return html;
}

function processHtml(html: string): string {
  let result = extractRawContent(html);

  // Strip meta divs (categorynum, categoryname, subcategorynum, subcategoryname)
  result = result.replace(META_DIV_RE, '');

  // Convert YouTube media links to embeds FIRST (before clutter removal strips them)
  result = embedYouTubeVideos(result);

  // Remove clutter
  for (const re of CLUTTER_PATTERNS) {
    result = result.replace(re, '');
  }

  // Fix malformed HTML
  for (const [re, replacement] of MALFORMED_PATTERNS) {
    result = result.replace(re, replacement);
  }

  // Fix unclosed <ul>/<li> tags inside <td> cells
  result = fixTableCells(result);

  // Clean up trailing <BR>/<br> noise
  result = result.replace(/(?:<br\s*\/?>\s*|<BR\s*\/?>\s*)+$/gi, '');

  // Remove leftover empty tables (gutted by clutter removal)
  result = result.replace(/<table[^>]*>\s*<\/table>/gi, '');
  result = result.replace(/<td\s+style\s*=\s*['"][^'"]*float\s*:\s*right[^'"]*['"][^>]*>\s*<\/td>/gi, '');

  // Clean up video tables: keep only the row with the video wrapper, strip empty cells/rows
  result = result.replace(
    /(<div id="mybodymedia">)<table[^>]*>[\s\S]*?(<div class="video-wrapper">[\s\S]*?<\/div>)[\s\S]*?<\/table>/gi,
    '$1$2'
  );

  // Balance stray closing divs that would break Astro's DOM parsing.
  // Find indices of all unmatched </div> tags and remove only those.
  let depth = 0;
  const unmatched: number[] = [];
  let pos = 0;
  while (pos < result.length) {
    const openIdx = result.indexOf('<div', pos);
    const closeIdx = result.indexOf('</div>', pos);
    if (closeIdx === -1) break;
    if (openIdx !== -1 && openIdx < closeIdx) {
      depth++;
      pos = openIdx + 4;
    } else {
      if (depth > 0) {
        depth--;
      } else {
        unmatched.push(closeIdx);
      }
      pos = closeIdx + 6;
    }
  }
  // Remove unmatched closes in reverse order so indices stay valid
  for (let i = unmatched.length - 1; i >= 0; i--) {
    const idx = unmatched[i];
    result = result.slice(0, idx) + result.slice(idx + 6);
  }

  // Replace CDN URLs with Cloudflare Images delivery URLs
  result = result.replace(CDN_URL_RE, `${CF_IMAGES_BASE}$1/public`);

  return result.trim();
}

function stripSubcategoryPrefix(title: string, subcategoryName: string): string {
  if (!subcategoryName) return title;
  // Normalize HTML entities in subcategoryName for comparison
  const norm = subcategoryName.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
  if (title.toLowerCase().startsWith(norm.toLowerCase())) {
    const rest = title.slice(norm.length).trimStart();
    if (rest.startsWith(':')) {
      const stripped = rest.slice(1).trimStart();
      if (stripped.length > 0) return stripped;
    }
  }
  return title;
}

// Display name overrides: [categoryNum][subcategoryNum] → display name.
// The URL slug is derived from the original name so existing URLs stay stable.
const SUBCATEGORY_NAME_OVERRIDE: Record<number, Record<number, string>> = {
  4: { 8423: 'Virology & Mycology' }, // Microbiology: Virology subcategory also contains fungi
};

// Process all notes once at module load time (build-time)
const _notes: Note[] = (rawNotes as RawNote[]).map(raw => {
  const meta = extractMeta(raw.body_html);
  let bodyHtml = processHtml(raw.body_html);
  const { headings, html } = extractHeadings(bodyHtml);
  const title = stripSubcategoryPrefix(raw.title, meta.subcategoryName);
  const subcategorySlug = meta.subcategoryNum > 0 ? slugify(meta.subcategoryName) : '';
  const nameOverride = SUBCATEGORY_NAME_OVERRIDE[meta.categoryNum]?.[meta.subcategoryNum];
  const subcategoryName = nameOverride ?? meta.subcategoryName;
  return {
    nid: raw.nid,
    title,
    bodyHtml: html,
    headings,
    categoryNum: meta.categoryNum,
    categoryName: meta.categoryName,
    categorySlug: slugify(meta.categoryName),
    subcategoryNum: meta.subcategoryNum,
    subcategoryName,
    subcategorySlug,
    sortOrder: raw.sort_order || 0,
    relatedNids: raw.related_nids || [],
  };
});

// Sort notes by category, subcategory, then sortOrder
_notes.sort((a, b) => {
  if (a.categoryNum !== b.categoryNum) return a.categoryNum - b.categoryNum;
  if (a.subcategoryNum !== b.subcategoryNum) return a.subcategoryNum - b.subcategoryNum;
  return a.sortOrder - b.sortOrder;
});

export function getAllNotes(): Note[] {
  return _notes;
}

export function getNoteByNid(nid: string): Note | undefined {
  return _notes.find(n => n.nid === nid);
}

// Subcategory display order overrides for categories where legacy high subcategory
// numbers would otherwise produce a clinically illogical ordering.
// Map: categoryNum → { subcategoryNum → sort position (lower = first) }
const SUBCATEGORY_SORT_OVERRIDE: Record<number, Record<number, number>> = {
  3: { 9326: 1, 300: 2, 100: 3, 4059: 4, 200: 5 },                    // Pharmacology: Cardiovascular → GI → Neuropsych → Antimicrobials → Endocrine
  4: { 7650: 1, 8423: 2, 300: 3, 200: 4, 100: 5 },                    // Microbiology: Bacteriology → Virology → Clinical → Immunology → Parasitology
  5: { 100: 1, 150: 2, 200: 3, 7185: 4, 500: 5, 300: 6, 400: 7 },    // Pathology: Cardiorespiratory → Renal → GI/Endocrine → Haematology → Infectious → Neurology → Rheumatology
  6: { 1: 1, 2: 2, 3: 3, 4: 4, 5: 5 },                               // EBM: Foundational → Distributions → Hypothesis Testing → Risk/Screening → Epidemiology
};

export function getCategories(): Category[] {
  const catMap = new Map<number, Category>();
  for (const note of _notes) {
    if (!catMap.has(note.categoryNum)) {
      catMap.set(note.categoryNum, {
        num: note.categoryNum,
        name: note.categoryName,
        slug: note.categorySlug,
        count: 0,
        subcategories: [],
      });
    }
    const cat = catMap.get(note.categoryNum)!;
    cat.count++;
    if (note.subcategoryNum > 0) {
      let sub = cat.subcategories.find(s => s.num === note.subcategoryNum);
      if (!sub) {
        sub = { num: note.subcategoryNum, name: note.subcategoryName, slug: note.subcategorySlug, count: 0 };
        cat.subcategories.push(sub);
      }
      sub.count++;
    }
  }
  return [...catMap.values()].sort((a, b) => a.num - b.num).map(cat => {
    const overrides = SUBCATEGORY_SORT_OVERRIDE[cat.num];
    return {
      ...cat,
      subcategories: cat.subcategories.sort((a, b) => {
        if (overrides) {
          const posA = overrides[a.num] ?? 999;
          const posB = overrides[b.num] ?? 999;
          return posA - posB;
        }
        return a.num - b.num;
      }),
    };
  });
}

export function getNotesByCategory(categorySlug: string, subcategorySlug?: string): Note[] {
  return _notes.filter(n => {
    if (n.categorySlug !== categorySlug) return false;
    if (subcategorySlug !== undefined && n.subcategorySlug !== subcategorySlug) return false;
    return true;
  });
}

export function getAdjacentNotes(nid: string): { prev: Note | null; next: Note | null } {
  const note = _notes.find(n => n.nid === nid);
  if (!note) return { prev: null, next: null };
  const siblings = note.subcategorySlug
    ? getNotesByCategory(note.categorySlug, note.subcategorySlug)
    : getNotesByCategory(note.categorySlug).filter(n => n.subcategorySlug === '');
  const idx = siblings.findIndex(n => n.nid === nid);
  return {
    prev: idx > 0 ? siblings[idx - 1] : null,
    next: idx < siblings.length - 1 ? siblings[idx + 1] : null,
  };
}

export function getRelatedNotes(nid: string): Note[] {
  const note = _notes.find(n => n.nid === nid);
  if (!note || note.relatedNids.length === 0) return [];
  return note.relatedNids
    .map(id => _notes.find(n => n.nid === id))
    .filter((n): n is Note => n !== undefined);
}

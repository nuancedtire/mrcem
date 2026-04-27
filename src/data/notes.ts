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
    icon: '<path d="M12 2a5 5 0 0 1 5 5c0 1.5-.7 2.8-1.8 3.7a8 8 0 0 1 4.8 7.3 2 2 0 0 1-4 0 4 4 0 0 0-8 0 2 2 0 0 1-4 0 8 8 0 0 1 4.8-7.3A4.9 4.9 0 0 1 7 7a5 5 0 0 1 5-5z"/>',
    tint: '#FDF2F4',
    tintDark: '#1A060A',
  },
  'physiology': {
    icon: '<path d="M20.8 10.2a6.5 6.5 0 0 1-2 5.8c-.8.7-1.7 1.2-2.7 1.5a2 2 0 0 0-1.6 1.9v.1a2 2 0 0 1-4 0v-.1a2 2 0 0 0-1.6-1.9 6.5 6.5 0 0 1-4.7-7.3c.2-1.5.9-2.8 1.9-3.9.7-.7 1.6-1.2 2.6-1.5A2 2 0 0 0 10 4a2 2 0 0 1 4 0 2 2 0 0 0 1.8 1.7c1 .3 1.9.8 2.6 1.5a6.5 6.5 0 0 1 2.4 3z"/><path d="M12 11v3"/>',
    tint: '#EFF6FF',
    tintDark: '#080E1C',
  },
  'pharmacology': {
    icon: '<path d="M10.5 20.5l10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"/><path d="M8.5 8.5l7 7"/>',
    tint: '#ECFDF5',
    tintDark: '#06140E',
  },
  'microbiology': {
    icon: '<path d="M12 12c0-3 0-3-3-3s-3 0-3 3 0 3 3 3 3 0 3-3z"/><path d="M9 12H4"/><path d="M15 12h5"/><circle cx="12" cy="12" r="10"/>',
    tint: '#FFFBEB',
    tintDark: '#141008',
  },
  'pathology': {
    icon: '<path d="M6 21l12-12"/><path d="M10 10l-2-2"/><path d="M18 18l-2-2"/><circle cx="12" cy="12" r="10"/>',
    tint: '#F5F3FF',
    tintDark: '#0C061A',
  },
  'evidenced-based-medicine': {
    icon: '<path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/>',
    tint: '#F1F5F9',
    tintDark: '#070B14',
  },
  'embryology': {
    icon: '<path d="M12 2a5 5 0 0 1 5 5c0 1.5-.7 2.8-1.8 3.7a8 8 0 0 1 4.8 7.3 2 2 0 0 1-4 0 4 4 0 0 0-8 0 2 2 0 0 1-4 0 8 8 0 0 1 4.8-7.3A4.9 4.9 0 0 1 7 7a5 5 0 0 1 5-5z"/>',
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

// Process all notes once at module load time (build-time)
const _notes: Note[] = (rawNotes as RawNote[]).map(raw => {
  const meta = extractMeta(raw.body_html);
  let bodyHtml = processHtml(raw.body_html);
  const { headings, html } = extractHeadings(bodyHtml);
  return {
    nid: raw.nid,
    title: raw.title,
    bodyHtml: html,
    headings,
    categoryNum: meta.categoryNum,
    categoryName: meta.categoryName,
    categorySlug: slugify(meta.categoryName),
    subcategoryNum: meta.subcategoryNum,
    subcategoryName: meta.subcategoryName,
    subcategorySlug: meta.subcategoryNum > 0 ? slugify(meta.subcategoryName) : '',
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
  return [...catMap.values()].sort((a, b) => a.num - b.num).map(cat => ({
    ...cat,
    subcategories: cat.subcategories.sort((a, b) => a.num - b.num),
  }));
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

import rawNotes from '../../data/_all_notes.json';

interface RawNote {
  nid: string;
  title: string;
  body_html: string;
  category: string;
}

export interface Note {
  nid: string;
  title: string;
  bodyHtml: string;
  categoryNum: number;
  categoryName: string;
  categorySlug: string;
  subcategoryNum: number;
  subcategoryName: string;
  subcategorySlug: string;
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

const CDN_ORIGIN = 'https://d20g8jnrcgqmxh.cloudfront.net';
const CDN_RE = new RegExp(CDN_ORIGIN.replace(/\./g, '\\.'), 'g');
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
  // Media links (YouTube embeds etc.)
  /<a[^>]*media_link[^>]*>[\s\S]*?<\/a>/gi,
  // Inline rate buttons with SVG icons
  /<button[^>]*rate-link[^>]*>[\s\S]*?<\/button>/gi,
  // Rate count spans
  /<span[^>]*link_good_count[^>]*>[\s\S]*?<\/span>/gi,
  /<span[^>]*link_bad_count[^>]*>[\s\S]*?<\/span>/gi,
  // Generic btn-sm in table (often rating buttons)
  /<button[^>]*btn-sm[^>]*>[\s\S]*?<\/button>/gi,
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
  return html.replace(/<td[^>]*>([\s\S]*?)<\/td>/gi, (_full: string, inner: string) => {
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
    return `<td>${fixed}</td>`;
  });
}

function processHtml(html: string): string {
  let result = extractRawContent(html);

  // Strip meta divs (categorynum, categoryname, subcategorynum, subcategoryname)
  result = result.replace(META_DIV_RE, '');

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

  // Replace CDN URLs
  result = result.replace(CDN_RE, '/images');

  return result.trim();
}

// Process all notes once at module load time (build-time)
const _notes: Note[] = (rawNotes as RawNote[]).map(raw => {
  const meta = extractMeta(raw.body_html);
  return {
    nid: raw.nid,
    title: raw.title,
    bodyHtml: processHtml(raw.body_html),
    categoryNum: meta.categoryNum,
    categoryName: meta.categoryName,
    categorySlug: slugify(meta.categoryName),
    subcategoryNum: meta.subcategoryNum,
    subcategoryName: meta.subcategoryName,
    subcategorySlug: meta.subcategoryNum > 0 ? slugify(meta.subcategoryName) : '',
  };
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

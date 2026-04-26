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

function processHtml(html: string): string {
  return html
    .replace(META_DIV_RE, '')
    .replace(CDN_RE, '/images');
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

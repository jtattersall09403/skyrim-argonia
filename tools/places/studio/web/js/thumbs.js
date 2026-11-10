// Thumbnails for search results and the info panel: the server's own picture of each base's model
// (/api/asset/thumb, a small WebP it keeps), so the tablet neither downloads the model nor draws it for a picture.
// A base with no model gets a plain tile in its kind's colour.
import { API_BASE } from './api.js';
import { KIND_COLOUR } from './objects.js';

export function thumb(base) {
  if (!base) return '';
  if (base.model) return `${API_BASE}/asset/thumb?model=${encodeURIComponent(base.model)}`;
  const c = encodeURIComponent(KIND_COLOUR[base.kind] || '#999999');
  return `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 8 8'%3E%3Crect x='1.5' y='1.5' width='5' height='5' rx='1' fill='${c}'/%3E%3C/svg%3E`;
}

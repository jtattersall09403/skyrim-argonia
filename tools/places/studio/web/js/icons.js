// Line icons for the rail and panels (drawn here, 24px grid).
const p = (d) => `<svg viewBox="0 0 24 24" aria-hidden="true">${d}</svg>`;
export const ICON = {
  select: p('<path d="M5 3l14 8-6 2-2 6z"/>'),
  search: p('<circle cx="10.5" cy="10.5" r="6.5"/><path d="m20 20-4.8-4.8"/>'),
  people: p('<circle cx="9" cy="7" r="3.2"/><path d="M3 20c0-3.8 2.7-6 6-6s6 2.2 6 6"/><circle cx="17.5" cy="8.5" r="2.4"/><path d="M16 14.2c2.9.1 5 2 5 5.3"/>'),
  quests: p('<path d="M6 21V4"/><path d="M6 4h11l-2.5 4L17 12H6"/>'),
  paint: p('<path d="M18 3l3 3-9 9-3-3z"/><path d="M9 12c-3 0-5 2-5 5 0 2-1 3-2 4 4 0 9-1 9-6"/>'),
  land: p('<path d="M2 19l6-9 4 5 3-3 7 7z"/><path d="M14 6h6M17 3v6"/>'),
  plants: p('<path d="M12 21v-8"/><path d="M12 13c-4 0-6-3-6-7 4 0 6 3 6 7z"/><path d="M12 15c3 0 5-2 5-5-3 0-5 2-5 5z"/>'),
  walking: p('<path d="M8 21c-1.6 0-2.4-1.4-2.2-3.4.2-1.8 1.2-3 2.6-3s2 1.4 1.7 3.2C9.8 19.6 9.2 21 8 21z"/><path d="M16 13c-1.4 0-2.1-1.2-1.9-3 .2-1.6 1-2.6 2.3-2.6s1.8 1.2 1.5 2.8c-.3 1.5-.8 2.8-1.9 2.8z"/><path d="M6.5 12.5h3.2M14.8 5h3"/>'),
  paths: p('<path d="M5 21c2-6 10-5 10-10S9 6 11 3"/><path d="M10 21c2-5 9-4 9-10S14 6 16 3" opacity=".45"/>'),
  history: p('<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l3 2"/>'),
  notes: p('<path d="M4 4h16v12H9l-5 4z"/><path d="M8 9h8M8 12h5"/>'),
  saves: p('<path d="M5 3h11l3 3v15H5z"/><path d="M8 3v6h8V3M8 21v-7h8v7"/>'),
  needs: p('<path d="M4 5a2 2 0 0 1 2-2h12v16H6a2 2 0 0 0-2 2z"/><path d="M4 21V5M8 7h6M8 10h6"/>'),
  help: p('<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.7.3-1 1-1 1.7v.5M12 17.5v.01"/>'),
  move: p('<path d="M12 3v18M3 12h18M12 3l-3 3m3-3 3 3M12 21l-3-3m3 3 3-3M3 12l3-3m-3 3 3 3M21 12l-3-3m3 3-3 3"/>'),
  lift: p('<path d="M12 20V4m0 0-5 5m5-5 5 5"/>'),
  rotate: p('<path d="M20 12a8 8 0 1 1-2.3-5.7"/><path d="M20 4v5h-5"/>'),
  scale: p('<path d="M4 20 20 4M14 4h6v6M10 20H4v-6"/>'),
  theme: p('<path d="M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5z"/>'),
};

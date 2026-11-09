// Ids we mint for our own placed things: <place_id>.<ulid>, stable for life.
const B32 = '0123456789ABCDEFGHJKMNPQRSTVWXYZ';
let last = 0, seq = 0;
export function ulid() {
  let t = Date.now(); if (t === last) seq++; else { seq = 0; last = t; }
  let s = '';
  for (let i = 0; i < 10; i++) { s = B32[t % 32] + s; t = Math.floor(t / 32); }
  const rnd = crypto.getRandomValues(new Uint8Array(16));
  for (let i = 0; i < 16; i++) s += B32[(rnd[i] + (i === 15 ? seq : 0)) % 32];
  return s;
}
export const mintId = (placeId) => `${placeId}.${ulid()}`;

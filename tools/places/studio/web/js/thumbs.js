// Thumbnails for search results and the info panel, drawn here from each base's model and kept for the session.
import * as THREE from 'three';
import { loadModel, KIND_COLOUR } from './objects.js';

const SIZE = 160, cache = new Map();
let renderer, scene, camera;
function setup() {
  if (renderer) return;
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
  renderer.setSize(SIZE, SIZE, false); renderer.outputColorSpace = THREE.SRGBColorSpace;
  scene = new THREE.Scene();
  scene.add(new THREE.HemisphereLight('#ffffff', '#555544', 2.2));
  const d = new THREE.DirectionalLight('#ffffff', 1.2); d.position.set(1, -1.4, 2); scene.add(d);
  camera = new THREE.PerspectiveCamera(30, 1, 1, 100000); camera.up.set(0, 0, 1);
}
function shoot(objects, box) {
  setup(); scene.add(...objects);
  const c = box.getCenter(new THREE.Vector3()), r = box.getSize(new THREE.Vector3()).length() / 2 || 50;
  camera.position.set(c.x + r * 1.6, c.y - r * 2.2, c.z + r * 1.4); camera.near = r / 50; camera.far = r * 20;
  camera.lookAt(c); camera.updateProjectionMatrix();
  renderer.render(scene, camera); const url = renderer.domElement.toDataURL('image/png');
  scene.remove(...objects); return url;
}
// A box of the base's bounds straight away; the model's picture when it arrives.
export function thumb(base, onReady) {
  if (!base) return '';
  if (cache.has(base.key)) return cache.get(base.key);
  const b = base.bounds || [[-32, -32, 0], [32, 32, 64]];
  const box = new THREE.Box3(new THREE.Vector3(...b[0]), new THREE.Vector3(...b[1]));
  const m = new THREE.Mesh(new THREE.BoxGeometry(...box.getSize(new THREE.Vector3()).toArray()), new THREE.MeshLambertMaterial({ color: KIND_COLOUR[base.kind] || '#999' }));
  m.position.copy(box.getCenter(new THREE.Vector3()));
  const placeholder = shoot([m], box); m.geometry.dispose();
  cache.set(base.key, placeholder);
  if (base.model) loadModel(base.model, 0).then((parts) => {
    if (!parts?.length) return;
    const meshes = parts.map((p) => new THREE.Mesh(p.geometry, p.material)), bb = new THREE.Box3();
    for (const mm of meshes) { mm.geometry.computeBoundingBox(); bb.union(mm.geometry.boundingBox); }
    const url = shoot(meshes, bb); cache.set(base.key, url); onReady?.(url);
  });
  return placeholder;
}

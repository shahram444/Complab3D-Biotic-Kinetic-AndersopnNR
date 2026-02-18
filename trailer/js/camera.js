/* ============================================================
   ARKE: Guardians of Earth — Cinematic Trailer
   CAMERA: Pan, zoom, shake, letterbox for cinematic shots
   ============================================================ */

const Camera = (() => {
  let x = 0, y = 0;
  let zoom = 1;
  let targetX = 0, targetY = 0, targetZoom = 1;
  let shakeIntensity = 0, shakeDecay = 0;
  let shakeOffX = 0, shakeOffY = 0;
  let panSpeed = 2;       // lerp speed
  let zoomSpeed = 1.5;

  /* Easing functions */
  function easeInOut(t) { return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2; }
  function lerp(a, b, t) { return a + (b - a) * t; }

  /* Set camera position instantly */
  function set(px, py, z) {
    x = targetX = px;
    y = targetY = py;
    zoom = targetZoom = z || 1;
  }

  /* Smoothly move camera to target */
  function moveTo(px, py, z, speed) {
    targetX = px;
    targetY = py;
    if (z !== undefined) targetZoom = z;
    if (speed !== undefined) panSpeed = speed;
  }

  /* Camera shake */
  function shake(intensity, duration) {
    shakeIntensity = intensity;
    shakeDecay = intensity / (duration || 0.3);
  }

  /* Update camera state */
  function update(dt) {
    // Smooth follow
    const t = 1 - Math.pow(0.001, dt * panSpeed);
    x = lerp(x, targetX, t);
    y = lerp(y, targetY, t);
    zoom = lerp(zoom, targetZoom, 1 - Math.pow(0.001, dt * zoomSpeed));

    // Shake
    if (shakeIntensity > 0) {
      shakeOffX = (Math.random() - 0.5) * shakeIntensity * 2;
      shakeOffY = (Math.random() - 0.5) * shakeIntensity * 2;
      shakeIntensity = Math.max(0, shakeIntensity - shakeDecay * dt);
    } else {
      shakeOffX = 0;
      shakeOffY = 0;
    }
  }

  /* Apply camera transform to canvas context */
  function apply(ctx) {
    ctx.save();
    ctx.translate(CFG.W / 2, CFG.H / 2);
    ctx.scale(zoom, zoom);
    ctx.translate(-x + shakeOffX, -y + shakeOffY);
  }

  /* Restore context */
  function restore(ctx) {
    ctx.restore();
  }

  /* Slow cinematic pan */
  function cinematicPan(fromX, fromY, toX, toY, fromZ, toZ, duration, elapsed) {
    const t = Math.min(1, elapsed / duration);
    const e = easeInOut(t);
    x = targetX = lerp(fromX, toX, e);
    y = targetY = lerp(fromY, toY, e);
    zoom = targetZoom = lerp(fromZ, toZ, e);
  }

  /* Getters */
  function getX() { return x; }
  function getY() { return y; }
  function getZoom() { return zoom; }

  return { set, moveTo, shake, update, apply, restore, cinematicPan, getX, getY, getZoom, easeInOut, lerp };
})();

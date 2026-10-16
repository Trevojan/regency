// Layout triage helpers (layout/README.md, "Triage"). Paste into the console, or run through the browser tool.
// Read-only except outlineAll(), which toggles a debug outline. Nothing here depends on the design.

// 1. Draw every box. Call again to remove.
function outlineAll() {
  const id = "__outline_all";
  const old = document.getElementById(id);
  if (old) return old.remove(), "outlines off";
  const s = document.createElement("style");
  s.id = id;
  s.textContent = "*{outline:1px solid color-mix(in oklab, currentColor 35%, transparent)!important;outline-offset:-1px}";
  document.head.append(s);
  return "outlines on";
}

// 2. The element and every ancestor, with the properties that decide layout.
function chain(el) {
  const rows = [];
  for (let n = el; n && n.nodeType === 1; n = n.parentElement) {
    const c = getComputedStyle(n);
    const r = n.getBoundingClientRect();
    rows.push({
      el: n.tagName.toLowerCase() + (n.id ? "#" + n.id : "") + (n.classList.length ? "." + [...n.classList].slice(0, 4).join(".") : ""),
      display: c.display, position: c.position,
      overflow: c.overflowX + "/" + c.overflowY,
      minW: c.minWidth, minH: c.minHeight, w: Math.round(r.width), h: Math.round(r.height),
      makesContainingBlock: containingBlockReason(n) || "",
      z: c.zIndex,
    });
  }
  console.table(rows);
  return rows.length + " boxes";
}

// Why this box would capture absolute/fixed descendants (or null).
function containingBlockReason(n) {
  const c = getComputedStyle(n);
  const reasons = [];
  if (c.position !== "static") reasons.push("position:" + c.position);
  if (c.transform !== "none") reasons.push("transform");
  if (c.translate !== "none" && c.translate) reasons.push("translate");
  if (c.rotate !== "none" && c.rotate) reasons.push("rotate");
  if (c.scale !== "none" && c.scale) reasons.push("scale");
  if (c.filter !== "none") reasons.push("filter");
  if (c.backdropFilter && c.backdropFilter !== "none") reasons.push("backdrop-filter");
  if (c.perspective !== "none") reasons.push("perspective");
  if (/paint|layout|strict|content/.test(c.contain)) reasons.push("contain:" + c.contain);
  if (/transform|filter|perspective/.test(c.willChange)) reasons.push("will-change");
  if (c.containerType && c.containerType !== "normal") reasons.push("container-type");
  return reasons.join(", ") || null;
}

// The box an absolute (or fixed) element is positioned against.
function containingBlock(el) {
  const fixed = getComputedStyle(el).position === "fixed";
  for (let n = el.parentElement; n; n = n.parentElement) {
    const why = containingBlockReason(n);
    if (!why) continue;
    // a positioned ancestor captures absolute, but only transform-like reasons capture fixed
    if (fixed && /^position:/.test(why) && !why.includes(",")) continue;
    return { box: n, why };
  }
  return { box: fixed ? "viewport" : document.documentElement, why: "initial containing block" };
}

// Ancestors that create a stacking context: a z-index inside one cannot escape it.
function stackingContexts(el) {
  const out = [];
  for (let n = el.parentElement; n && n !== document.documentElement; n = n.parentElement) {
    const c = getComputedStyle(n);
    const p = n.parentElement && getComputedStyle(n.parentElement);
    const flexOrGridChild = p && /flex|grid/.test(p.display);
    const why = [];
    if (c.zIndex !== "auto" && (c.position !== "static" || flexOrGridChild)) why.push("z-index " + c.zIndex);
    if (c.position === "fixed" || c.position === "sticky") why.push(c.position);
    if (parseFloat(c.opacity) < 1) why.push("opacity");
    if (c.transform !== "none" || (c.translate && c.translate !== "none") || (c.scale && c.scale !== "none") || (c.rotate && c.rotate !== "none")) why.push("transform");
    if (c.filter !== "none" || (c.backdropFilter && c.backdropFilter !== "none")) why.push("filter");
    if (c.isolation === "isolate") why.push("isolation");
    if (c.mixBlendMode !== "normal") why.push("mix-blend");
    if (/paint|layout|strict|content/.test(c.contain)) why.push("contain");
    if (why.length) out.push({ el: n.tagName.toLowerCase() + "." + [...n.classList].slice(0, 3).join("."), why: why.join(", ") });
  }
  console.table(out);
  return out;
}

// Elements that stick out past the viewport's right edge (horizontal page scroll). Deepest first.
function overflowCulprits() {
  const vw = document.documentElement.clientWidth;
  // an element clipped by an ancestor that itself fits (overflow-x-auto table wrapper, overflow-hidden card)
  // does not widen the page: skip it
  // An overflow ancestor clips an absolute box only if it is the box's containing block or above it: an
  // `sr-only` label inside an `overflow-x-auto` table with no `relative` in between escapes the clip.
  const clippedInside = (e) => {
    let escaping = /absolute|fixed/.test(getComputedStyle(e).position);
    for (let n = e.parentElement; n && n !== document.body; n = n.parentElement) {
      const c = getComputedStyle(n);
      if (escaping && containingBlockReason(n)) escaping = false; // reached the containing block
      if (!escaping && c.overflowX !== "visible" && n.getBoundingClientRect().right <= vw + 1) return true;
      if (!escaping && /absolute|fixed/.test(c.position)) escaping = true; // nested absolute ancestor
    }
    return false;
  };
  const hits = [...document.body.querySelectorAll("*")].filter((e) => {
    const r = e.getBoundingClientRect();
    return r.width && r.right > vw + 1 && !clippedInside(e);
  });
  const leaves = hits.filter((e) => !hits.some((o) => o !== e && e.contains(o)));
  return { pageScrolls: document.documentElement.scrollWidth > vw, viewport: vw, culprits: leaves.map((e) => e.outerHTML.slice(0, 140)) };
}

// Sticky that never sticks: report the scroll container it actually sticks to.
function stickyScroller(el) {
  for (let n = el.parentElement; n; n = n.parentElement) {
    const c = getComputedStyle(n);
    if (/(auto|scroll|hidden|clip)/.test(c.overflowX + c.overflowY)) return { scroller: n, overflow: c.overflowX + "/" + c.overflowY };
  }
  return { scroller: "viewport" };
}

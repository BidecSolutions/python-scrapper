// Google Maps collector content script (MV3)

const STATE = {
  capturing: false,
  lastSentAt: 0,
  observer: null,
  scrapeTimer: null,
  interval: null,
  detailTimer: null,
  processingDetails: false,
  processedDetailKeys: new Set(),
};

function isMapsSearchResultsPage() {
  return location.hostname === "www.google.com" && location.pathname.startsWith("/maps");
}

function findFeedContainer() {
  // Google Maps results list is usually in a feed container.
  return document.querySelector('div[role="feed"]');
}

function normalizeText(text) {
  return (text || "")
    .replace(/\u00A0/g, " ")
    .replace(/\s+/g, " ")
    .replace(/\s*Â·\s*/g, " · ")
    .trim();
}

function safeNumber(text) {
  const cleaned = normalizeText(text).replace(/,/g, "");
  const match = cleaned.match(/(\d+(\.\d+)?)/);
  if (!match) return null;
  const value = Number(match[1]);
  return Number.isFinite(value) ? value : null;
}

function isSocialHost(hostname) {
  const h = (hostname || "").toLowerCase();
  return (
    h.endsWith("facebook.com") ||
    h.endsWith("instagram.com") ||
    h.endsWith("linkedin.com") ||
    h.endsWith("twitter.com") ||
    h === "x.com" ||
    h.endsWith("tiktok.com") ||
    h.endsWith("youtube.com") ||
    h.endsWith("wa.me") ||
    h.endsWith("whatsapp.com")
  );
}

function preferNonSocialUrl(candidateUrls) {
  const urls = (candidateUrls || []).filter(Boolean);
  if (urls.length === 0) return null;
  const nonSocial = urls.find((u) => {
    try {
      return !isSocialHost(new URL(u).hostname);
    } catch {
      return true;
    }
  });
  return nonSocial || urls[0] || null;
}

function extractCardDataFromAnchor(anchor) {
  try {
    const url = anchor.href;
    if (!url || !url.includes("/maps/place/")) return null;

    const place_key = extractPlaceKey(url);

    // Card root tends to be a few parents up from the anchor.
    const cardRoot = anchor.closest('[role="article"], div.Nv2PK, div[aria-label][jsaction], div') || anchor.parentElement;
    if (!cardRoot) return null;

    // Name: try aria-label first, then visible text
    const aria = anchor.getAttribute("aria-label");
    let name = normalizeText(aria);
    if (!name) {
      const nameEl =
        cardRoot.querySelector('[role="heading"]') ||
        cardRoot.querySelector("div.qBF1Pd") ||
        cardRoot.querySelector("span, div");
      name = normalizeText(nameEl?.textContent);
    }
    name = name.replace(/\s*·\s*Visited link\s*$/i, "").trim();

    // Rating: aria-label like "4.7 stars"
    const ratingEl =
      cardRoot.querySelector('span[aria-label*="stars"]') ||
      cardRoot.querySelector('span[aria-label*="Star"]');
    const rating = ratingEl ? safeNumber(ratingEl.getAttribute("aria-label")) : null;

    // Reviews: often "(1,234)" or "1,234"
    const reviewsEl =
      cardRoot.querySelector("span.UY7F9") ||
      Array.from(cardRoot.querySelectorAll("span")).find((s) => /\(\s*[\d,.]+\s*\)/.test(s.textContent || ""));
    const reviewsText = normalizeText(reviewsEl?.textContent).replace(/[()]/g, "");
    const reviews = reviewsText ? safeNumber(reviewsText) : null;

    // Category/address line: best-effort
    const metaLine = normalizeText(
      cardRoot.querySelector("div.W4Efsd")?.textContent ||
        Array.from(cardRoot.querySelectorAll("div, span")).map((n) => normalizeText(n.textContent)).find((t) => t && t.length < 80 && t.includes("·"))
    );

    // Some listings show phone / website directly in the left list card. Extract best-effort.
    const cardLines = normalizeText(cardRoot.innerText || "")
      .split("\n")
      .map((l) => normalizeText(l))
      .filter((l) => l && l.length >= 2)
      .slice(0, 30);
    const phoneFromCard = (() => {
      const line = cardLines.find(looksLikePhone);
      return line ? extractPhone(line) : null;
    })();
    const websiteFromCard = (() => {
      const hrefs = Array.from(cardRoot.querySelectorAll("a[href]"))
        .map((a) => a.getAttribute("href") || "")
        .map(toExternalWebsiteUrl)
        .filter(Boolean);
      const byHref = preferNonSocialUrl(hrefs);
      if (byHref) return byHref;

      const domainLine = cardLines.find((l) => {
        if (l.includes(" ")) return false;
        if (!/[a-zA-Z]/.test(l)) return false;
        if (!l.includes(".")) return false;
        if (l.includes("+")) return false;
        if (l.toLowerCase().includes("google.")) return false;
        if (l.length > 80) return false;
        return true;
      });
      if (!domainLine) return null;
      return `https://${domainLine.replace(/^https?:\/\//i, "")}`;
    })();

    return {
      name: name || null,
      detail_url: url,
      place_key,
      rating,
      reviews,
      meta_line: metaLine || null,
      collected_at: new Date().toISOString(),
      address: null,
      phone: phoneFromCard || null,
      website: websiteFromCard || null,
      emails: [],
    };
  } catch {
    return null;
  }
}

function extractPlaceKey(detailUrl) {
  try {
    const u = new URL(detailUrl);
    const cid = u.searchParams.get("cid");
    if (cid) return `cid:${cid}`;
    // Sometimes the URL contains a stable "1s0x...:0x..." token.
    const m = detailUrl.match(/!1s(0x[0-9a-fA-F]+:0x[0-9a-fA-F]+)/);
    if (m) return `s:${m[1]}`;
    // Fallback: stable-ish path without query string
    return `path:${u.pathname}`;
  } catch {
    return null;
  }
}

function isVisible(el) {
  if (!el) return false;
  const rect = el.getBoundingClientRect?.();
  if (!rect) return false;
  if (rect.width < 2 || rect.height < 2) return false;
  const style = window.getComputedStyle(el);
  if (style.visibility === "hidden" || style.display === "none") return false;
  return true;
}

function findVisiblePlaceTitle() {
  const scoped = document.querySelector("#pane") || document;
  const candidates = Array.from(scoped.querySelectorAll("h1")).filter((h) => {
    if (!isVisible(h)) return false;
    const t = normalizeText(h.textContent);
    return !!t && t.length >= 2;
  });
  candidates.sort((a, b) => b.getBoundingClientRect().height - a.getBoundingClientRect().height);
  return candidates[0] || null;
}

function findPlacePanelRoot() {
  // Try to target the right-side "place details" panel.
  // Google Maps markup varies a lot, so we use a few text/role anchors.
  const title = findVisiblePlaceTitle();
  if (title) {
    // Climb up to a container that looks like the details sheet (has tabs/buttons)
    let node = title;
    for (let i = 0; i < 12 && node; i++) {
      const parent = node.parentElement;
      if (!parent) break;
      if (parent.querySelector('[role="tablist"]') || parent.querySelector('button[aria-label*="Directions"]')) {
        return parent;
      }
      node = parent;
    }
    return title.closest("#pane") || title.closest('div[role="main"]') || title.parentElement || document.body;
  }

  const textAnchors = ["Suggest an edit", "Add a label", "Your Maps activity"];
  for (const text of textAnchors) {
    const el = Array.from(document.querySelectorAll("button, div, span")).find(
      (n) => normalizeText(n.textContent).includes(text)
    );
    if (el) {
      return (
        el.closest('div[role="region"]') ||
        el.closest("#pane") ||
        el.closest('div[role="main"]') ||
        document.body
      );
    }
  }

  return document.querySelector("#pane") || document.querySelector('div[role="main"]') || document.body;
}

function looksLikePhone(text) {
  const t = normalizeText(text);
  if (!t) return false;
  return /(\+?\d[\d\s().-]{6,}\d)/.test(t);
}

function extractPhone(text) {
  const t = normalizeText(text);
  const match = t.match(/(\+?\d[\d\s().-]{6,}\d)/);
  return match ? normalizeText(match[1]) : null;
}

function isExternalWebsite(url) {
  try {
    const u = new URL(url);
    if (!["http:", "https:"].includes(u.protocol)) return false;
    if (u.hostname.endsWith("google.com")) return false;
    return true;
  } catch {
    return false;
  }
}

function unwrapGoogleRedirect(url) {
  try {
    const u = new URL(url);
    if (!u.hostname.endsWith("google.com")) return null;
    if (u.pathname !== "/url") return null;
    const target = u.searchParams.get("url") || u.searchParams.get("q");
    if (!target) return null;
    const decoded = decodeURIComponent(target);
    return decoded || null;
  } catch {
    return null;
  }
}

function toExternalWebsiteUrl(rawHref) {
  if (!rawHref) return null;
  if (isExternalWebsite(rawHref)) return rawHref;
  const unwrapped = unwrapGoogleRedirect(rawHref);
  if (unwrapped && isExternalWebsite(unwrapped)) return unwrapped;
  return null;
}

function findBestVisible(scope, selector) {
  const nodes = Array.from((scope || document).querySelectorAll(selector)).filter(isVisible);
  if (nodes.length === 0) return null;
  // Prefer the right-most element (usually the place details panel vs left list).
  nodes.sort((a, b) => (b.getBoundingClientRect().x || 0) - (a.getBoundingClientRect().x || 0));
  return nodes[0] || null;
}

function findVisibleByAttrContains(scope, selector, attr, needles) {
  const nodes = Array.from((scope || document).querySelectorAll(selector)).filter(isVisible);
  const list = (needles || []).map((n) => String(n).toLowerCase());
  for (const node of nodes) {
    const val = normalizeText(node.getAttribute(attr) || "").toLowerCase();
    if (!val) continue;
    if (list.some((n) => n && val.includes(n))) return node;
  }
  return null;
}

async function waitForPlacePanelSelection(targetDetailUrl, timeoutMs = 8000) {
  const targetKey = extractPlaceKey(targetDetailUrl) || targetDetailUrl;
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const currentKey = extractPlaceKey(location.href) || location.href;
    const root = findPlacePanelRoot();
    const title = findVisiblePlaceTitle();
    const hasAny = !!(
      root.querySelector('[data-item-id="address"],[data-item-id^="phone"],[data-item-id="authority"],a[href^="tel:"],a[href^="http"]') ||
        title
    );
    if (hasAny && (currentKey === targetKey || location.href.includes("/maps/place/"))) return true;
    await new Promise((r) => setTimeout(r, 250));
  }
  return false;
}

function scrapeSelectedPlaceDetails() {
  const pane = document.querySelector("#pane") || document;
  const root = findPlacePanelRoot() || pane;

  // Attempt to extract address/phone/website from known data-item-id attributes
  const addressEl =
    findBestVisible(root, '[data-item-id="address"],button[data-item-id*="address"],div[data-item-id*="address"]') ||
    findBestVisible(pane, '[data-item-id="address"],button[data-item-id*="address"],div[data-item-id*="address"]') ||
    findVisibleByAttrContains(root, "*", "aria-label", ["address:"]) ||
    findVisibleByAttrContains(pane, "*", "aria-label", ["address:"]) ||
    findVisibleByAttrContains(root, "*", "data-tooltip", ["copy address"]) ||
    findVisibleByAttrContains(pane, "*", "data-tooltip", ["copy address"]);
  const address = normalizeText(
    addressEl?.getAttribute("aria-label")?.replace(/^Address:\s*/i, "") || addressEl?.textContent
  );

  const telLink =
    findBestVisible(root, 'a[href^="tel:"]') ||
    findBestVisible(pane, 'a[href^="tel:"]') ||
    document.querySelector('a[href^="tel:"]');
  const phoneEl =
    telLink ||
    findBestVisible(root, '[data-item-id^="phone"],button[data-item-id*="phone"],div[data-item-id*="phone"]') ||
    findBestVisible(pane, '[data-item-id^="phone"],button[data-item-id*="phone"],div[data-item-id*="phone"]') ||
    findVisibleByAttrContains(root, "*", "aria-label", ["phone:"]) ||
    findVisibleByAttrContains(pane, "*", "aria-label", ["phone:"]) ||
    findVisibleByAttrContains(root, "*", "data-tooltip", ["copy phone", "copy phone number"]) ||
    findVisibleByAttrContains(pane, "*", "data-tooltip", ["copy phone", "copy phone number"]);
  const phoneText =
    (telLink && telLink.getAttribute("href")?.replace(/^tel:/i, "")) ||
    phoneEl?.getAttribute("aria-label")?.replace(/^Phone:\s*/i, "") ||
    phoneEl?.textContent ||
    "";
  const phone = extractPhone(phoneText);

  // Website is usually an <a> element in the details panel
  const authorityEl =
    findBestVisible(root, '[data-item-id="authority"] a[href],a[data-item-id="authority"][href]') ||
    findBestVisible(pane, '[data-item-id="authority"] a[href],a[data-item-id="authority"][href]') ||
    findBestVisible(root, '[data-item-id="authority"]') ||
    findBestVisible(pane, '[data-item-id="authority"]') ||
    findVisibleByAttrContains(root, "*", "aria-label", ["website:"]) ||
    findVisibleByAttrContains(pane, "*", "aria-label", ["website:"]) ||
    findVisibleByAttrContains(root, "*", "data-tooltip", ["open website"]) ||
    findVisibleByAttrContains(pane, "*", "data-tooltip", ["open website"]);
  let authorityHref = null;
  if (authorityEl) {
    authorityHref =
      authorityEl.getAttribute?.("href") ||
      authorityEl.querySelector?.("a[href]")?.getAttribute?.("href") ||
      null;
  }

  const websiteElCandidates = Array.from(new Set([
    ...Array.from(root.querySelectorAll("a[href]")),
    ...Array.from(pane.querySelectorAll("a[href]")),
  ])).filter(isVisible);
  const websiteCandidates = [];
  const externalFromAuthority = toExternalWebsiteUrl(authorityHref);
  if (externalFromAuthority) websiteCandidates.push(externalFromAuthority);
  for (const a of websiteElCandidates) {
    const href = a.getAttribute("href") || "";
    const label = normalizeText(a.getAttribute("aria-label") || a.textContent);
    const external = toExternalWebsiteUrl(href);
    if (label.toLowerCase().includes("website") && external) websiteCandidates.push(external);
  }
  for (const a of websiteElCandidates) {
    const href = a.getAttribute("href") || "";
    const external = toExternalWebsiteUrl(href);
    if (external) websiteCandidates.push(external);
  }
  const website = preferNonSocialUrl(Array.from(new Set(websiteCandidates)));

  // Text-based fallbacks (some UIs show the domain as plain text)
  const lines = (root.innerText || pane.innerText || "")
    .split("\n")
    .map((l) => normalizeText(l))
    .filter((l) => l && l.length >= 2);

  const phoneFinal = phone || (() => {
    const phoneLine = lines.find(looksLikePhone);
    return phoneLine ? extractPhone(phoneLine) : null;
  })();

  const websiteFinal =
    website ||
    (() => {
      // Find something that looks like a domain, e.g. "almustafa.pk"
      const domainLine = lines.find((l) => {
        if (l.includes(" ")) return false;
        if (!/[a-zA-Z]/.test(l)) return false;
        if (!l.includes(".")) return false;
        if (l.includes("+")) return false; // plus code
        if (l.toLowerCase().includes("google.")) return false;
        if (l.length > 80) return false;
        return true;
      });
      if (!domainLine) return null;
      return `https://${domainLine.replace(/^https?:\/\//i, "")}`;
    })();

  // Address/phone/website can also appear as plain icon rows. As a last resort,
  // scan for likely candidates within the panel text.
  const phoneFromText = phoneFinal || (() => {
    const candidate = lines.find(looksLikePhone);
    return candidate ? extractPhone(candidate) : null;
  })();

  const websiteFromText =
    websiteFinal ||
    (() => {
      const candidate = lines.find((l) => {
        if (l.includes(" ")) return false;
        if (!/[a-zA-Z]/.test(l)) return false;
        if (!l.includes(".")) return false;
        if (l.includes("+")) return false;
        if (l.toLowerCase().includes("google.")) return false;
        if (l.length > 80) return false;
        return true;
      });
      if (!candidate) return null;
      return `https://${candidate.replace(/^https?:\/\//i, "")}`;
    })();

  const addressFinal =
    address ||
    (() => {
      // Prefer lines that look like a postal address (contains commas and/or country)
      const candidates = lines.filter((l) => {
        if (phoneFromText && l.includes(phoneFromText)) return false;
        if (websiteFromText && l.includes(websiteFromText)) return false;
        if (l.toLowerCase().includes("open")) return false;
        if (l.toLowerCase().includes("hours")) return false;
        if (l.toLowerCase().includes("rating")) return false;
        if (l.toLowerCase().includes("reviews")) return false;
        if (/^[A-Z0-9]{3,}\+[A-Z0-9]{2,}/.test(l)) return false; // plus code-ish
        return l.includes(",") && l.length >= 10;
      });
      const withCountry = candidates.find((l) => /pakistan|india|usa|united states|uk|united kingdom/i.test(l));
      return withCountry || candidates[0] || null;
    })();

  return {
    address: addressFinal || null,
    phone: phoneFromText || null,
    website: websiteFromText || null,
  };
}

function scrapeVisibleResults() {
  if (!isMapsSearchResultsPage()) return [];
  const feed = findFeedContainer();
  if (!feed) return [];

  const anchors = Array.from(feed.querySelectorAll('a[href*="/maps/place/"]'));
  const items = [];
  const seen = new Set();

  for (const a of anchors) {
    const item = extractCardDataFromAnchor(a);
    if (!item || !item.detail_url) continue;
    if (seen.has(item.detail_url)) continue;
    seen.add(item.detail_url);
    items.push(item);
  }

  return items;
}

async function sendNewItems(items) {
  if (!items.length) return;
  STATE.lastSentAt = Date.now();
  try {
    await chrome.runtime.sendMessage({ type: "mapsAddItems", items });
  } catch {
    // ignore (service worker may be asleep; it will wake on next message)
  }
}

async function clickNextUnprocessedResult() {
  if (STATE.processingDetails) return;
  const feed = findFeedContainer();
  if (!feed) return;

  const anchors = Array.from(feed.querySelectorAll('a[href*="/maps/place/"]'));
  const next = anchors.find((a) => {
    if (!a.href) return false;
    const key = extractPlaceKey(a.href) || a.href;
    return !STATE.processedDetailKeys.has(key);
  });
  if (!next) return;

  STATE.processingDetails = true;
  try {
    next.scrollIntoView({ block: "center" });
    next.click();

    // Wait for panel to load (more reliable than a fixed sleep)
    await waitForPlacePanelSelection(next.href, 10000);

    const details = scrapeSelectedPlaceDetails();
    const patch = {
      detail_url: next.href,
      place_key: extractPlaceKey(next.href),
      ...details,
      collected_at: new Date().toISOString(),
    };
    if (!patch.address && !patch.phone && !patch.website) {
      try {
        await chrome.runtime.sendMessage({
          type: "mapsPanelDebug",
          payload: { failed_for: next.href, ...debugPanelSnapshot() },
        });
      } catch {
        // ignore
      }
    }
    STATE.processedDetailKeys.add(patch.place_key || next.href);
    await sendNewItems([patch]);
  } finally {
    STATE.processingDetails = false;
  }
}

function startCapture() {
  if (STATE.capturing) return;
  STATE.capturing = true;

  const feed = findFeedContainer();
  if (feed) {
    STATE.observer = new MutationObserver(() => {
      // Debounce via timer
      if (!STATE.scrapeTimer) {
        STATE.scrapeTimer = setTimeout(async () => {
          STATE.scrapeTimer = null;
          const items = scrapeVisibleResults();
          await sendNewItems(items);
        }, 800);
      }
    });
    STATE.observer.observe(feed, { childList: true, subtree: true });
  }

  // Initial scrape and periodic refresh (in case mutations are missed)
  const tick = async () => {
    if (!STATE.capturing) return;
    const items = scrapeVisibleResults();
    await sendNewItems(items);
  };
  tick();
  STATE.interval = setInterval(tick, 5000);
}

function stopCapture() {
  STATE.capturing = false;
  if (STATE.observer) {
    STATE.observer.disconnect();
    STATE.observer = null;
  }
  if (STATE.scrapeTimer) {
    clearTimeout(STATE.scrapeTimer);
    STATE.scrapeTimer = null;
  }
  if (STATE.interval) {
    clearInterval(STATE.interval);
    STATE.interval = null;
  }
  if (STATE.detailTimer) {
    clearInterval(STATE.detailTimer);
    STATE.detailTimer = null;
  }
}

function debugPanelSnapshot() {
  const root = findPlacePanelRoot();
  const title = findVisiblePlaceTitle();
  const tel = (root.querySelector('a[href^="tel:"]') || document.querySelector('a[href^="tel:"]'))?.getAttribute("href") || null;
  const authority =
    (root.querySelector('[data-item-id="authority"] a[href]')?.getAttribute("href") ||
      root.querySelector('a[data-item-id="authority"][href]')?.getAttribute("href") ||
      root.querySelector('[data-item-id="authority"]')?.getAttribute?.("href") ||
      null);
  const externalAuthority = toExternalWebsiteUrl(authority);
  const lines = (root.innerText || "")
    .split("\n")
    .map((l) => normalizeText(l))
    .filter((l) => l && l.length >= 2)
    .slice(0, 80);

  return {
    href: location.href,
    title: title ? normalizeText(title.textContent) : null,
    rootTag: root?.tagName || null,
    rootId: root?.id || null,
    rootRole: root?.getAttribute?.("role") || null,
    telHref: tel,
    authorityHref: authority,
    authorityExternal: externalAuthority,
    sampleLines: lines,
  };
}

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (!msg || typeof msg !== "object") return;
  if (msg.type === "mapsStart") {
    startCapture();
    sendResponse({ ok: true });
  }
  if (msg.type === "mapsStop") {
    stopCapture();
    sendResponse({ ok: true });
  }
  if (msg.type === "mapsFetchDetails") {
    // Iterate through visible results and open each to capture address/phone/website.
    if (!STATE.detailTimer) {
      const throttleMs = typeof msg.throttleMs === "number" ? msg.throttleMs : 2500;
      STATE.detailTimer = setInterval(clickNextUnprocessedResult, Math.max(1000, throttleMs));
    }
    sendResponse({ ok: true });
  }
  if (msg.type === "mapsFetchDetailsStop") {
    if (STATE.detailTimer) {
      clearInterval(STATE.detailTimer);
      STATE.detailTimer = null;
    }
    sendResponse({ ok: true });
  }
  if (msg.type === "mapsDebugPanel") {
    sendResponse(debugPanelSnapshot());
  }
  if (msg.type === "mapsPing") {
    sendResponse({ ok: true, capturing: STATE.capturing });
  }
});

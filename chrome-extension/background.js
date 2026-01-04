// Background service worker for LeadFlux extension

chrome.runtime.onInstalled.addListener(() => {
  console.log('LeadFlux Email Finder extension installed');
});

const MAPS_STORAGE_KEY = "mapsCaptureItems";
const MAPS_STATE_KEY = "mapsCaptureState";
const MAPS_LAST_ERROR_KEY = "mapsLastError";
const MAPS_LAST_IMPORT_KEY = "mapsLastImport";
const MAPS_LAST_PANEL_DEBUG_KEY = "mapsLastPanelDebug";

async function getMapsState() {
  const result = await chrome.storage.local.get([MAPS_STATE_KEY]);
  return result[MAPS_STATE_KEY] || { capturing: false };
}

async function setMapsState(next) {
  await chrome.storage.local.set({ [MAPS_STATE_KEY]: next });
}

async function getMapsItems() {
  const result = await chrome.storage.local.get([MAPS_STORAGE_KEY]);
  return result[MAPS_STORAGE_KEY] || [];
}

async function setMapsItems(items) {
  await chrome.storage.local.set({ [MAPS_STORAGE_KEY]: items });
}

async function setLastError(message) {
  await chrome.storage.local.set({ [MAPS_LAST_ERROR_KEY]: message || "" });
}

async function getLastError() {
  const result = await chrome.storage.local.get([MAPS_LAST_ERROR_KEY]);
  return result[MAPS_LAST_ERROR_KEY] || "";
}

async function setLastImport(value) {
  await chrome.storage.local.set({ [MAPS_LAST_IMPORT_KEY]: value || null });
}

async function getLastImport() {
  const result = await chrome.storage.local.get([MAPS_LAST_IMPORT_KEY]);
  return result[MAPS_LAST_IMPORT_KEY] || null;
}

async function setLastPanelDebug(value) {
  await chrome.storage.local.set({ [MAPS_LAST_PANEL_DEBUG_KEY]: value || null });
}

async function getLastPanelDebug() {
  const result = await chrome.storage.local.get([MAPS_LAST_PANEL_DEBUG_KEY]);
  return result[MAPS_LAST_PANEL_DEBUG_KEY] || null;
}

async function getApiUrl() {
  const result = await chrome.storage.sync.get(["apiUrl"]);
  return (result.apiUrl || "http://localhost:8002").trim();
}

function toCsv(items) {
  const headers = [
    "name",
    "detail_url",
    "address",
    "phone",
    "website",
    "emails",
    "rating",
    "reviews",
    "meta_line",
    "collected_at",
  ];
  const escape = (v) => {
    const s = v === null || v === undefined ? "" : String(v);
    if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
    return s;
  };
  const lines = [headers.join(",")];
  for (const it of items) {
    const row = { ...it };
    if (Array.isArray(row.emails)) row.emails = row.emails.join("; ");
    lines.push(headers.map((h) => escape(row[h])).join(","));
  }
  return lines.join("\n");
}

async function downloadText(filename, text, mimeType) {
  // Use a data: URL (works reliably in MV3 service workers without needing Blob/object URLs).
  const url = `data:${mimeType};charset=utf-8,${encodeURIComponent(text)}`;
  await chrome.downloads.download({
    url,
    filename,
    saveAs: true,
  });
}

// Listen for messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  (async () => {
    // Legacy (LinkedIn)
    if (request.action === "findEmail") {
      sendResponse({ success: true });
      return;
    }

    // Google Maps capture
    if (request.type === "mapsAddItems") {
      const incoming = Array.isArray(request.items) ? request.items : [];
      const existing = await getMapsItems();
      const makeKey = (x) => x.place_key || x.detail_url;
      const byUrl = new Map(existing.map((x) => [makeKey(x), x]));
      for (const item of incoming) {
        if (!item || !item.detail_url) continue;
        const key = makeKey(item);
        const prev = byUrl.get(key) || {};
        byUrl.set(key, { ...prev, ...item });
      }
      const merged = Array.from(byUrl.values());
      await setMapsItems(merged);
      sendResponse({ ok: true, total: merged.length });
      return;
    }

    if (request.type === "mapsGet") {
      const [items, state, lastError, lastImport] = await Promise.all([
        getMapsItems(),
        getMapsState(),
        getLastError(),
        getLastImport(),
      ]);
      const lastPanelDebug = await getLastPanelDebug();
      sendResponse({ ok: true, items, state, lastError, lastImport, lastPanelDebug });
      return;
    }

    if (request.type === "mapsClear") {
      await setMapsItems([]);
      await setLastError("");
      await setLastImport(null);
      await setLastPanelDebug(null);
      sendResponse({ ok: true });
      return;
    }

    if (request.type === "mapsSetCapturing") {
      const capturing = !!request.capturing;
      await setMapsState({ capturing });
      sendResponse({ ok: true, capturing });
      return;
    }

    if (request.type === "mapsDownloadCsv") {
      try {
        const items = await getMapsItems();
        const csv = toCsv(items);
        await downloadText("google-maps-results.csv", csv, "text/csv");
        sendResponse({ ok: true });
      } catch (e) {
        sendResponse({ ok: false, error: String(e) });
      }
      return;
    }

    if (request.type === "mapsDownloadJson") {
      try {
        const items = await getMapsItems();
        await downloadText(
          "google-maps-results.json",
          JSON.stringify(items, null, 2),
          "application/json"
        );
        sendResponse({ ok: true });
      } catch (e) {
        sendResponse({ ok: false, error: String(e) });
      }
      return;
    }

    if (request.type === "mapsEnrichEmails") {
      try {
        const apiUrl = await getApiUrl();
        const items = await getMapsItems();
        const updated = [...items];
        let failures = 0;
        let processed = 0;

        for (let i = 0; i < updated.length; i++) {
          const item = updated[i];
          const website = item.website;
          if (!website) continue;
          if (Array.isArray(item.emails) && item.emails.length > 0) continue;

          const resp = await fetch(`${apiUrl}/api/google-maps/extract-contacts`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: website }),
          });
          processed += 1;
          if (!resp.ok) {
            failures += 1;
            // Back off a bit when failing (rate limiting / blocked)
            await new Promise((r) => setTimeout(r, Math.min(3000, 300 + failures * 200)));
            if (failures >= 25) {
              await setLastError("Email fetch stopped after too many failures.");
              break;
            }
            continue;
          }
          const data = await resp.json();
          const emails = Array.isArray(data.emails) ? data.emails : [];
          const phones = Array.isArray(data.phones) ? data.phones : [];
          item.emails = emails;
          if (!item.phone && phones.length > 0) {
            item.phone = phones[0];
          }

          // Persist every few items
          if (i % 5 === 0) {
            await setMapsItems(updated);
          }

          // Gentle delay to avoid hammering sites/backend
          await new Promise((r) => setTimeout(r, 300));
        }

        await setMapsItems(updated);
        sendResponse({ ok: true, processed, failures });
      } catch (e) {
        await setLastError(String(e));
        sendResponse({ ok: false, error: String(e) });
      }
      return;
    }

    if (request.type === "mapsImport") {
      try {
        const apiUrl = await getApiUrl();
        const items = await getMapsItems();
        const niche = (request.niche || "").trim() || undefined;
        const location = (request.location || "").trim() || undefined;

        const resp = await fetch(`${apiUrl}/api/google-maps/import`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ items, niche, location }),
        });
        if (!resp.ok) {
          const txt = await resp.text();
          await setLastError(txt || `HTTP ${resp.status}`);
          sendResponse({ ok: false, error: txt || `HTTP ${resp.status}` });
          return;
        }
        const data = await resp.json();
        await setLastImport({ at: new Date().toISOString(), ...data });
        sendResponse({ ok: true, ...data });
      } catch (e) {
        await setLastError(String(e));
        sendResponse({ ok: false, error: String(e) });
      }
      return;
    }

    if (request.type === "mapsPanelDebug") {
      // Store the last panel debug snapshot when detail scraping fails to find phone/website/address.
      await setLastPanelDebug(request.payload || null);
      sendResponse({ ok: true });
      return;
    }

    if (request.type === "mapsEnrichImportedLeads") {
      try {
        const apiUrl = await getApiUrl();
        const leadIds = Array.isArray(request.leadIds) ? request.leadIds : [];
        if (leadIds.length === 0) {
          sendResponse({ ok: false, error: "No lead IDs provided" });
          return;
        }
        const resp = await fetch(`${apiUrl}/api/google-maps/enrich-leads`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ lead_ids: leadIds, emails: true, phones: true, social_links: true }),
        });
        if (!resp.ok) {
          const txt = await resp.text();
          await setLastError(txt || `HTTP ${resp.status}`);
          sendResponse({ ok: false, error: txt || `HTTP ${resp.status}` });
          return;
        }
        const data = await resp.json();
        sendResponse({ ok: true, ...data });
      } catch (e) {
        await setLastError(String(e));
        sendResponse({ ok: false, error: String(e) });
      }
      return;
    }

    sendResponse({ ok: false, error: "Unknown request" });
  })();

  return true; // keep channel open for async
});

// Popup script for LeadFlux extension

document.addEventListener('DOMContentLoaded', async () => {
  const statusDiv = document.getElementById('status');
  const apiUrlInput = document.getElementById('apiUrl');
  const frontendUrlInput = document.getElementById('frontendUrl');
  const saveBtn = document.getElementById('saveBtn');
  const mapsSection = document.getElementById('mapsSection');
  const mapsStartBtn = document.getElementById('mapsStartBtn');
  const mapsStopBtn = document.getElementById('mapsStopBtn');
  const mapsFetchDetailsBtn = document.getElementById('mapsFetchDetailsBtn');
  const mapsFetchDetailsStopBtn = document.getElementById('mapsFetchDetailsStopBtn');
  const mapsSpeed = document.getElementById('mapsSpeed');
  const mapsSpeedLabel = document.getElementById('mapsSpeedLabel');
  const mapsCopyJsonBtn = document.getElementById('mapsCopyJsonBtn');
  const mapsDebugPanelBtn = document.getElementById('mapsDebugPanelBtn');
  const mapsDownloadCsvBtn = document.getElementById('mapsDownloadCsvBtn');
  const mapsDownloadJsonBtn = document.getElementById('mapsDownloadJsonBtn');
  const mapsEnrichEmailsBtn = document.getElementById('mapsEnrichEmailsBtn');
  const mapsImportBtn = document.getElementById('mapsImportBtn');
  const mapsImportStatus = document.getElementById('mapsImportStatus');
  const mapsEnrichImportedBtn = document.getElementById('mapsEnrichImportedBtn');
  const mapsNicheInput = document.getElementById('mapsNiche');
  const mapsLocationInput = document.getElementById('mapsLocation');
  const mapsClearBtn = document.getElementById('mapsClearBtn');
  const mapsCount = document.getElementById('mapsCount');
  const mapsLastError = document.getElementById('mapsLastError');

  // Load saved settings
  const result = await chrome.storage.sync.get(['apiUrl', 'frontendUrl', 'showInlineButton']);
  if (result.apiUrl) {
    apiUrlInput.value = result.apiUrl;
  }
  if (result.frontendUrl) {
    frontendUrlInput.value = result.frontendUrl;
  }
  const showInlineButtonCheckbox = document.getElementById('showInlineButton');
  if (showInlineButtonCheckbox) {
    showInlineButtonCheckbox.checked = result.showInlineButton !== false; // Default to true
  }

  // Check if we're on LinkedIn
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const isLinkedIn = !!(tab.url && tab.url.includes('linkedin.com'));
  const isGoogleMaps = !!(tab.url && tab.url.includes('google.com/maps'));

  if (isLinkedIn) {
    statusDiv.textContent = 'Active on LinkedIn';
    statusDiv.className = 'status active';
  } else if (isGoogleMaps) {
    statusDiv.textContent = 'Active on Google Maps';
    statusDiv.className = 'status active';
  } else {
    statusDiv.textContent = 'Open LinkedIn or Google Maps to use';
    statusDiv.className = 'status inactive';
  }

  // Google Maps capture UI
  async function refreshMapsStatus() {
    if (!isGoogleMaps) return;
    try {
      const resp = await chrome.runtime.sendMessage({ type: "mapsGet" });
      if (resp && resp.ok) {
        const count = Array.isArray(resp.items) ? resp.items.length : 0;
        mapsCount.textContent = `Collected: ${count}`;
        mapsCount.className = `status ${count > 0 ? "active" : "inactive"}`;
        mapsLastError.textContent = resp.lastError ? `Last error: ${resp.lastError}` : "";
        if (resp.lastPanelDebug) {
          mapsLastError.textContent = mapsLastError.textContent
            ? `${mapsLastError.textContent} (panel debug saved)`
            : "Panel debug saved (use Debug Panel button)";
        }
      }
    } catch {
      // ignore
    }
  }

  if (isGoogleMaps) {
    mapsSection.style.display = "block";

    // Load saved maps settings
    const mapsSettings = await chrome.storage.sync.get(["mapsNiche", "mapsLocation", "mapsSpeedMs"]);
    if (mapsNicheInput && mapsSettings.mapsNiche) mapsNicheInput.value = mapsSettings.mapsNiche;
    if (mapsLocationInput && mapsSettings.mapsLocation) mapsLocationInput.value = mapsSettings.mapsLocation;
    const savedSpeed = Number(mapsSettings.mapsSpeedMs || 2500);
    if (mapsSpeed) mapsSpeed.value = String(savedSpeed);
    if (mapsSpeedLabel) mapsSpeedLabel.textContent = `${(savedSpeed / 1000).toFixed(1)}s`;

    if (mapsSpeed) {
      mapsSpeed.addEventListener("input", async () => {
        const ms = Number(mapsSpeed.value || 2500);
        if (mapsSpeedLabel) mapsSpeedLabel.textContent = `${(ms / 1000).toFixed(1)}s`;
        await chrome.storage.sync.set({ mapsSpeedMs: ms });
      });
    }

    await refreshMapsStatus();

    mapsStartBtn.addEventListener("click", async () => {
      if (!tab.id) return;
      await chrome.runtime.sendMessage({ type: "mapsSetCapturing", capturing: true });
      await chrome.tabs.sendMessage(tab.id, { type: "mapsStart" });
      await refreshMapsStatus();
    });

    mapsStopBtn.addEventListener("click", async () => {
      if (!tab.id) return;
      await chrome.runtime.sendMessage({ type: "mapsSetCapturing", capturing: false });
      await chrome.tabs.sendMessage(tab.id, { type: "mapsStop" });
      await refreshMapsStatus();
    });

    mapsFetchDetailsBtn.addEventListener("click", async () => {
      if (!tab.id) return;
      const ms = Number(mapsSpeed?.value || 2500);
      await chrome.tabs.sendMessage(tab.id, { type: "mapsFetchDetails", throttleMs: ms });
      await refreshMapsStatus();
    });

    mapsFetchDetailsStopBtn.addEventListener("click", async () => {
      if (!tab.id) return;
      await chrome.tabs.sendMessage(tab.id, { type: "mapsFetchDetailsStop" });
      await refreshMapsStatus();
    });

    mapsCopyJsonBtn.addEventListener("click", async () => {
      const resp = await chrome.runtime.sendMessage({ type: "mapsGet" });
      if (!resp || !resp.ok) {
        alert("Copy failed: could not read items");
        return;
      }
      const text = JSON.stringify(resp.items || [], null, 2);
      await navigator.clipboard.writeText(text);
      alert("Copied JSON to clipboard");
    });

    mapsDebugPanelBtn.addEventListener("click", async () => {
      if (!tab.id) return;
      const [live, state] = await Promise.all([
        chrome.tabs.sendMessage(tab.id, { type: "mapsDebugPanel" }).catch(() => null),
        chrome.runtime.sendMessage({ type: "mapsGet" }).catch(() => null),
      ]);
      const combined = {
        live: live || null,
        lastStored: state?.lastPanelDebug || null,
      };
      const text = JSON.stringify(combined, null, 2);
      await navigator.clipboard.writeText(text);
      alert("Copied panel debug info to clipboard (live + last stored)");
    });

    mapsDownloadCsvBtn.addEventListener("click", async () => {
      const resp = await chrome.runtime.sendMessage({ type: "mapsDownloadCsv" });
      if (!resp || !resp.ok) {
        alert(`CSV download failed: ${resp?.error || "unknown error"}`);
      }
    });

    mapsDownloadJsonBtn.addEventListener("click", async () => {
      const resp = await chrome.runtime.sendMessage({ type: "mapsDownloadJson" });
      if (!resp || !resp.ok) {
        alert(`JSON download failed: ${resp?.error || "unknown error"}`);
      }
    });

    mapsEnrichEmailsBtn.addEventListener("click", async () => {
      mapsEnrichEmailsBtn.disabled = true;
      mapsEnrichEmailsBtn.textContent = "Fetching...";
      const resp = await chrome.runtime.sendMessage({ type: "mapsEnrichEmails" });
      mapsEnrichEmailsBtn.disabled = false;
      mapsEnrichEmailsBtn.textContent = "Fetch Emails (from website)";
      if (!resp || !resp.ok) {
        alert(`Email enrichment failed: ${resp?.error || "unknown error"}`);
      } else {
        await refreshMapsStatus();
        alert("Done. Download CSV/JSON again.");
      }
    });

    mapsImportBtn.addEventListener("click", async () => {
      mapsImportBtn.disabled = true;
      mapsImportBtn.textContent = "Importing...";
      mapsImportStatus.textContent = "";

      const mapsNiche = (mapsNicheInput?.value || "").trim();
      const mapsLocation = (mapsLocationInput?.value || "").trim();
      await chrome.storage.sync.set({ mapsNiche, mapsLocation });

      const resp = await chrome.runtime.sendMessage({ type: "mapsImport", niche: mapsNiche, location: mapsLocation });
      mapsImportBtn.disabled = false;
      mapsImportBtn.textContent = "Import to Backend";

      if (!resp || !resp.ok) {
        mapsImportStatus.textContent = `Import failed: ${resp?.error || "unknown error"}`;
        return;
      }
      mapsImportStatus.textContent = `Imported: ${resp.imported || 0}, Updated: ${resp.updated || 0}, Skipped: ${resp.skipped || 0}`;
    });

    mapsEnrichImportedBtn.addEventListener("click", async () => {
      mapsEnrichImportedBtn.disabled = true;
      mapsEnrichImportedBtn.textContent = "Enriching...";
      const state = await chrome.runtime.sendMessage({ type: "mapsGet" });
      const leadIds = state?.lastImport?.lead_ids;
      if (!Array.isArray(leadIds) || leadIds.length === 0) {
        mapsEnrichImportedBtn.disabled = false;
        mapsEnrichImportedBtn.textContent = "Enrich Imported Leads (backend)";
        alert("No imported lead IDs found. Import first.");
        return;
      }

      const resp = await chrome.runtime.sendMessage({ type: "mapsEnrichImportedLeads", leadIds });
      mapsEnrichImportedBtn.disabled = false;
      mapsEnrichImportedBtn.textContent = "Enrich Imported Leads (backend)";
      if (!resp || !resp.ok) {
        alert(`Enrich failed: ${resp?.error || "unknown error"}`);
        return;
      }
      alert(`Enrichment queued. Queued: ${resp.queued || 0}, Skipped: ${resp.skipped || 0}`);
    });

    mapsClearBtn.addEventListener("click", async () => {
      if (!confirm("Clear collected Google Maps results?")) return;
      await chrome.runtime.sendMessage({ type: "mapsClear" });
      await refreshMapsStatus();
    });

    // Update count while popup is open
    setInterval(refreshMapsStatus, 1500);
  }

  // Save settings
  saveBtn.addEventListener('click', async () => {
    const apiUrl = apiUrlInput.value.trim();
    const frontendUrl = frontendUrlInput.value.trim();
    const showInlineButton = showInlineButtonCheckbox ? showInlineButtonCheckbox.checked : true;
    
    if (!apiUrl) {
      alert('Please enter an API URL');
      return;
    }

    await chrome.storage.sync.set({ 
      apiUrl,
      frontendUrl: frontendUrl || undefined, // Only save if provided
      showInlineButton
    });
    alert('Settings saved!');
    
    // Reload the current tab to apply changes
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab.id) {
      chrome.tabs.reload(tab.id);
    }
  });
});


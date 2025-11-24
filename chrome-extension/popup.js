// Popup script for LeadFlux extension

document.addEventListener('DOMContentLoaded', async () => {
  const statusDiv = document.getElementById('status');
  const apiUrlInput = document.getElementById('apiUrl');
  const frontendUrlInput = document.getElementById('frontendUrl');
  const saveBtn = document.getElementById('saveBtn');

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
  if (tab.url && tab.url.includes('linkedin.com')) {
    statusDiv.textContent = 'Active on LinkedIn';
    statusDiv.className = 'status active';
  } else {
    statusDiv.textContent = 'Open a LinkedIn profile to use';
    statusDiv.className = 'status inactive';
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


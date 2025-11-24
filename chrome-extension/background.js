// Background service worker for LeadFlux extension

chrome.runtime.onInstalled.addListener(() => {
  console.log('LeadFlux Email Finder extension installed');
});

// Listen for messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'findEmail') {
    // Handle email finding request
    // This could be used for more complex logic
    sendResponse({ success: true });
  }
  return true;
});


/**
 * LeadFlux Email Finder - LinkedIn Content Script
 * 
 * This script runs on LinkedIn pages and:
 * 1. Detects profile pages
 * 2. Extracts name and company information
 * 3. Calls the LeadFlux API to find emails
 * 4. Displays results on the page
 */

(function() {
  'use strict';

  // Note: The "chrome-extension://invalid/" errors you may see in the console
  // are from LinkedIn's own JavaScript code trying to detect extensions.
  // These errors are harmless and occur when the extension context is invalidated
  // (e.g., after reloading the extension). They do not affect functionality.

  // Check if extension context is still valid
  function isExtensionContextValid() {
    try {
      // Try to access chrome.runtime - if it throws, context is invalidated
      if (!chrome || !chrome.runtime) return false;
      // Accessing chrome.runtime.id will throw if context is invalidated
      const id = chrome.runtime.id;
      return id !== undefined && id !== null;
    } catch (error) {
      // Context invalidated - silently return false
      return false;
    }
  }

  // Get current API URL (with fallback)
  async function getApiUrl() {
    return new Promise((resolve) => {
      if (!isExtensionContextValid()) {
        // Silently use default - don't log warnings for invalidated context
        resolve('http://localhost:8002');
        return;
      }
      
      try {
        chrome.storage.sync.get(['apiUrl'], (result) => {
          if (chrome.runtime.lastError) {
            // Context invalidated during the call
            resolve('http://localhost:8002');
            return;
          }
          resolve(result.apiUrl || 'http://localhost:8002');
        });
      } catch (error) {
        // Extension context invalidated - use default silently
        resolve('http://localhost:8002');
      }
    });
  }
  
  // Check if we're on a LinkedIn profile page
  function isProfilePage() {
    return window.location.pathname.match(/^\/in\/[^\/]+/);
  }

  // Check if we're on a LinkedIn search results page
  function isSearchPage() {
    return window.location.pathname.includes('/search/') || 
           window.location.search.includes('keywords=') ||
           document.querySelector('.search-results-container, .reusable-search__result-container');
  }

  // Extract name from LinkedIn profile
  function extractName() {
    // Try multiple selectors for profile name (LinkedIn changes their DOM structure frequently)
    const nameSelectors = [
      'h1.text-heading-xlarge',
      '.pv-text-details__left-panel h1',
      'h1[class*="text-heading"]',
      '.top-card-layout__title',
      '.ph5 h1',
      'main h1',
      '[data-test-id="profile-name"]',
      '.pv-text-details__left-panel h1.text-heading-xlarge',
      'h1.text-heading-xlarge.inline.t-24.v-align-middle.break-words'
    ];
    
    let nameElement = null;
    for (const selector of nameSelectors) {
      nameElement = document.querySelector(selector);
      if (nameElement && nameElement.textContent.trim()) {
        break;
      }
    }
    
    if (!nameElement) return null;
    
    const fullName = nameElement.textContent.trim();
    if (!fullName || fullName.length < 2) return null;
    
    const parts = fullName.split(' ').filter(p => p);
    return {
      first: parts[0] || '',
      last: parts.slice(1).join(' ') || '',
      full: fullName
    };
  }

  // Extract company from LinkedIn profile
  function extractCompany() {
    // Try multiple selectors for company name
    const selectors = [
      '.pv-text-details__left-panel .text-body-medium',
      '.pv-entity__secondary-title',
      '.experience-section .pv-entity__summary-info h3',
      '[data-test-id="experience-item"] .pv-entity__summary-info h3'
    ];
    
    for (const selector of selectors) {
      const element = document.querySelector(selector);
      if (element) {
        return element.textContent.trim();
      }
    }
    
    return null;
  }

  // Extract domain from company name (simple heuristic)
  function companyToDomain(companyName) {
    if (!companyName) return null;
    
    // Remove common suffixes and clean
    let domain = companyName
      .toLowerCase()
      .replace(/\s+(inc|llc|corp|corporation|ltd|limited|co|company)$/i, '')
      .replace(/[^a-z0-9]/g, '')
      .substring(0, 20); // Limit length
    
    return domain ? `${domain}.com` : null;
  }

  // Call LeadFlux API to find email
  async function findEmail(firstName, lastName, domain) {
    try {
      const apiUrl = await getApiUrl();
      const response = await fetch(`${apiUrl}/api/email-finder`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          first_name: firstName,
          last_name: lastName,
          domain: domain,
          skip_smtp: false, // Set to true for faster results
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error finding email:', error);
      return null;
    }
  }

  // Display email result on the page
  function displayEmailResult(result, container) {
    if (!result || !result.email) {
      container.innerHTML = '<div class="leadflux-no-email">No email found</div>';
      return;
    }

    const statusClass = result.status === 'valid' ? 'leadflux-valid' : 
                        result.status === 'risky' ? 'leadflux-risky' : 
                        'leadflux-unknown';
    
    const confidence = result.confidence ? Math.round(result.confidence * 100) : 0;

    container.innerHTML = `
      <div class="leadflux-email-result ${statusClass}">
        <div class="leadflux-email-header">
          <span class="leadflux-email-icon">📧</span>
          <span class="leadflux-email-address">${result.email}</span>
        </div>
        <div class="leadflux-email-details">
          <span class="leadflux-status">${result.status}</span>
          <span class="leadflux-confidence">${confidence}% confidence</span>
        </div>
        <button class="leadflux-save-btn" data-email="${result.email}">
          Save to Leads
        </button>
      </div>
    `;

    // Add click handler for save button
    const saveBtn = container.querySelector('.leadflux-save-btn');
    if (saveBtn) {
      saveBtn.addEventListener('click', async () => {
        // Use new LinkedIn capture endpoint with widget
        await saveLinkedInProfile(true, false, true);
      });
    }
  }

  // Extract headline from LinkedIn profile
  function extractHeadline() {
    const selectors = [
      '.text-body-medium.break-words',
      '.pv-text-details__left-panel .text-body-medium',
      '.top-card-layout__headline',
      '[data-test-id="headline"]',
    ];
    
    for (const selector of selectors) {
      const element = document.querySelector(selector);
      if (element) {
        return element.textContent.trim();
      }
    }
    
    return null;
  }

  // Extract location from profile (helper function)
  function extractLocation() {
    const locationSelectors = [
      '.text-body-small.inline.t-black--light.break-words',
      '.pv-text-details__left-panel .text-body-small',
      '[data-test-id="location"]',
      '.top-card-layout__first-subline'
    ];
    
    for (const selector of locationSelectors) {
      const element = document.querySelector(selector);
      if (element) {
        const text = element.textContent.trim();
        if (text && !text.includes('connections') && !text.includes('followers')) {
          return text;
        }
      }
    }
    return null;
  }

  // Save LinkedIn profile to leads (new unified endpoint)
  async function saveLinkedInProfile(autoFindEmail = true, skipSmtp = false, showWidget = true) {
    // Check if API key is configured
    const storage = await new Promise((resolve) => {
      if (!isExtensionContextValid()) {
        resolve({});
        return;
      }
      
      try {
        chrome.storage.sync.get(['apiUrl'], (result) => {
          if (chrome.runtime.lastError) {
            // Context invalidated during the call
            resolve({});
            return;
          }
          resolve(result);
        });
      } catch (error) {
        // Extension context invalidated - silently handle
        resolve({});
      }
    });
    
    if (!storage.apiUrl) {
      if (showWidget) {
        renderWidget(null, 'Not configured: Add your API URL in the extension popup.');
      } else {
        showNotification('Not configured: Add your API URL in the extension popup', 'error');
      }
      return null;
    }

    const name = extractName();
    const company = extractCompany();
    const headline = extractHeadline();
    const linkedinUrl = window.location.href;

    if (!name || !name.full) {
      if (showWidget) {
        renderWidget(null, 'Could not extract name from LinkedIn profile');
      } else {
        showNotification('Could not extract name from LinkedIn profile', 'error');
      }
      return null;
    }

    try {
      const apiUrl = await getApiUrl();
      const response = await fetch(`${apiUrl}/api/leads/linkedin-capture`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          full_name: name.full,
          first_name: name.first,
          last_name: name.last,
          headline: headline,
          title: headline, // Use headline as title for now
          company_name: company,
          linkedin_url: linkedinUrl,
          company_domain: companyToDomain(company),
          auto_find_email: autoFindEmail,
          skip_smtp: skipSmtp,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMsg = errorData.detail || `API error: ${response.status}`;
        
        // Handle specific error cases
        if (response.status === 401) {
          if (showWidget) {
            renderWidget(null, 'Auth error: Check your API key or log in again.');
          } else {
            showNotification('Auth error: Check your API key', 'error');
          }
          return null;
        }
        
        throw new Error(errorMsg);
      }

      const data = await response.json();
      console.log('Lead captured:', data);
      
      // Show widget if requested
      if (showWidget) {
        renderWidget(data);
      } else {
        // Fallback to notification if widget disabled
        let message = 'Lead saved successfully!';
        if (data.email_status && data.email_status.email) {
          message += ` Email: ${data.email_status.email} (${data.email_status.status || 'unknown'})`;
        } else if (data.job) {
          message += ' Email finder job queued.';
        }
        showNotification(message, 'success');
      }
      
      return data;
    } catch (error) {
      console.error('Error saving LinkedIn profile:', error);
      
      // Handle network errors
      if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        if (showWidget) {
          renderWidget(null, 'Network issue: Couldn\'t reach the server.');
        } else {
          showNotification('Network error: Couldn\'t reach the server', 'error');
        }
      } else {
        if (showWidget) {
          renderWidget(null, error.message || 'Failed to save lead');
        } else {
          showNotification('Failed to save lead: ' + error.message, 'error');
        }
      }
      return null;
    }
  }

  // Legacy function for backward compatibility (saves found email)
  async function saveToLeads(result) {
    // Use the new LinkedIn capture endpoint instead
    return saveLinkedInProfile(true, false);
  }

  // Show notification (helper function)
  function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `leadflux-notification leadflux-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 12px 20px;
      background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
      color: white;
      border-radius: 8px;
      z-index: 10000;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
      font-size: 14px;
      max-width: 300px;
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
      notification.style.opacity = '0';
      notification.style.transition = 'opacity 0.3s';
      setTimeout(() => notification.remove(), 300);
    }, 3000);
  }

  // LinkedIn overlay widget
  const WIDGET_ID = "leadflux-linkedin-widget";

  function injectWidgetStyles() {
    if (document.getElementById("leadflux-widget-styles")) return;
    const style = document.createElement("style");
    style.id = "leadflux-widget-styles";
    style.textContent = `
      #${WIDGET_ID} {
        position: fixed;
        right: 16px;
        bottom: 16px;
        z-index: 999999;
        max-width: 320px;
        background: #020617;
        color: #e5e7eb;
        border-radius: 12px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.45);
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        padding: 12px 14px;
        border: 1px solid #1f2937;
        animation: slideInUp 0.3s ease-out;
      }
      @keyframes slideInUp {
        from {
          transform: translateY(20px);
          opacity: 0;
        }
        to {
          transform: translateY(0);
          opacity: 1;
        }
      }
      #${WIDGET_ID} h4 {
        margin: 0 0 4px;
        font-size: 14px;
        font-weight: 600;
        color: #38bdf8;
      }
      #${WIDGET_ID} .leadflux-sub {
        font-size: 12px;
        color: #9ca3af;
        margin-bottom: 6px;
      }
      #${WIDGET_ID} .leadflux-email {
        font-size: 13px;
        margin-bottom: 4px;
        word-break: break-all;
        color: #e5e7eb;
      }
      #${WIDGET_ID} .leadflux-status {
        font-size: 11px;
        margin-bottom: 8px;
        color: #a3e635;
      }
      #${WIDGET_ID} .leadflux-status.risky { color: #f97316; }
      #${WIDGET_ID} .leadflux-status.invalid { color: #f97373; }
      #${WIDGET_ID} .leadflux-status.unknown { color: #9ca3af; }
      #${WIDGET_ID} button {
        font-size: 12px;
        border: none;
        border-radius: 999px;
        padding: 6px 10px;
        cursor: pointer;
        background: #0ea5e9;
        color: white;
        transition: background 0.2s;
      }
      #${WIDGET_ID} button:hover {
        background: #0284c7;
      }
      #${WIDGET_ID} .leadflux-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
      }
      #${WIDGET_ID} .leadflux-close {
        cursor: pointer;
        font-size: 18px;
        color: #6b7280;
        margin-left: 4px;
        line-height: 1;
        transition: color 0.2s;
      }
      #${WIDGET_ID} .leadflux-close:hover {
        color: #9ca3af;
      }
    `;
    document.head.appendChild(style);
  }

  function removeWidget() {
    const existing = document.getElementById(WIDGET_ID);
    if (existing) existing.remove();
  }

  // Fetch lists for dropdown
  async function fetchLists() {
    try {
      const apiUrl = await getApiUrl();
      const response = await fetch(`${apiUrl}/api/lists`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        return [];
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching lists:', error);
      return [];
    }
  }

  // Fetch usage/credits
  async function fetchUsage() {
    try {
      const apiUrl = await getApiUrl();
      const response = await fetch(`${apiUrl}/api/me/usage`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        return null;
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching usage:', error);
      return null;
    }
  }

  // Poll for email status updates
  async function pollEmailStatus(leadId, maxAttempts = 12, interval = 5000) {
    let attempts = 0;
    
    const poll = async () => {
      if (attempts >= maxAttempts) return null;
      
      try {
        const apiUrl = await getApiUrl();
        const response = await fetch(`${apiUrl}/api/leads/${leadId}/email-status`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          return null;
        }

        const status = await response.json();
        if (status && status.email) {
          return status;
        }

        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, interval);
        }
        return null;
      } catch (error) {
        console.error('Error polling email status:', error);
        return null;
      }
    };

    return poll();
  }

  function renderWidget(leadResponse, error = null) {
    injectWidgetStyles();
    removeWidget();

    const wrapper = document.createElement("div");
    wrapper.id = WIDGET_ID;

    // Handle error states
    if (error) {
      wrapper.innerHTML = `
        <div class="leadflux-row">
          <h4>LeadFlux – Error</h4>
          <span class="leadflux-close">×</span>
        </div>
        <div class="leadflux-sub" style="color: #f97373;">${error}</div>
        <div class="leadflux-row">
          <button type="button" id="leadflux-retry-btn">Retry</button>
        </div>
      `;
      document.body.appendChild(wrapper);
      wrapper.querySelector(".leadflux-close").addEventListener("click", () => wrapper.remove());
      
      const retryBtn = document.getElementById("leadflux-retry-btn");
      if (retryBtn) {
        retryBtn.addEventListener("click", async () => {
          await saveLinkedInProfile(true, false, true);
        });
      }
      return;
    }

    const lead = leadResponse;
    const emailStatus = lead.email_status;
    const hasEmail = emailStatus && emailStatus.email;

    const statusText = hasEmail
      ? `${emailStatus.status === 'valid' ? '✅' : emailStatus.status === 'risky' ? '⚠️' : '❓'} ${emailStatus.status || ""} (${Math.round((emailStatus.confidence || 0) * 100)}%)`
      : "⏳ Finding & verifying email…";

    const statusClass = hasEmail
      ? `leadflux-status ${emailStatus.status || ""}`
      : "leadflux-status";

    const titleLine = lead.title && lead.company_name
      ? `${lead.title} @ ${lead.company_name}`
      : (lead.company_name || lead.title || lead.headline || "");

    // Fetch lists and usage asynchronously
    let listsHtml = '<option value="">No list</option>';
    let usageHtml = '';

    fetchLists().then(lists => {
      if (lists && lists.length > 0) {
        listsHtml = '<option value="">No list</option>' + lists.map(list => 
          `<option value="${list.id}">${list.name} (${list.total_leads || 0})</option>`
        ).join('');
        const select = wrapper.querySelector('#leadflux-list-select');
        if (select) select.innerHTML = listsHtml;
      }
    });

    fetchUsage().then(usage => {
      if (usage) {
        const remaining = usage.credits_remaining || 0;
        const total = usage.credits_total || 1000;
        const percent = (remaining / total) * 100;
        
        if (percent < 10) {
          usageHtml = `<div class="leadflux-usage" style="font-size: 10px; color: #f97316; margin-top: 4px;">⚠️ Low on credits – ${remaining} left</div>`;
        } else {
          usageHtml = `<div class="leadflux-usage" style="font-size: 10px; color: #9ca3af; margin-top: 4px;">🔋 ${remaining.toLocaleString()} credits left</div>`;
        }
        
        const usageDiv = wrapper.querySelector('.leadflux-usage-container');
        if (usageDiv) usageDiv.innerHTML = usageHtml;
      }
    });

    wrapper.innerHTML = `
      <div class="leadflux-row">
        <h4>LeadFlux – ${hasEmail ? "Email found" : "Lead saved"}</h4>
        <span class="leadflux-close">×</span>
      </div>
      <div class="leadflux-sub">${lead.full_name}${titleLine ? " · " + titleLine : ""}</div>
      <div class="leadflux-email">
        ${hasEmail ? `📧 ${emailStatus.email}` : "📧 …"}
      </div>
      <div class="${statusClass}">
        ${statusText}
      </div>
      <div style="margin: 8px 0;">
        <select id="leadflux-list-select" style="width: 100%; padding: 6px; background: #1e293b; border: 1px solid #334155; border-radius: 4px; color: #e2e8f0; font-size: 12px;">
          ${listsHtml}
        </select>
      </div>
      <div class="leadflux-usage-container"></div>
      <div class="leadflux-row" style="gap: 4px;">
        <button type="button" id="leadflux-save-list-btn" style="flex: 1;">Save to List</button>
        <button type="button" id="leadflux-open-btn" style="flex: 1;">Open in LeadFlux</button>
      </div>
    `;

    document.body.appendChild(wrapper);

    wrapper.querySelector(".leadflux-close").addEventListener("click", () => wrapper.remove());
    
    // Keyboard shortcuts
    const handleKeyDown = (e) => {
      // Only handle if widget is visible and user is not typing in an input
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }
      
      // Ctrl+S or Cmd+S to save to list
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        const saveBtn = document.getElementById("leadflux-save-list-btn");
        if (saveBtn && !saveBtn.disabled) {
          saveBtn.click();
        }
      }
      
      // Escape to close
      if (e.key === 'Escape') {
        const closeBtn = wrapper.querySelector(".leadflux-close");
        if (closeBtn) {
          closeBtn.click();
        }
      }
    };
    
    document.addEventListener("keydown", handleKeyDown);
    
    // Clean up listener when widget is removed
    const originalRemove = wrapper.remove.bind(wrapper);
    wrapper.remove = function() {
      document.removeEventListener("keydown", handleKeyDown);
      originalRemove();
    };

    // Save to list button
    const saveListBtn = document.getElementById("leadflux-save-list-btn");
    if (saveListBtn) {
      saveListBtn.addEventListener("click", async () => {
        const select = document.getElementById("leadflux-list-select");
        const listId = select ? parseInt(select.value) : null;
        
        if (!listId) {
          showNotification('Please select a list', 'info');
          return;
        }

        saveListBtn.disabled = true;
        saveListBtn.textContent = 'Saving...';
        
        try {
          // Re-save with list_id
          const apiUrl = await getApiUrl();
          const name = extractName();
          const company = extractCompany();
          const headline = extractHeadline();
          
          const response = await fetch(`${apiUrl}/api/leads/linkedin-capture`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              full_name: name.full,
              first_name: name.first,
              last_name: name.last,
              headline: headline,
              title: headline,
              company_name: company,
              linkedin_url: window.location.href,
              company_domain: companyToDomain(company),
              auto_find_email: false, // Already found
              list_id: listId,
            }),
          });

          if (response.ok) {
            showNotification('Saved to list!', 'success');
            saveListBtn.textContent = 'Saved ✓';
            setTimeout(() => {
              saveListBtn.disabled = false;
              saveListBtn.textContent = 'Save to List';
            }, 2000);
          } else {
            throw new Error('Failed to save to list');
          }
        } catch (error) {
          console.error('Error saving to list:', error);
          showNotification('Failed to save to list', 'error');
          saveListBtn.disabled = false;
          saveListBtn.textContent = 'Save to List';
        }
      });
    }

    // Open in LeadFlux button
    const openBtn = document.getElementById("leadflux-open-btn");
    if (openBtn) {
      openBtn.addEventListener("click", async () => {
        // Get frontend URL (try storage first, then derive from API URL)
        const storage = await new Promise((resolve) => {
          if (!isExtensionContextValid()) {
            resolve({});
            return;
          }
          
          try {
            chrome.storage.sync.get(['frontendUrl', 'apiUrl'], (result) => {
              if (chrome.runtime.lastError) {
                // Context invalidated during the call
                resolve({});
                return;
              }
              resolve(result);
            });
          } catch (error) {
            // Extension context invalidated - silently handle
            resolve({});
          }
        });
        
        let frontendUrl = storage.frontendUrl;
        
        // If no frontend URL stored, try to derive from API URL
        if (!frontendUrl) {
          const apiUrl = storage.apiUrl || 'http://localhost:8002';
          // Replace port 8002 with 3000 or 3001 (common Next.js ports)
          if (apiUrl.includes(':8002')) {
            frontendUrl = apiUrl.replace(':8002', ':3000');
          } else if (apiUrl.includes('localhost')) {
            frontendUrl = apiUrl.replace(/:\d+/, ':3000');
          } else {
            // For production, assume frontend is on same domain without /api
            frontendUrl = apiUrl.replace(/\/api\/?$/, '');
          }
        }
        
        const url = `${frontendUrl}/leads/${lead.id}`;
        window.open(url, "_blank");
      });
    }

    // If email not found yet, start polling
    if (!hasEmail && lead.id) {
      pollEmailStatus(lead.id).then(status => {
        if (status) {
          // Update widget with new email status
          const emailDiv = wrapper.querySelector('.leadflux-email');
          const statusDiv = wrapper.querySelector('.leadflux-status');
          if (emailDiv) {
            emailDiv.innerHTML = `📧 ${status.email}`;
          }
          if (statusDiv) {
            const statusText = `${status.status === 'valid' ? '✅' : status.status === 'risky' ? '⚠️' : '❓'} ${status.status || ""} (${Math.round((status.confidence || 0) * 100)}%)`;
            statusDiv.innerHTML = statusText;
            statusDiv.className = `leadflux-status ${status.status || ""}`;
          }
        }
      });
    }

    // Auto-remove after 15 seconds (longer to allow for list selection)
    setTimeout(() => {
      if (document.getElementById(WIDGET_ID)) {
        wrapper.style.opacity = '0';
        wrapper.style.transition = 'opacity 0.3s';
        setTimeout(() => wrapper.remove(), 300);
      }
    }, 15000);
  }

  // Add inline "Find email with LeadFlux" button
  function addInlineButton() {
    if (!isProfilePage()) return;
    if (document.getElementById('leadflux-inline-btn')) return;

    // Check if user wants inline button enabled
    if (!isExtensionContextValid()) {
      // Extension context invalidated - skip inline button
      return;
    }
    
    try {
      chrome.storage.sync.get(['showInlineButton'], (result) => {
        if (chrome.runtime.lastError) {
          // Context invalidated - skip inline button
          return;
        }
        if (result.showInlineButton === false) return; // Default to true if not set

      const nameElement = document.querySelector('h1.text-heading-xlarge, .pv-text-details__left-panel h1');
      if (!nameElement) return;

      // Try to find a good place to inject (near the name)
      const container = nameElement.parentElement || nameElement.nextElementSibling;
      if (!container) return;

      const btn = document.createElement('button');
      btn.id = 'leadflux-inline-btn';
      btn.textContent = '🔍 Find email with LeadFlux';
      btn.style.cssText = `
        margin-left: 12px;
        padding: 6px 12px;
        background: #0ea5e9;
        color: white;
        border: none;
        border-radius: 6px;
        font-size: 12px;
        cursor: pointer;
        font-weight: 500;
        transition: background 0.2s;
      `;
      btn.addEventListener('mouseenter', () => {
        btn.style.background = '#0284c7';
      });
      btn.addEventListener('mouseleave', () => {
        btn.style.background = '#0ea5e9';
      });
      btn.addEventListener('click', async () => {
        btn.disabled = true;
        btn.textContent = 'Saving...';
        try {
          await saveLinkedInProfile(true, false, true);
        } catch (error) {
          console.error('Error saving lead:', error);
        } finally {
          btn.disabled = false;
          btn.textContent = '🔍 Find email with LeadFlux';
        }
      });

      container.insertBefore(btn, nameElement.nextSibling);
      });
    } catch (error) {
      // Extension context invalidated - continue without inline button
      console.warn('Extension context invalidated, skipping inline button');
    }
  }

  // Main function to inject email finder widget
  function injectEmailFinder() {
    // Check if already injected
    if (document.getElementById('leadflux-email-widget')) {
      return;
    }

    if (!isProfilePage()) {
      return;
    }

    // Add inline button instead of auto-injecting widget
    addInlineButton();

    const name = extractName();
    const company = extractCompany();
    const domain = companyToDomain(company);

    if (!name || !name.first || !domain) {
      return; // Can't find email without name and domain
    }

    // Find a good place to inject the widget (near the profile header)
    const profileHeader = document.querySelector('.pv-text-details__left-panel, .ph5.pb5');
    if (!profileHeader) {
      return;
    }

    // Create widget container (only shown when user clicks "Find Email")
    const widget = document.createElement('div');
    widget.id = 'leadflux-email-widget';
    widget.className = 'leadflux-widget';
    widget.style.display = 'none'; // Hidden by default
    widget.innerHTML = `
      <div class="leadflux-widget-header">
        <span class="leadflux-logo">🔍 LeadFlux</span>
        <button class="leadflux-save-btn" style="margin-right: 8px;">Save to Leads</button>
        <button class="leadflux-find-btn">Find Email</button>
      </div>
      <div class="leadflux-widget-content">
        <div class="leadflux-loading" style="display: none;">
          Finding email...
        </div>
        <div class="leadflux-result"></div>
      </div>
    `;

    // Insert widget (hidden)
    profileHeader.appendChild(widget);

    // Add click handler for "Save to Leads" (new unified endpoint)
    const saveBtn = widget.querySelector('.leadflux-save-btn');
    if (saveBtn) {
      saveBtn.addEventListener('click', async () => {
        saveBtn.disabled = true;
        saveBtn.textContent = 'Saving...';
        
        try {
          // Save and show widget
          await saveLinkedInProfile(true, false, true);
        } catch (error) {
          console.error('Error saving lead:', error);
        } finally {
          saveBtn.disabled = false;
          saveBtn.textContent = 'Save to Leads';
        }
      });
    }

    // Add click handler for "Find Email" (legacy, still works)
    const findBtn = widget.querySelector('.leadflux-find-btn');
    const loadingDiv = widget.querySelector('.leadflux-loading');
    const resultDiv = widget.querySelector('.leadflux-result');

    if (findBtn) {
      findBtn.addEventListener('click', async () => {
        loadingDiv.style.display = 'block';
        resultDiv.innerHTML = '';
        findBtn.disabled = true;

        const result = await findEmail(name.first, name.last, domain);
        
        loadingDiv.style.display = 'none';
        findBtn.disabled = false;

        if (result) {
          displayEmailResult(result, resultDiv);
        } else {
          resultDiv.innerHTML = '<div class="leadflux-error">Failed to find email</div>';
        }
      });
    }
  }

  // Run on page load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectEmailFinder);
  } else {
    injectEmailFinder();
  }

  // ============================================
  // LinkedIn Search Results Scraping Feature
  // ============================================

  // Extract profile data from search result card
  function extractProfileFromCard(cardElement) {
    try {
      // Try multiple selectors for LinkedIn search result cards (updated for 2024 LinkedIn structure)
      const nameSelectors = [
        '.entity-result__title-text a',
        '.entity-result__title a',
        'h3 a[href*="/in/"]',
        'h2 a[href*="/in/"]',
        '.base-search-card__title a',
        '.search-result__result-link',
        'a[href*="/in/"][href*="?miniProfile"]',
        '.app-aware-link[href*="/in/"]',
        'span[dir="ltr"] a[href*="/in/"]', // New LinkedIn structure
        '.entity-result__title-link', // Alternative structure
        'a[data-control-name="search_srp_result"]' // Search result link
      ];
      
      let nameLink = null;
      for (const selector of nameSelectors) {
        nameLink = cardElement.querySelector(selector);
        if (nameLink && nameLink.textContent.trim().length > 1) break;
      }
      
      // Also try finding any link with /in/ in href that has visible text
      if (!nameLink || !nameLink.textContent.trim()) {
        const allLinks = cardElement.querySelectorAll('a[href*="/in/"]');
        for (const link of allLinks) {
          const href = link.getAttribute('href') || link.href;
          const linkText = link.textContent.trim() || link.innerText.trim();
          
          // Filter out overlay URLs and only get actual profile URLs with names
          if (href && linkText && linkText.length > 1 &&
              href.includes('/in/') && 
              !href.includes('miniProfile') && 
              !href.includes('/overlay/') && 
              !href.includes('/recent-activity/') &&
              !href.includes('/opportunities/') &&
              !href.includes('urn:li:fsd') &&
              href.match(/\/in\/[^\/]+$/)) {
            nameLink = link;
            break;
          }
        }
      }
      
      if (!nameLink) {
        // Last resort: find any link with /in/ and get text from parent or span
        const anyInLink = cardElement.querySelector('a[href*="/in/"]');
        if (anyInLink) {
          // Try to get name from link or nearby span
          const nameSpan = anyInLink.querySelector('span[aria-hidden="true"]') || 
                          anyInLink.parentElement?.querySelector('span');
          if (nameSpan && nameSpan.textContent.trim()) {
            nameLink = { textContent: nameSpan.textContent.trim(), href: anyInLink.href || anyInLink.getAttribute('href') };
          } else {
            nameLink = anyInLink;
          }
        } else {
          return null;
        }
      }

      // Extract name - handle both direct link and object with textContent
      let fullName = (nameLink.textContent || nameLink.innerText || '').trim();
      
      // If name is still empty, try getting from parent element
      if (!fullName || fullName.length < 2) {
        const parentName = nameLink.parentElement?.textContent?.trim();
        if (parentName && parentName.length > 2 && parentName.length < 100) {
          const nameMatch = parentName.match(/^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)/);
          if (nameMatch) {
            fullName = nameMatch[1];
          } else {
            // Try first line of parent text
            const firstLine = parentName.split('\n')[0].trim();
            if (firstLine.length > 2 && firstLine.length < 100) {
              fullName = firstLine;
            }
          }
        }
      }
      
      if (!fullName || fullName.length < 2) {
        return null;
      }
      
      // Get profile URL - handle both direct link and object with href
      let profileUrl = nameLink.href || nameLink.getAttribute('href') || '';
      if (profileUrl && !profileUrl.startsWith('http')) {
        profileUrl = 'https://www.linkedin.com' + profileUrl;
      }
      
      // Clean up URL - remove query params and overlay paths
      if (profileUrl) {
        // Remove query params like ?miniProfile
        if (profileUrl.includes('?')) {
          profileUrl = profileUrl.split('?')[0];
        }
        // Filter out overlay URLs (like /overlay/about-this-profile/, /overlay/contact-info/)
        if (profileUrl.includes('/overlay/') || profileUrl.includes('/recent-activity/')) {
          return null; // Skip overlay/modals, not actual profile pages
        }
        // Only accept actual profile URLs (must have /in/username pattern)
        if (!profileUrl.match(/\/in\/[^\/]+$/)) {
          return null; // Not a valid profile URL
        }
      }
      
      // Extract headline/title - try multiple selectors (updated for 2024 LinkedIn)
      const headlineSelectors = [
        '.entity-result__primary-subtitle',
        '.entity-result__summary',
        '.search-result__snippets',
        '.base-search-card__subtitle',
        '.entity-result__summary-text',
        '.search-result__info',
        'span[aria-hidden="true"]', // New LinkedIn structure
        '.entity-result__primary-subtitle-text',
        'div[class*="subtitle"]'
      ];
      let headlineEl = null;
      for (const selector of headlineSelectors) {
        headlineEl = cardElement.querySelector(selector);
        if (headlineEl && headlineEl.textContent.trim() && headlineEl.textContent.trim().length > 3) break;
      }
      const headline = headlineEl ? headlineEl.textContent.trim() : '';

      // Extract company - try multiple selectors (updated for 2024 LinkedIn)
      const companySelectors = [
        '.entity-result__secondary-subtitle',
        '.entity-result__summary-text',
        '.search-result__info',
        '.base-search-card__metadata',
        '.entity-result__insights',
        'div[class*="secondary"]',
        'span[class*="secondary"]'
      ];
      let companyEl = null;
      for (const selector of companySelectors) {
        companyEl = cardElement.querySelector(selector);
        const companyText = companyEl ? companyEl.textContent.trim() : '';
        if (companyText && companyText.length > 2 && 
            !companyText.includes('connection') && 
            !companyText.includes('follower') &&
            !companyText.match(/^\d+$/)) { // Not just a number
          break;
        }
        companyEl = null;
      }
      const company = companyEl ? companyEl.textContent.trim() : '';

      // Extract location - try multiple selectors (updated for 2024 LinkedIn)
      const locationSelectors = [
        '.entity-result__tertiary-subtitle',
        '.search-result__location',
        '.entity-result__insights',
        '[class*="location"]',
        'span[class*="tertiary"]',
        'div[class*="location"]'
      ];
      let locationEl = null;
      for (const selector of locationSelectors) {
        locationEl = cardElement.querySelector(selector);
        const locationText = locationEl ? locationEl.textContent.trim() : '';
        if (locationText && locationText.length > 2 && 
            !locationText.includes('connection') &&
            !locationText.includes('follower')) {
          break;
        }
        locationEl = null;
      }
      const location = locationEl ? locationEl.textContent.trim() : '';

      const nameParts = fullName.split(' ').filter(p => p.length > 0);
      return {
        full_name: fullName,
        first_name: nameParts[0] || '',
        last_name: nameParts.slice(1).join(' ') || '',
        headline: headline,
        company_name: company,
        location: location,
        linkedin_url: profileUrl,
        element: cardElement
      };
    } catch (error) {
      console.error('Error extracting profile from card:', error);
      return null;
    }
  }

  // Get all profile cards from search results
  function getAllProfileCards() {
    console.log('🔍 Starting profile detection...');
    
    // Try multiple selectors for LinkedIn search result containers (updated for 2024 LinkedIn structure)
    const cardSelectors = [
      'li.reusable-search__result-container',
      '.reusable-search__result-container',
      'li[data-chameleon-result-urn]', // New LinkedIn structure
      '.entity-result__item',
      '.search-result',
      '.base-card',
      'li[class*="result"]',
      '.search-results__list-item',
      'li[class*="search-result"]',
      '.scaffold-finite-scroll__content li', // LinkedIn's scroll container
      'ul.reusable-search__entity-result-list > li', // People search results
      'ul.search-results__list > li'
    ];
    
    let cards = [];
    for (const selector of cardSelectors) {
      const found = document.querySelectorAll(selector);
      if (found.length > 0) {
        cards = Array.from(found);
        console.log(`✅ Found ${cards.length} cards with selector: ${selector}`);
        break;
      }
    }
    
    // If no cards found with specific selectors, use comprehensive link-based detection
    if (cards.length === 0) {
      console.log('⚠️ No cards found with standard selectors, using link-based detection...');
      const allLinks = document.querySelectorAll('a[href*="/in/"]');
      console.log(`Found ${allLinks.length} total /in/ links`);
      
      const uniqueCards = new Map(); // Use Map to deduplicate by URL
      const seenUrls = new Set();
      
      allLinks.forEach(link => {
        const href = link.getAttribute('href') || link.href;
        if (!href) return;
        
        // Clean and validate URL
        let cleanUrl = href.split('?')[0].split('#')[0];
        if (!cleanUrl.startsWith('http')) {
          cleanUrl = 'https://www.linkedin.com' + cleanUrl;
        }
        
        // Filter out invalid URLs
        if (cleanUrl.includes('/in/') && 
            !cleanUrl.includes('miniProfile') && 
            !cleanUrl.includes('/overlay/') && 
            !cleanUrl.includes('/recent-activity/') &&
            !cleanUrl.includes('/opportunities/') &&
            !cleanUrl.includes('urn:li:fsd') &&
            cleanUrl.match(/\/in\/[^\/]+$/)) {
          
          // Avoid duplicates
          if (seenUrls.has(cleanUrl)) return;
          seenUrls.add(cleanUrl);
          
          // Find the parent card/container - try multiple strategies
          let parent = link.closest('li') || 
                       link.closest('.reusable-search__result-container') || 
                       link.closest('.entity-result__item') || 
                       link.closest('.base-card') ||
                       link.closest('[class*="result"]') ||
                       link.closest('[data-chameleon-result-urn]') ||
                       link.parentElement?.parentElement?.parentElement;
          
          if (parent) {
            // Use URL as key to avoid duplicates
            uniqueCards.set(cleanUrl, parent);
          }
        }
      });
      
      cards = Array.from(uniqueCards.values());
      console.log(`✅ Found ${cards.length} unique profile cards by link detection`);
    }
    
    // Filter to only valid profile cards (have /in/ links and extractable names)
    const validCards = [];
    cards.forEach(card => {
      const profile = extractProfileFromCard(card);
      if (profile && profile.full_name && profile.full_name.length > 1 && profile.linkedin_url) {
        validCards.push(card);
      }
    });
    
    console.log(`✅ Valid profile cards after filtering: ${validCards.length}`);
    return validCards;
  }

  // Data field options for selection
  const DATA_FIELDS = [
    { id: 'name', label: 'Full Name', default: true },
    { id: 'headline', label: 'Headline/Title', default: true },
    { id: 'company', label: 'Company', default: true },
    { id: 'location', label: 'Location', default: false },
    { id: 'linkedin_url', label: 'LinkedIn URL', default: true },
    { id: 'email', label: 'Find Email', default: false },
    { id: 'phone', label: 'Phone Number', default: false },
    { id: 'website', label: 'Website', default: false }
  ];

  // Create field selection UI
  function createFieldSelectionUI() {
    const container = document.createElement('div');
    container.id = 'leadflux-search-panel';
    container.style.display = 'block';
    container.innerHTML = `
      <div class="leadflux-search-header">
        <h3>🔍 LeadFlux Scraper</h3>
        <button class="leadflux-close-btn" id="leadflux-close-panel">×</button>
      </div>
      <div class="leadflux-search-content">
        <div class="leadflux-field-selection">
          <h4>Select Data Fields to Extract:</h4>
          <div class="leadflux-checkboxes" id="leadflux-field-checkboxes"></div>
        </div>
        <div class="leadflux-profile-count">
          <span id="leadflux-profile-count">0</span> profiles found on this page
        </div>
        <div id="leadflux-profile-list" class="leadflux-profile-list" style="display: none;">
          <div class="leadflux-list-header">
            <span>Select profiles to scrape:</span>
            <div class="leadflux-list-actions">
              <button id="leadflux-check-all" class="leadflux-small-btn">All</button>
              <button id="leadflux-uncheck-all" class="leadflux-small-btn">None</button>
            </div>
          </div>
          <div id="leadflux-profiles-container" class="leadflux-profiles-container"></div>
        </div>
        <div class="leadflux-scraping-mode">
          <label class="leadflux-checkbox-label" style="margin-bottom: 8px;">
            <input type="checkbox" id="leadflux-use-playwright" class="leadflux-field-checkbox">
            <span>Use Playwright (Browser Automation) - More reliable for JS-heavy pages</span>
          </label>
        </div>
        <div class="leadflux-actions">
          <button id="leadflux-scrape-btn" class="leadflux-primary-btn">Scrape Selected Profiles</button>
          <div style="display: flex; gap: 8px;">
            <button id="leadflux-select-all-btn" class="leadflux-secondary-btn" style="flex: 1;">Show Profiles</button>
            <button id="leadflux-clear-btn" class="leadflux-secondary-btn" style="flex: 1;">Clear</button>
            <button id="leadflux-refresh-btn" class="leadflux-secondary-btn" style="flex: 1;" title="Refresh profile list">🔄</button>
          </div>
        </div>
        <div id="leadflux-results-container" class="leadflux-results-container" style="display: none;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <h4 style="margin: 0;">📊 Scraped Results:</h4>
            <button id="leadflux-scroll-to-results" class="leadflux-small-btn" style="display: none; padding: 4px 8px; font-size: 11px;">⬇️ Scroll</button>
          </div>
          <div id="leadflux-results-list" class="leadflux-results-list"></div>
          <div class="leadflux-results-actions">
            <button id="leadflux-export-csv" class="leadflux-export-btn">Export to CSV</button>
            <button id="leadflux-save-all" class="leadflux-export-btn">Save All to Leads</button>
            <button id="leadflux-batch-scrape" class="leadflux-export-btn" style="background: #8b5cf6;">Batch Scrape URLs</button>
          </div>
        </div>
        <div id="leadflux-progress" class="leadflux-progress" style="display: none;">
          <div class="leadflux-progress-bar">
            <div class="leadflux-progress-fill" id="leadflux-progress-fill"></div>
          </div>
          <div class="leadflux-progress-text" id="leadflux-progress-text">Scraping...</div>
        </div>
      </div>
    `;
    return container;
  }

  // Initialize field checkboxes
  function initFieldCheckboxes(container) {
    const checkboxesDiv = container.querySelector('#leadflux-field-checkboxes');
    checkboxesDiv.innerHTML = DATA_FIELDS.map(field => `
      <label class="leadflux-checkbox-label">
        <input type="checkbox" 
               data-field="${field.id}" 
               ${field.default ? 'checked' : ''}
               class="leadflux-field-checkbox">
        <span>${field.label}</span>
      </label>
    `).join('');
  }

  // Get selected fields
  function getSelectedFields(container) {
    const checkboxes = container.querySelectorAll('.leadflux-field-checkbox:checked');
    return Array.from(checkboxes).map(cb => cb.dataset.field);
  }

  // Scrape profiles with selected fields
  let scrapedProfiles = [];
  let selectedProfileCards = [];

  async function scrapeProfiles(container, profiles) {
    const selectedFields = getSelectedFields(container);
    if (selectedFields.length === 0) {
      showNotification('Please select at least one field to extract', 'error');
      return;
    }

    // Check if Playwright mode is enabled
    const usePlaywright = container.querySelector('#leadflux-use-playwright')?.checked || false;

    // Filter out invalid profiles (overlay URLs, etc.)
    const validProfiles = profiles.filter(profile => {
      if (!profile.linkedin_url) return false;
      const validUrl = validateProfileUrl(profile.linkedin_url);
      if (!validUrl) {
        console.warn('Filtered out invalid profile URL:', profile.linkedin_url);
        return false;
      }
      // Update profile URL to cleaned version
      profile.linkedin_url = validUrl;
      return true;
    });

    if (validProfiles.length === 0) {
      showNotification('No valid profiles selected. Please ensure profile URLs are correct.', 'error');
      return;
    }

    const progressDiv = container.querySelector('#leadflux-progress');
    const progressFill = container.querySelector('#leadflux-progress-fill');
    const progressText = container.querySelector('#leadflux-progress-text');
    const resultsContainer = container.querySelector('#leadflux-results-container');
    const resultsList = container.querySelector('#leadflux-results-list');
    const scrapeBtn = container.querySelector('#leadflux-scrape-btn');

    // Show progress and hide previous results
    progressDiv.style.display = 'block';
    if (resultsContainer) {
      resultsContainer.style.display = 'none';
    }
    scrapeBtn.disabled = true;
    scrapeBtn.textContent = 'Scraping...';
    scrapedProfiles = [];

    const apiUrl = await getApiUrl();
    let successCount = 0;
    let errorCount = 0;

    // Use Playwright scraping if enabled
    if (usePlaywright) {
      progressText.textContent = `Using Playwright browser automation...`;
      
      // Scrape profiles using Playwright endpoint
      for (let i = 0; i < validProfiles.length; i++) {
        const profile = validProfiles[i];
        const progress = ((i + 1) / validProfiles.length) * 100;
        progressFill.style.width = `${progress}%`;
        progressText.textContent = `Scraping ${i + 1}/${validProfiles.length} with Playwright: ${profile.full_name || profile.linkedin_url}`;

        try {
          const scrapeRequest = {
            linkedin_url: profile.linkedin_url,
            auto_find_email: selectedFields.includes('email'),
            skip_smtp: false,
            headless: true
          };

          const response = await fetch(`${apiUrl}/api/leads/linkedin-scrape`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(scrapeRequest),
          });

          if (response.ok) {
            const result = await response.json();
            if (result.success && result.data) {
              // Map Playwright response to our format
              const mappedProfile = {
                full_name: result.data.full_name || profile.full_name || '',
                first_name: result.data.first_name || profile.first_name || '',
                last_name: result.data.last_name || profile.last_name || '',
                headline: result.data.headline || profile.headline || '',
                title: result.data.headline || profile.headline || '',
                company_name: result.data.company_name || profile.company_name || '',
                location: result.data.location || profile.location || '',
                linkedin_url: result.data.linkedin_url || profile.linkedin_url,
                about: result.data.about || '',
                experience: result.data.experience || [],
                lead_id: result.data.lead_id,
                scraped_fields: selectedFields,
                success: true
              };
              
              // Add email status if available
              if (result.data.email_status) {
                mappedProfile.email_status = result.data.email_status;
              }
              
              scrapedProfiles.push(mappedProfile);
              successCount++;
            } else {
              scrapedProfiles.push({
                ...profile,
                error: result.error || 'Playwright scraping failed',
                success: false
              });
              errorCount++;
            }
          } else {
            const errorText = await response.text();
            scrapedProfiles.push({
              ...profile,
              error: `API error: ${response.status} - ${errorText}`,
              success: false
            });
            errorCount++;
          }
        } catch (error) {
          scrapedProfiles.push({
            ...profile,
            error: error.message,
            success: false
          });
          errorCount++;
        }

        // Delay between requests to avoid rate limiting
        if (i < validProfiles.length - 1) {
          await new Promise(resolve => setTimeout(resolve, 2000));
        }
      }
    } else {
      // Use traditional DOM scraping method
      for (let i = 0; i < validProfiles.length; i++) {
        const profile = validProfiles[i];
        const progress = ((i + 1) / validProfiles.length) * 100;
        progressFill.style.width = `${progress}%`;
        progressText.textContent = `Scraping ${i + 1}/${validProfiles.length}: ${profile.full_name}`;

        try {
          const profileData = {
            full_name: profile.full_name,
            first_name: profile.first_name,
            last_name: profile.last_name,
            headline: profile.headline,
            title: profile.headline,
            company_name: profile.company_name,
            linkedin_url: profile.linkedin_url,
            company_domain: profile.company_name ? companyToDomain(profile.company_name) : null,
            auto_find_email: selectedFields.includes('email'),
            skip_smtp: false
          };

          // Call LinkedIn capture API
          const response = await fetch(`${apiUrl}/api/leads/linkedin-capture`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(profileData),
          });

          if (response.ok) {
            const result = await response.json();
            scrapedProfiles.push({
              ...profile,
              ...result,
              scraped_fields: selectedFields,
              success: true
            });
            successCount++;
          } else {
            scrapedProfiles.push({
              ...profile,
              error: `API error: ${response.status}`,
              success: false
            });
            errorCount++;
          }
        } catch (error) {
          scrapedProfiles.push({
            ...profile,
            error: error.message,
            success: false
          });
          errorCount++;
        }

        // Small delay to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }

    // Hide progress, show results
    progressDiv.style.display = 'none';
    scrapeBtn.disabled = false;
    scrapeBtn.textContent = 'Scrape Selected Profiles';

    // Display results FIRST
    displayResults(resultsList, scrapedProfiles, selectedFields);
    
    // Make sure results container is visible and scrollable - FORCE IT
    resultsContainer.style.display = 'block';
    resultsContainer.style.visibility = 'visible';
    resultsContainer.style.opacity = '1';
    resultsContainer.style.height = 'auto';
    resultsContainer.style.minHeight = '200px';
    
    // Show scroll to results button
    const scrollBtn = container.querySelector('#leadflux-scroll-to-results');
    if (scrollBtn) {
      scrollBtn.style.display = 'inline-block';
    }
    
    // Force scroll to results after a short delay
    setTimeout(() => {
      const panel = container.closest('#leadflux-search-panel');
      if (panel && resultsContainer) {
        // Scroll the panel to show results
        resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        // Also ensure panel is scrolled
        const resultsTop = resultsContainer.offsetTop;
        panel.scrollTop = resultsTop - 20; // 20px padding from top
      }
    }, 200);
    
    console.log(`Scraping complete: ${successCount} success, ${errorCount} errors`);
    console.log('Results container display:', resultsContainer.style.display);
    console.log('Results container visible:', resultsContainer.offsetHeight > 0);
    
    showNotification(`✅ Scraped ${successCount} profiles successfully, ${errorCount} errors. Scroll down to see results.`, 
                     successCount > 0 ? 'success' : 'error');
  }

  // Display scraped results
  function displayResults(container, profiles, fields) {
    console.log('Displaying results:', profiles.length, 'profiles');
    
    if (!container) {
      console.error('Results container not found!');
      return;
    }
    
    if (profiles.length === 0) {
      container.innerHTML = '<div class="leadflux-no-results">No results to display</div>';
      return;
    }

    const resultsHtml = profiles.map((profile, index) => {
      const statusIcon = profile.success ? '✅' : '❌';
      const statusClass = profile.success ? 'success' : 'error';
      
      let fieldsHtml = '';
      fields.forEach(field => {
        let value = '';
        if (field === 'name') value = profile.full_name || '';
        else if (field === 'headline') value = profile.headline || '';
        else if (field === 'company') value = profile.company_name || '';
        else if (field === 'location') value = profile.location || '';
        else if (field === 'linkedin_url') value = profile.linkedin_url || '';
        else if (field === 'email') {
          if (profile.email_status && profile.email_status.email) {
            value = `${profile.email_status.email} (${profile.email_status.status || 'unknown'})`;
          } else {
            value = 'Not found';
          }
        }
        
        if (value) {
          fieldsHtml += `
            <div class="leadflux-result-field">
              <strong>${DATA_FIELDS.find(f => f.id === field)?.label || field}:</strong>
              <span>${value}</span>
            </div>
          `;
        }
      });

      return `
        <div class="leadflux-result-item ${statusClass}">
          <div class="leadflux-result-header">
            <span class="leadflux-result-status">${statusIcon}</span>
            <span class="leadflux-result-name">${profile.full_name || 'Unknown'}</span>
            ${profile.error ? `<span class="leadflux-result-error">${profile.error}</span>` : ''}
          </div>
          <div class="leadflux-result-fields">
            ${fieldsHtml}
          </div>
        </div>
      `;
    }).join('');
    
    container.innerHTML = resultsHtml;
    console.log('Results HTML inserted, container height:', container.offsetHeight);
  }

  // Export to CSV
  function exportToCSV(profiles, fields) {
    if (profiles.length === 0) return;

    const headers = fields.map(f => DATA_FIELDS.find(df => df.id === f)?.label || f);
    const rows = profiles
      .filter(p => p.success)
      .map(profile => {
        return fields.map(field => {
          let value = '';
          if (field === 'name') value = profile.full_name || '';
          else if (field === 'headline') value = profile.headline || '';
          else if (field === 'company') value = profile.company_name || '';
          else if (field === 'location') value = profile.location || '';
          else if (field === 'linkedin_url') value = profile.linkedin_url || '';
          else if (field === 'email') {
            value = (profile.email_status && profile.email_status.email) || '';
          }
          // Escape commas and quotes
          return `"${String(value).replace(/"/g, '""')}"`;
        });
      });

    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `leadflux-scraped-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  // Create floating button to open scraper
  function createScraperButton() {
    // Only create on LinkedIn pages
    if (!window.location.hostname.includes('linkedin.com')) {
      console.log('Not on LinkedIn, skipping button creation');
      return;
    }
    
    // Check if button already exists
    if (document.getElementById('leadflux-scraper-btn')) {
      console.log('Scraper button already exists');
      return;
    }
    
    // Show on both search pages and individual profile pages
    const isSearch = isSearchPage();
    const isProfile = isIndividualProfilePage();
    
    console.log('Creating scraper button - isSearch:', isSearch, 'isProfile:', isProfile, 'URL:', window.location.href);
    
    // Always show button on LinkedIn pages (removed restriction)
    // The button will work on any LinkedIn page

    const btn = document.createElement('button');
    btn.id = 'leadflux-scraper-btn';
    btn.innerHTML = '🔍 Scrape Results';
    btn.style.cssText = `
      position: fixed !important;
      bottom: 20px !important;
      right: 20px !important;
      z-index: 999999 !important;
      padding: 12px 20px !important;
      background: #06b6d4 !important;
      color: white !important;
      border: none !important;
      border-radius: 8px !important;
      font-size: 14px !important;
      font-weight: 600 !important;
      cursor: pointer !important;
      box-shadow: 0 4px 12px rgba(6, 182, 212, 0.4) !important;
      transition: all 0.2s !important;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
      display: block !important;
      visibility: visible !important;
      opacity: 1 !important;
    `;
    
    btn.addEventListener('mouseenter', () => {
      btn.style.background = '#0891b2';
      btn.style.transform = 'translateY(-2px)';
      btn.style.boxShadow = '0 6px 16px rgba(6, 182, 212, 0.5)';
    });
    
    btn.addEventListener('mouseleave', () => {
      btn.style.background = '#06b6d4';
      btn.style.transform = 'translateY(0)';
      btn.style.boxShadow = '0 4px 12px rgba(6, 182, 212, 0.4)';
    });
    
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const existingPanel = document.getElementById('leadflux-search-panel');
      if (existingPanel) {
        existingPanel.remove();
        btn.innerHTML = '🔍 Scrape Results';
      } else {
        injectSearchScraper();
        btn.innerHTML = '✕ Close Scraper';
      }
    });
    
    // Wait for body to be ready
    if (document.body) {
      document.body.appendChild(btn);
      console.log('Scraper button created and appended to body');
    } else {
      // Wait for body to load
      const observer = new MutationObserver((mutations, obs) => {
        if (document.body) {
          document.body.appendChild(btn);
          console.log('Scraper button created after body loaded');
          obs.disconnect();
        }
      });
      observer.observe(document.documentElement, { childList: true });
    }
  }

  // Check if we're on an individual profile page (not search)
  function isIndividualProfilePage() {
    return isProfilePage() && !isSearchPage();
  }

  // Helper function to validate and clean LinkedIn profile URL
  function validateProfileUrl(url) {
    if (!url) return null;
    
    // Remove query params
    let cleanUrl = url.split('?')[0];
    
    // Filter out overlay URLs
    if (cleanUrl.includes('/overlay/') || 
        cleanUrl.includes('/recent-activity/') ||
        cleanUrl.includes('/opportunities/') ||
        cleanUrl.includes('/skill-associations-details') ||
        cleanUrl.includes('urn:li:fsd')) {
      // Try to extract base profile URL from overlay URL
      const match = cleanUrl.match(/(https?:\/\/[^\/]+\/in\/[^\/]+)/);
      if (match) {
        return match[1]; // Return base profile URL
      }
      return null; // Invalid overlay URL
    }
    
    // Must match /in/username pattern (allow trailing slash)
    const profileMatch = cleanUrl.match(/(https?:\/\/[^\/]+\/in\/[^\/]+)/);
    if (profileMatch) {
      return profileMatch[1]; // Return base profile URL without trailing slash or extra paths
    }
    
    return null; // Not a valid profile URL
  }
  
  // Helper function to extract base profile URL from any LinkedIn URL
  function extractBaseProfileUrl(url) {
    if (!url) return null;
    
    // Remove query params
    let cleanUrl = url.split('?')[0];
    
    // Extract base profile URL pattern: /in/username
    const match = cleanUrl.match(/(https?:\/\/[^\/]+\/in\/[^\/]+)/);
    if (match) {
      return match[1];
    }
    
    // Try with pathname if full URL doesn't match
    try {
      const urlObj = new URL(cleanUrl);
      const pathMatch = urlObj.pathname.match(/^(\/in\/[^\/]+)/);
      if (pathMatch) {
        return `${urlObj.origin}${pathMatch[1]}`;
      }
    } catch (e) {
      // Invalid URL format
    }
    
    return null;
  }

  // Inject search scraping UI
  function injectSearchScraper() {
    // Allow on both search pages and individual profile pages
    if (!isSearchPage() && !isIndividualProfilePage()) return;
    if (document.getElementById('leadflux-search-panel')) return;

    const panel = createFieldSelectionUI();
    document.body.appendChild(panel);

    initFieldCheckboxes(panel);

    // Function to update profile count and refresh cards (ONLY for search pages)
    function updateProfileCount() {
      // Only search for profiles on search pages, not individual profile pages
      if (isIndividualProfilePage()) {
        return [];
      }
      
      console.log('🔄 Updating profile count...');
      const allCards = getAllProfileCards();
      const profileCount = panel.querySelector('#leadflux-profile-count');
      
      // Extract valid profiles to get accurate count
      const validProfiles = allCards.map(card => extractProfileFromCard(card))
        .filter(p => p && p.full_name && p.linkedin_url && validateProfileUrl(p.linkedin_url));
      
      const count = validProfiles.length;
      profileCount.innerHTML = `<span id="leadflux-profile-count-num">${count}</span> profiles found on this page`;
      
      // Update selected count if any
      const checkedCount = panel.querySelectorAll('.leadflux-profile-checkbox:checked').length;
      if (checkedCount > 0) {
        profileCount.innerHTML += ` <span style="color: #06b6d4;">(${checkedCount} selected)</span>`;
      }
      
      console.log(`✅ Profile count updated: ${count} profiles`);
      return allCards;
    }

    // Function to render profile list with checkboxes
    function renderProfileList(profiles) {
      const listContainer = panel.querySelector('#leadflux-profile-list');
      const profilesContainer = panel.querySelector('#leadflux-profiles-container');
      
      if (profiles.length === 0) {
        listContainer.style.display = 'none';
        return;
      }

      listContainer.style.display = 'block';
      profilesContainer.innerHTML = profiles.map((profile, index) => {
        const isChecked = selectedProfileCards.some(p => p.linkedin_url === profile.linkedin_url);
        return `
          <label class="leadflux-profile-item">
            <input type="checkbox" 
                   class="leadflux-profile-checkbox" 
                   data-index="${index}"
                   ${isChecked ? 'checked' : ''}
                   data-url="${profile.linkedin_url || ''}">
            <div class="leadflux-profile-info">
              <div class="leadflux-profile-name">${profile.full_name || 'Unknown'}</div>
              <div class="leadflux-profile-details">
                ${profile.headline ? `<span>${profile.headline}</span>` : ''}
                ${profile.company_name ? `<span>@ ${profile.company_name}</span>` : ''}
                ${profile.location ? `<span>📍 ${profile.location}</span>` : ''}
              </div>
            </div>
          </label>
        `;
      }).join('');

      // Add event listeners to checkboxes
      profilesContainer.querySelectorAll('.leadflux-profile-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', (e) => {
          const index = parseInt(e.target.dataset.index);
          const profile = profiles[index];
          
          if (e.target.checked) {
            // Add to selection if not already there
            if (!selectedProfileCards.some(p => p.linkedin_url === profile.linkedin_url)) {
              selectedProfileCards.push(profile);
            }
          } else {
            // Remove from selection
            selectedProfileCards = selectedProfileCards.filter(
              p => p.linkedin_url !== profile.linkedin_url
            );
          }
          updateProfileCount();
        });
      });
    }

    // Initial profile count - handle individual profile pages differently
    let allCards = [];
    if (isIndividualProfilePage()) {
      // On individual profile page, extract ONLY the current profile (not all links on page)
      const name = extractName();
      const company = extractCompany();
      const headline = extractHeadline();
      const location = extractLocation();
      
      // Extract base profile URL from current page
      // LinkedIn profile URLs are like: https://www.linkedin.com/in/username/
      // We need to extract just the base /in/username part
      let currentUrl = window.location.href;
      
      // Remove query parameters
      if (currentUrl.includes('?')) {
        currentUrl = currentUrl.split('?')[0];
      }
      
      // Extract base profile URL (handle overlay pages)
      let baseProfileUrl = currentUrl;
      if (currentUrl.includes('/overlay/')) {
        // Extract base URL from overlay URL
        // e.g., /in/username/overlay/about-this-profile/ -> /in/username
        const match = currentUrl.match(/(https?:\/\/[^\/]+\/in\/[^\/]+)/);
        if (match) {
          baseProfileUrl = match[1];
        } else {
          // Try to get from pathname
          const pathMatch = window.location.pathname.match(/^(\/in\/[^\/]+)/);
          if (pathMatch) {
            baseProfileUrl = window.location.origin + pathMatch[1];
          }
        }
      } else {
        // Clean up URL - remove trailing slashes and extra path segments
        // Use pathname directly for more reliable extraction
        const pathMatch = window.location.pathname.match(/^(\/in\/[^\/]+)/);
        if (pathMatch) {
          baseProfileUrl = window.location.origin + pathMatch[1];
        } else {
          // Fallback: try URL object
          try {
            const urlObj = new URL(currentUrl);
            const pathParts = urlObj.pathname.split('/').filter(p => p);
            if (pathParts.length >= 2 && pathParts[0] === 'in') {
              // Valid profile URL: /in/username
              baseProfileUrl = `${urlObj.origin}/in/${pathParts[1]}`;
            }
          } catch (e) {
            // Invalid URL format
          }
        }
      }
      
      // Final validation - must have /in/username pattern
      if (!baseProfileUrl || !baseProfileUrl.match(/\/in\/[^\/]+$/)) {
        const profileCount = panel.querySelector('#leadflux-profile-count');
        profileCount.innerHTML = `<span>0</span> profiles found (not a valid profile URL)`;
        return;
      }
      
      // Create profile - use multiple fallback strategies for name extraction
      let profileName = name;
      
      // Fallback 1: Try page title
      if (!profileName || !profileName.full) {
        const pageTitle = document.title;
        const titleMatch = pageTitle.match(/^([^|]+)/); // Extract name before "|" in title
        if (titleMatch) {
          const titleName = titleMatch[1].trim();
          if (titleName && titleName.length > 2 && titleName.length < 100) {
            const parts = titleName.split(' ').filter(p => p);
            profileName = {
              first: parts[0] || '',
              last: parts.slice(1).join(' ') || '',
              full: titleName
            };
          }
        }
      }
      
      // Fallback 2: Try any h1 on the page
      if (!profileName || !profileName.full) {
        const anyH1 = document.querySelector('h1');
        if (anyH1 && anyH1.textContent.trim()) {
          const h1Text = anyH1.textContent.trim();
          if (h1Text.length > 2 && h1Text.length < 100 && !h1Text.includes('LinkedIn')) {
            const parts = h1Text.split(' ').filter(p => p);
            profileName = {
              first: parts[0] || '',
              last: parts.slice(1).join(' ') || '',
              full: h1Text
            };
          }
        }
      }
      
      // Create profile with extracted data (or minimal data if extraction fails)
      const currentProfile = {
        full_name: (profileName && profileName.full) ? profileName.full : 'Unknown',
        first_name: (profileName && profileName.first) ? profileName.first : '',
        last_name: (profileName && profileName.last) ? profileName.last : '',
        headline: headline || '',
        company_name: company || '',
        location: location || '',
        linkedin_url: baseProfileUrl,
        element: document.body
      };
      
      allCards = [document.body];
      selectedProfileCards = [currentProfile];
      
      const profileCount = panel.querySelector('#leadflux-profile-count');
      if (profileName && profileName.full && profileName.full !== 'Unknown') {
        profileCount.innerHTML = `<span>1</span> profile (current page)`;
      } else {
        profileCount.innerHTML = `<span>1</span> profile (URL detected - name extraction in progress...)`;
        
        // Retry name extraction after delay
        setTimeout(() => {
          const retryName = extractName();
          if (retryName && retryName.full && retryName.full !== 'Unknown') {
            currentProfile.full_name = retryName.full;
            currentProfile.first_name = retryName.first;
            currentProfile.last_name = retryName.last;
            const updatedCount = panel.querySelector('#leadflux-profile-count');
            if (updatedCount) {
              updatedCount.innerHTML = `<span>1</span> profile (current page)`;
            }
            renderProfileList([currentProfile]);
          }
        }, 2000);
      }
      
      // Auto-show profile list for individual pages
      renderProfileList([currentProfile]);
      setTimeout(() => {
        panel.querySelectorAll('.leadflux-profile-checkbox').forEach(cb => cb.checked = true);
      }, 100);
    } else {
      // On search pages, use getAllProfileCards (which filters overlays)
      // Auto-detect profiles when panel opens
      console.log('🔍 Auto-detecting profiles on search page...');
      allCards = updateProfileCount();
      
      // If profiles found, automatically show them after a short delay
      if (allCards.length > 0) {
        setTimeout(() => {
          const validProfiles = allCards.map(card => extractProfileFromCard(card))
            .filter(p => p && p.full_name && p.linkedin_url && validateProfileUrl(p.linkedin_url));
          
          if (validProfiles.length > 0) {
            console.log(`✅ Auto-showing ${validProfiles.length} detected profiles`);
            renderProfileList(validProfiles);
            showNotification(`Found ${validProfiles.length} profiles! Select the ones you want to scrape.`, 'success');
          }
        }, 500); // Small delay to ensure DOM is ready
      }
    }

    // Close button
    panel.querySelector('#leadflux-close-panel').addEventListener('click', () => {
      panel.remove();
      const scraperBtn = document.getElementById('leadflux-scraper-btn');
      if (scraperBtn) {
        scraperBtn.innerHTML = '🔍 Scrape Results';
      }
    });

    // Show profiles button (renamed from Select All)
    panel.querySelector('#leadflux-select-all-btn').addEventListener('click', () => {
      console.log('🔍 Show Profiles button clicked');
      
      // On individual profile pages, don't search - just use current profile
      if (isIndividualProfilePage()) {
        const name = extractName();
        if (name && name.full) {
          let currentUrl = window.location.href;
          if (currentUrl.includes('?')) currentUrl = currentUrl.split('?')[0];
          if (currentUrl.includes('/overlay/')) {
            const match = currentUrl.match(/(https?:\/\/[^\/]+\/in\/[^\/]+)/);
            if (match) currentUrl = match[1];
          }
          
          if (currentUrl.match(/\/in\/[^\/]+$/)) {
            const currentProfile = {
              full_name: name.full,
              first_name: name.first,
              last_name: name.last,
              headline: extractHeadline() || '',
              company_name: extractCompany() || '',
              location: extractLocation() || '',
              linkedin_url: currentUrl
            };
            renderProfileList([currentProfile]);
            showNotification('Current profile loaded', 'success');
          }
        }
        return;
      }
      
      // On search pages, force refresh and get all profiles
      console.log('🔍 Detecting profiles on search page...');
      showNotification('Detecting profiles...', 'info');
      
      // Force a fresh scan
      allCards = getAllProfileCards(); // Use the improved detection function
      console.log(`🔍 Found ${allCards.length} profile cards`);
      
      // Extract profiles from cards
      const profiles = [];
      allCards.forEach((card, index) => {
        const profile = extractProfileFromCard(card);
        if (profile && profile.full_name && profile.linkedin_url) {
          const validUrl = validateProfileUrl(profile.linkedin_url);
          if (validUrl) {
            profile.linkedin_url = validUrl;
            profiles.push(profile);
            console.log(`✅ Profile ${index + 1}: ${profile.full_name} - ${profile.linkedin_url}`);
          } else {
            console.warn(`⚠️ Invalid URL for ${profile.full_name}: ${profile.linkedin_url}`);
          }
        }
      });
      
      console.log(`✅ Total valid profiles: ${profiles.length}`);
      
      // Update profile count
      const profileCount = panel.querySelector('#leadflux-profile-count');
      if (profileCount) {
        profileCount.innerHTML = `<span id="leadflux-profile-count-num">${profiles.length}</span> profiles found on this page`;
      }
      
      if (profiles.length === 0) {
        showNotification('No profiles found. Try: 1) Scroll down to load more results, 2) Click Refresh button, 3) Make sure you are on a LinkedIn search results page.', 'error');
        return;
      }
      
      // Render the profile list
      renderProfileList(profiles);
      showNotification(`✅ Found ${profiles.length} profiles! Select the ones you want to scrape.`, 'success');
    });

    // Clear selection button
    panel.querySelector('#leadflux-clear-btn').addEventListener('click', () => {
      selectedProfileCards = [];
      // Uncheck all checkboxes
      panel.querySelectorAll('.leadflux-profile-checkbox').forEach(cb => cb.checked = false);
      updateProfileCount(); // Update count display
      showNotification('Selection cleared', 'info');
    });

    // Check all button
    panel.querySelector('#leadflux-check-all').addEventListener('click', () => {
      panel.querySelectorAll('.leadflux-profile-checkbox').forEach(cb => {
        cb.checked = true;
        const index = parseInt(cb.dataset.index);
        const profiles = allCards.map(card => extractProfileFromCard(card)).filter(p => p && p.full_name);
        if (profiles[index] && !selectedProfileCards.some(p => p.linkedin_url === profiles[index].linkedin_url)) {
          selectedProfileCards.push(profiles[index]);
        }
      });
      updateProfileCount();
    });

    // Uncheck all button
    panel.querySelector('#leadflux-uncheck-all').addEventListener('click', () => {
      panel.querySelectorAll('.leadflux-profile-checkbox').forEach(cb => cb.checked = false);
      selectedProfileCards = [];
      updateProfileCount();
    });

    // Refresh button
    panel.querySelector('#leadflux-refresh-btn').addEventListener('click', () => {
      allCards = getAllProfileCards(); // Force refresh
      updateProfileCount();
      showNotification(`Found ${allCards.length} profiles`, allCards.length > 0 ? 'success' : 'info');
    });

    // Scrape button
    const scrapeBtn = panel.querySelector('#leadflux-scrape-btn');
    if (!scrapeBtn) {
      console.error('Scrape button not found!');
      return;
    }
    
    scrapeBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      console.log('Scrape button clicked');
      
      try {
        // Get all available profiles first
        let profiles = [];
        if (isIndividualProfilePage()) {
          // On individual page, use the current profile
          const name = extractName();
          const headline = extractHeadline();
          const company = extractCompany();
          const location = extractLocation();
          
          if (name && name.full) {
            let currentUrl = window.location.href;
            if (currentUrl.includes('?')) currentUrl = currentUrl.split('?')[0];
            if (currentUrl.includes('/overlay/')) {
              const match = currentUrl.match(/(https?:\/\/[^\/]+\/in\/[^\/]+)/);
              if (match) currentUrl = match[1];
            }
            const validUrl = validateProfileUrl(currentUrl);
            if (validUrl) {
              profiles = [{
                full_name: name.full,
                first_name: name.first,
                last_name: name.last,
                headline: headline || '',
                company_name: company || '',
                location: location || '',
                linkedin_url: validUrl
              }];
              console.log('Individual profile extracted:', profiles[0]);
            }
          }
        } else {
          // On search pages, get all cards and extract profiles
          allCards = getAllProfileCards();
          console.log(`Found ${allCards.length} profile cards on search page`);
          profiles = allCards.map(card => extractProfileFromCard(card))
            .filter(p => p && p.full_name && p.linkedin_url)
            .map(p => {
              const validUrl = validateProfileUrl(p.linkedin_url);
              if (validUrl) {
                p.linkedin_url = validUrl;
                return p;
              }
              return null;
            })
            .filter(p => p !== null);
        }
        
        console.log(`Found ${profiles.length} total profiles`);
        
        // Get selected profiles from checkboxes
        const checkedBoxes = panel.querySelectorAll('.leadflux-profile-checkbox:checked');
        console.log(`Found ${checkedBoxes.length} checked boxes`);
        
        // Determine which profiles to scrape
        if (checkedBoxes.length > 0) {
          // Use checked profiles
          selectedProfileCards = Array.from(checkedBoxes).map(cb => {
            const index = parseInt(cb.dataset.index);
            if (index >= 0 && index < profiles.length) {
              return profiles[index];
            }
            return null;
          }).filter(p => p !== null && p.linkedin_url);
        } else {
          // No checkboxes checked - use all profiles
          selectedProfileCards = profiles;
        }
        
        console.log(`Selected ${selectedProfileCards.length} profiles for scraping:`, selectedProfileCards);
        
        if (selectedProfileCards.length === 0) {
          showNotification('No profiles found. Make sure you are on a LinkedIn profile or search page.', 'error');
          return;
        }
        
        // Show notification and start scraping
        showNotification(`Starting to scrape ${selectedProfileCards.length} profile(s)...`, 'info');
        await scrapeProfiles(panel, selectedProfileCards);
        
      } catch (error) {
        console.error('Error in scrape button handler:', error);
        console.error('Error stack:', error.stack);
        showNotification(`Error: ${error.message}`, 'error');
      }
    });

    // Scroll to results button
    const scrollToResultsBtn = panel.querySelector('#leadflux-scroll-to-results');
    if (scrollToResultsBtn) {
      scrollToResultsBtn.addEventListener('click', () => {
        const resultsContainer = panel.querySelector('#leadflux-results-container');
        if (resultsContainer) {
          resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
          scrollToResultsBtn.style.display = 'none';
        }
      });
    }

    // Export CSV button
    panel.querySelector('#leadflux-export-csv').addEventListener('click', () => {
      const fields = getSelectedFields(panel);
      exportToCSV(scrapedProfiles, fields);
      showNotification('CSV exported successfully', 'success');
    });

    // Save all button
    panel.querySelector('#leadflux-save-all').addEventListener('click', async () => {
      const successProfiles = scrapedProfiles.filter(p => p.success);
      if (successProfiles.length === 0) {
        showNotification('No successful scrapes to save', 'error');
        return;
      }
      showNotification(`${successProfiles.length} profiles already saved to leads`, 'success');
    });

    // Batch scrape button - opens profiles in new tabs for manual scraping or queues them
    panel.querySelector('#leadflux-batch-scrape').addEventListener('click', async () => {
      const checkedBoxes = panel.querySelectorAll('.leadflux-profile-checkbox:checked');
      if (checkedBoxes.length === 0) {
        showNotification('Please select profiles first', 'error');
        return;
      }

      const profiles = allCards.map(card => extractProfileFromCard(card)).filter(p => p && p.full_name);
      const selectedProfiles = Array.from(checkedBoxes).map(cb => {
        const index = parseInt(cb.dataset.index);
        return profiles[index];
      }).filter(p => p && p.linkedin_url);

      if (selectedProfiles.length === 0) {
        showNotification('No valid profiles found', 'error');
        return;
      }

      // Ask user how they want to batch scrape
      const method = confirm(
        `You selected ${selectedProfiles.length} profiles.\n\n` +
        `OK = Open profiles in new tabs (you can scrape each one)\n` +
        `Cancel = Queue for background scraping (requires backend support)`
      );

      if (method) {
        // Open profiles in new tabs (limited to 10 at a time to avoid overwhelming browser)
        const urlsToOpen = selectedProfiles.slice(0, 10).map(p => p.linkedin_url);
        urlsToOpen.forEach((url, index) => {
          setTimeout(() => {
            window.open(url, '_blank');
          }, index * 500); // Stagger opens
        });
        showNotification(`Opening ${urlsToOpen.length} profiles in new tabs...`, 'success');
      } else {
        // Queue for background scraping (use existing scrape function but in background)
        const batchBtn = panel.querySelector('#leadflux-batch-scrape');
        batchBtn.disabled = true;
        batchBtn.textContent = 'Queuing...';

        // Use the existing scrapeProfiles function but show it's a batch operation
        showNotification(`Queuing ${selectedProfiles.length} profiles for scraping...`, 'info');
        await scrapeProfiles(panel, selectedProfiles);
        
        batchBtn.disabled = false;
        batchBtn.textContent = 'Batch Scrape URLs';
      }
    });
  }

  // Re-run when navigating (LinkedIn uses SPA)
  let lastUrl = location.href;
  new MutationObserver(() => {
    const url = location.href;
    if (url !== lastUrl) {
      lastUrl = url;
      console.log('LinkedIn page changed to:', url);
      setTimeout(() => {
        injectEmailFinder();
        createScraperButton();
        injectSearchScraper();
      }, 1000); // Wait for page to load
    }
  }).observe(document, { subtree: true, childList: true });
  
  // Expose function to window for manual triggering (for debugging)
  window.leadfluxShowButton = function() {
    console.log('Manually creating LeadFlux button...');
    const existing = document.getElementById('leadflux-scraper-btn');
    if (existing) {
      existing.remove();
    }
    createScraperButton();
  };

  // Initial injection
  function initializeExtension() {
    console.log('Initializing LeadFlux extension on:', window.location.href);
    injectEmailFinder();
    createScraperButton();
    injectSearchScraper();
  }
  
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      setTimeout(initializeExtension, 500); // Wait a bit for LinkedIn to load
    });
  } else {
    // Page already loaded, but wait a bit for LinkedIn's JS to initialize
    setTimeout(initializeExtension, 1000);
  }
  
  // Also try after a longer delay in case LinkedIn loads slowly
  setTimeout(() => {
    if (!document.getElementById('leadflux-scraper-btn')) {
      console.log('Button not found after delay, retrying...');
      createScraperButton();
    }
  }, 3000);

})();



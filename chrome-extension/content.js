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

  // Get current API URL (with fallback)
  async function getApiUrl() {
    return new Promise((resolve) => {
      chrome.storage.sync.get(['apiUrl'], (result) => {
        resolve(result.apiUrl || 'http://localhost:8002');
      });
    });
  }
  
  // Check if we're on a LinkedIn profile page
  function isProfilePage() {
    return window.location.pathname.match(/^\/in\/[^\/]+/);
  }

  // Extract name from LinkedIn profile
  function extractName() {
    const nameElement = document.querySelector('h1.text-heading-xlarge, .pv-text-details__left-panel h1');
    if (!nameElement) return null;
    
    const fullName = nameElement.textContent.trim();
    const parts = fullName.split(' ');
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

  // Save LinkedIn profile to leads (new unified endpoint)
  async function saveLinkedInProfile(autoFindEmail = true, skipSmtp = false, showWidget = true) {
    // Check if API key is configured
    const storage = await new Promise((resolve) => {
      chrome.storage.sync.get(['apiUrl'], resolve);
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
          chrome.storage.sync.get(['frontendUrl', 'apiUrl'], resolve);
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
    chrome.storage.sync.get(['showInlineButton'], (result) => {
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

  // Re-run when navigating (LinkedIn uses SPA)
  let lastUrl = location.href;
  new MutationObserver(() => {
    const url = location.href;
    if (url !== lastUrl) {
      lastUrl = url;
      setTimeout(injectEmailFinder, 1000); // Wait for page to load
    }
  }).observe(document, { subtree: true, childList: true });

})();


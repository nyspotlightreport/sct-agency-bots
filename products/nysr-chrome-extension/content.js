// NYSR AI Companion — Content Script
// Runs on all pages to enable context menu and keyboard shortcuts
(function() {
  'use strict';
  
  // Listen for messages from popup
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'getPageContent') {
      sendResponse({
        content: document.body.innerText.slice(0, 5000),
        title: document.title,
        url: window.location.href
      });
    }
    return true;
  });
})();

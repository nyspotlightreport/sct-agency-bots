// NYSR AI Companion — Service Worker
chrome.runtime.onInstalled.addListener(() => {
  console.log('NYSR AI Companion installed');
  
  chrome.contextMenus.create({
    id: 'nysr-compose',
    title: 'NYSR: Generate content from selection',
    contexts: ['selection']
  });
  
  chrome.contextMenus.create({
    id: 'nysr-summarize',
    title: 'NYSR: Summarize this page',
    contexts: ['page']
  });
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === 'nysr-compose' && info.selectionText) {
    await chrome.storage.local.set({ pendingAction: { type: 'compose', text: info.selectionText } });
    chrome.action.openPopup();
  }
  if (info.menuItemId === 'nysr-summarize') {
    await chrome.storage.local.set({ pendingAction: { type: 'summarize', tabId: tab.id } });
    chrome.action.openPopup();
  }
});

chrome.commands.onCommand.addListener(async (command) => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (command === 'summarize-page') {
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/icon48.png',
      title: 'NYSR AI',
      message: 'Summarizing page...'
    });
  }
});

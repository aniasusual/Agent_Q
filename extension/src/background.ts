// Background Service Worker
console.log('Agent Q Background Service Worker started');

// Handle extension icon click - open side panel
chrome.action.onClicked.addListener((tab) => {
  if (tab.windowId) {
    chrome.sidePanel.open({ windowId: tab.windowId });
  }
});

// Handle installation
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    console.log('Agent Q installed successfully');

    // Set default side panel behavior
    chrome.sidePanel
      .setPanelBehavior({ openPanelOnActionClick: true })
      .catch((error) => console.error(error));
  } else if (details.reason === 'update') {
    console.log('Agent Q updated to version:', chrome.runtime.getManifest().version);
  }
});

// Listen for messages from content scripts or side panel
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  console.log('Background received message:', message);

  // Handle different message types
  switch (message.type) {
    case 'GET_ACTIVE_TAB':
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        sendResponse({ tab: tabs[0] });
      });
      return true; // Keep channel open for async response

    case 'CAPTURE_SCREENSHOT':
      chrome.tabs.captureVisibleTab({ format: 'png' }, (dataUrl) => {
        sendResponse({ screenshot: dataUrl });
      });
      return true;

    case 'SEND_TO_BACKEND':
      // This will be implemented in Milestone 2
      console.log('Will send to backend:', message.data);
      sendResponse({ status: 'queued' });
      break;

    case 'CONTENT_SCRIPT_READY':
      console.log('Content script ready on:', message.url);
      sendResponse({ received: true });
      break;

    default:
      console.log('Unknown message type:', message.type);
  }

  return false;
});

// Keep service worker alive
chrome.runtime.onConnect.addListener((port) => {
  console.log('Port connected:', port.name);
});
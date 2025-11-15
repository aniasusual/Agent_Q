// Content Script - Injected into web pages
console.log('Agent Q Content Script loaded');

// This script will be enhanced in Milestone 3 for DOM capture
// and in Milestone 5 for live preview execution

// Listen for messages from side panel or background
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  console.log('Content script received message:', message);

  switch (message.type) {
    case 'CAPTURE_DOM':
      // Will be implemented in Milestone 3
      sendResponse({
        html: document.documentElement.outerHTML.substring(0, 5000),
        url: window.location.href,
        title: document.title,
      });
      break;

    case 'HIGHLIGHT_ELEMENT':
      // Will be implemented in Milestone 5
      console.log('Highlight element:', message.selector);
      sendResponse({ success: true });
      break;

    case 'EXECUTE_ACTION':
      // Will be implemented in Milestone 5
      console.log('Execute action:', message.action);
      sendResponse({ success: true });
      break;

    case 'PING':
      sendResponse({ status: 'alive' });
      break;

    default:
      console.log('Unknown message type:', message.type);
  }

  return true; // Keep channel open for async response
});

// Signal that content script is ready
chrome.runtime.sendMessage({
  type: 'CONTENT_SCRIPT_READY',
  url: window.location.href,
});
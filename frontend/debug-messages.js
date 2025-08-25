/**
 * Debug utility for ChatMessage component styling
 * Run this in browser console to inspect message layout issues
 */

function debugMessageLayout() {
  console.log('=== Chat Message Debug Utility ===');
  
  // Find all message elements
  const messages = document.querySelectorAll('.chat-message');
  const bubbles = document.querySelectorAll('.message-bubble');
  const contents = document.querySelectorAll('.message-content');
  
  console.log(`Found ${messages.length} messages, ${bubbles.length} bubbles, ${contents.length} contents`);
  
  // Add debug borders
  messages.forEach((msg, index) => {
    msg.style.border = '1px dashed red';
    msg.style.position = 'relative';
    
    // Add index label
    const label = document.createElement('div');
    label.textContent = `Msg ${index}`;
    label.style.cssText = `
      position: absolute;
      top: -15px;
      left: 0;
      font-size: 10px;
      background: red;
      color: white;
      padding: 2px 4px;
      z-index: 1000;
    `;
    msg.appendChild(label);
  });
  
  bubbles.forEach((bubble, index) => {
    bubble.style.border = '1px dashed blue';
    
    // Add bubble label
    const label = document.createElement('div');
    label.textContent = `Bubble ${index}`;
    label.style.cssText = `
      position: absolute;
      top: -15px;
      right: 0;
      font-size: 10px;
      background: blue;
      color: white;
      padding: 2px 4px;
      z-index: 1001;
    `;
    bubble.appendChild(label);
  });
  
  contents.forEach((content, index) => {
    content.style.border = '1px dashed green';
    
    // Log content properties
    const computedStyle = window.getComputedStyle(content);
    console.log(`Content ${index}:`, {
      background: computedStyle.background,
      backgroundColor: computedStyle.backgroundColor,
      color: computedStyle.color,
      padding: computedStyle.padding,
      margin: computedStyle.margin,
      width: computedStyle.width,
      height: computedStyle.height,
      display: computedStyle.display,
      position: computedStyle.position
    });
  });
  
  // Check for conflicting styles
  checkForConflicts();
  
  console.log('Debug borders added. Run clearDebugBorders() to remove them.');
}

function clearDebugBorders() {
  // Remove debug borders
  document.querySelectorAll('.chat-message').forEach(msg => {
    msg.style.border = '';
    const label = msg.querySelector('div[style*="position: absolute"]');
    if (label) label.remove();
  });
  
  document.querySelectorAll('.message-bubble').forEach(bubble => {
    bubble.style.border = '';
    const label = bubble.querySelector('div[style*="position: absolute"]');
    if (label) label.remove();
  });
  
  document.querySelectorAll('.message-content').forEach(content => {
    content.style.border = '';
  });
  
  console.log('Debug borders cleared.');
}

function checkForConflicts() {
  console.log('=== Checking for style conflicts ===');
  
  // Check if any global CSS is affecting message components
  const globalStyles = [];
  const allStyleSheets = Array.from(document.styleSheets);
  
  allStyleSheets.forEach(sheet => {
    try {
      const rules = Array.from(sheet.cssRules || sheet.rules || []);
      rules.forEach(rule => {
        if (rule.selectorText && (
          rule.selectorText.includes('.message') ||
          rule.selectorText.includes('.chat') ||
          rule.selectorText.includes('*')
        )) {
          globalStyles.push({
            selector: rule.selectorText,
            style: rule.cssText,
            sheet: sheet.href || 'inline'
          });
        }
      });
    } catch (e) {
      console.warn('Could not access stylesheet:', sheet.href);
    }
  });
  
  console.log('Potentially conflicting styles:', globalStyles);
}

function inspectMessageStructure() {
  console.log('=== Message Structure Inspection ===');
  
  const messages = document.querySelectorAll('.chat-message');
  messages.forEach((msg, index) => {
    console.log(`Message ${index}:`);
    console.log('  Classes:', msg.className);
    console.log('  Children:', msg.children.length);
    console.log('  HTML:', msg.outerHTML.substring(0, 200) + '...');
    
    const bubble = msg.querySelector('.message-bubble');
    if (bubble) {
      console.log('  Bubble classes:', bubble.className);
      console.log('  Bubble computed background:', window.getComputedStyle(bubble).background);
      
      const content = bubble.querySelector('.message-content');
      if (content) {
        console.log('  Content classes:', content.className);
        console.log('  Content computed background:', window.getComputedStyle(content).background);
        console.log('  Content text preview:', content.textContent.substring(0, 100) + '...');
      }
    }
    console.log('---');
  });
}

// Export functions to global scope for console access
window.debugMessageLayout = debugMessageLayout;
window.clearDebugBorders = clearDebugBorders;
window.checkForConflicts = checkForConflicts;
window.inspectMessageStructure = inspectMessageStructure;

console.log('Chat Message Debug Utility loaded. Available functions:');
console.log('- debugMessageLayout(): Add visual debug borders');
console.log('- clearDebugBorders(): Remove debug borders');
console.log('- checkForConflicts(): Check for conflicting CSS');
console.log('- inspectMessageStructure(): Log message DOM structure');

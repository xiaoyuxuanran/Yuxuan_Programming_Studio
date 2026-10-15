/* Local desktop branding. GWT injects its theme after page load. */
(() => {
  'use strict';
  const colors = {'#8fc202':'#38bdf8','#a5cf47':'#7dd3fc','#a4cf47':'#7dd3fc',
    '#d2e0a6':'#bae6fd','#eef2e0':'#f0f9ff','#b3c833':'#7dd3fc','#6b9900':'#0284c7',
    '#6c8c24':'#0369a1','#62704a':'#33576b','#838e6f':'#648496','#727f5c':'#507084',
    '#ccddb3':'#bae6fd','#7d9d36':'#0284c7','#f7f9f2':'#f0f9ff','#f3f8e6':'#f0f9ff',
    '#3a4b1e':'#12344a','#f9faf5':'#f8fcff','#4f4f2c':'#34566a'};
  const recolor = text => text.replace(/#[0-9a-f]{6}\b/gi, c => colors[c.toLowerCase()] || c);
  const faceSelector = '.ode-TopPanelButton .html-face';
  const menuSelector = '.ode-ContextMenuItem[role="menuitem"]';
  const selector = 'style, .ode-Logo, '+faceSelector+', '+menuSelector;
  const styledText = new WeakMap();
  const pending = new Set();
  let scheduled=false;
  function update(element) {
    if(!element.isConnected)return;
    if(element.tagName==='STYLE') {
      const before=element.textContent;
      if(styledText.get(element)===before)return;
      const after=recolor(before);
      styledText.set(element,after);
      if(before!==after)element.textContent=after;
      return;
    }
    if(element.matches('.ode-Logo')) {
      if(element.tagName==='IMG' && !element.src.endsWith('/static/images/brand-logo.png'))element.src='/static/images/brand-logo.png';
      if(element.getAttribute('alt')!=='羽轩 Logo')element.setAttribute('alt','羽轩 Logo');
      return;
    }
    if(element.matches(menuSelector)) {
      const label=element.textContent.trim();
      if(label==='注销')element.textContent='更改用户名';
      else if(label==='Sign out')element.textContent='Change username';
      else if(label==='删除账号' || label==='Delete Account') {
        const row=element.closest('tr');
        if(row){row.hidden=true;row.style.display='none';}
      }
      return;
    }
    // The server metadata also covers an existing session created before the
    // passwordless entrance existed. Use the cookie only with an older page.
    const meta=document.querySelector('meta[name="offline-display-name"]');
    const cookie=document.cookie.split('; ').find(c=>c.startsWith('OfflineDisplayName='));
    const value=meta ? meta.content : (cookie ? cookie.split('=')[1] : '');
    const displayName=/^[A-Za-z0-9]{1,32}$/.test(value) ? value : '本地工作区';
    for(const child of element.childNodes)if(child.nodeType===Node.TEXT_NODE && child.textContent.includes('@offline.local')) {
      child.textContent=' '+displayName+' ▾';
      const icon=element.querySelector('.material-icons');if(icon)icon.textContent='person';
    }
  }
  function collectTree(node) {
    if(node.nodeType!==Node.ELEMENT_NODE)return;
    if(node.matches(selector))pending.add(node);
    node.querySelectorAll(selector).forEach(element=>pending.add(element));
  }
  function flush() {
    scheduled=false;
    const elements=Array.from(pending); pending.clear();
    elements.forEach(update);
  }
  function schedule() {
    if(!pending.size || scheduled)return;
    scheduled=true; requestAnimationFrame(flush);
  }
  new MutationObserver(records => {
    // Inspect only added subtrees and changed branding nodes. Blockly dragging must
    // not rescan or rewrite every GWT stylesheet on the page.
    for(const record of records) {
      const target=record.target.nodeType===Node.ELEMENT_NODE ? record.target : record.target.parentElement;
      if(target) {
        const relevant=target.closest('style, '+faceSelector+', '+menuSelector);
        if(relevant)pending.add(relevant);
      }
      if(record.type==='childList')record.addedNodes.forEach(collectTree);
    }
    schedule();
  }).observe(document.documentElement,{subtree:true,childList:true,characterData:true});
  function initialize() { collectTree(document.documentElement); schedule(); }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initialize,{once:true});
  else initialize();
})();

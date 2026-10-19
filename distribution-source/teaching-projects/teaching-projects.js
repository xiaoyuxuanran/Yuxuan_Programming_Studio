/* Bundled curriculum library. The native project manager owns all editable copies. */
(() => {
  'use strict';
  let catalogPromise;
  const states = new WeakMap();
  const folderIcon = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 5.5h6l2 2h10v12H3z" fill="#dceffc" stroke="#1685bf" stroke-width="1.5" stroke-linejoin="round"/><path d="M3 9h18" stroke="#1685bf" stroke-width="1.5"/></svg>';
  const icon = () => {const el=document.createElement('span');el.className='yx-folder-icon';el.innerHTML=folderIcon;return el;};
  function element(tag,cls,text) {const el=document.createElement(tag);if(cls)el.className=cls;if(text!==undefined)el.textContent=text;return el;}
  function button(cls,text,action) {const el=element('button',cls,text);el.type='button';if(action)el.addEventListener('click',action);return el;}
  function getCatalog() {
    if(!catalogPromise) catalogPromise=fetch('static/teaching/catalog.json?v=teaching1',{credentials:'same-origin',cache:'no-cache'})
      .then(r=>{if(!r.ok)throw Error('课程目录加载失败，请稍后重试。');return r.json();})
      .then(c=>{if(c.schemaVersion!==1||c.stages.length!==8)throw Error('课程目录版本不匹配。');return c;})
      .catch(e=>{catalogPromise=null;throw e;});
    return catalogPromise;
  }
  function save(state) {try{sessionStorage.setItem('yuxuan-teaching-view-v1',JSON.stringify({active:state.active,stage:state.stage,lesson:state.lesson}));}catch(_) {}}
  function resize(state) {
    if(!state.active || state.panel.hidden || !state.panel.getClientRects().length)return;
    const top=state.panel.getBoundingClientRect().top;
    state.panel.style.height=Math.max(360,window.innerHeight-top-26)+'px';
  }
  function nativeView(state) {
    const trash=state.box.getAttribute('data-yuxuan-project-box')==='trash';
    state.tabs.hidden=trash;
    const active=state.active&&!trash;
    state.personal.hidden=active;
    state.panel.hidden=!active;
    state.box.classList.toggle('yx-is-teaching',active);
    state.tabs.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String((b.dataset.view==='teaching')===active)));
    if(window.YuxuanTeaching && state.nativeActive!==active) {
      window.YuxuanTeaching.setTeachingView(active);state.nativeActive=active;
    }
    if(active)requestAnimationFrame(()=>resize(state));
  }
  function choose(state,stage,lesson) {state.stage=stage;state.lesson=lesson;save(state);render(state);}
  function folderRow(state,name,description,onClick,attrs={}) {
    const row=button('yx-folder-row','',onClick);row.append(icon());
    const body=element('span','yx-folder-body');body.append(element('span','yx-folder-name',name),element('span','yx-folder-detail',description));
    row.append(body,element('span','yx-folder-arrow','›'));
    for(const [key,value] of Object.entries(attrs))row.setAttribute(key,String(value));
    return row;
  }
  function renderRoute(state,stage) {
    const route=state.route;route.replaceChildren();
    const heading=element('div','yx-route-heading');heading.append(element('p','yx-eyebrow','从创意到作品'),element('h2','','课程学习路线'));
    const stats=element('p','yx-route-stats','8 个阶段 · 56 节课 · 每节 90 分钟');heading.append(stats);route.append(heading);
    const list=element('ol','yx-route-list');list.setAttribute('aria-label','八阶段教学大纲');
    state.catalog.stages.forEach((s,i)=>{
      const li=element('li','yx-route-step');li.classList.toggle('is-current',stage?.id===s.id);
      const node=button('yx-route-node','',()=>choose(state,s.id,null));node.setAttribute('data-route-stage',s.id);
      if(stage?.id===s.id)node.setAttribute('aria-current','step');
      const order=element('span','yx-route-number',String(i+1).padStart(2,'0'));
      const content=element('span','yx-route-text');content.append(element('span','yx-route-title',s.title),element('span','yx-route-detail',`第 ${s.start}–${s.end} 课 · ${s.focus}`));
      node.append(order,content);li.append(node);list.append(li);
    });
    route.append(list,element('p','yx-route-footer','点击任一阶段，即可查看对应课次文件夹。'));
  }
  function render(state) {
    if(!state.catalog)return;
    const c=state.catalog,stage=c.stages.find(s=>s.id===state.stage),lesson=stage?.lessons.find(l=>l.id===state.lesson);
    state.panel.classList.toggle('is-lesson',!!lesson);
    if(!stage){state.stage=null;state.lesson=null;}else if(!lesson)state.lesson=null;
    const left=state.left;left.replaceChildren();
    const trail=element('nav','yx-teaching-breadcrumb');trail.setAttribute('aria-label','教学项目路径');
    trail.append(button('yx-crumb','教学项目',()=>choose(state,null,null)));
    if(stage){trail.append(element('span','','/'),button('yx-crumb',`第${Number(stage.id)}阶段`,()=>choose(state,stage.id,null)));}
    if(lesson)trail.append(element('span','','/'),element('span','yx-crumb-current','No.'+lesson.id));
    left.append(trail);
    const header=element('div','yx-library-heading');
    header.append(element('h1','',lesson?lesson.name:(stage?stage.name:'教学项目')));
    header.append(element('p','',lesson?lesson.summary:(stage?`第 ${stage.start}–${stage.end} 课 · ${stage.focus}`:'按阶段探索 App Inventor，逐步完成自己的创意作品。')));
    left.append(header);
    const content=element('div','yx-library-items');content.setAttribute('data-teaching-folders','true');
    if(!stage) {
      c.stages.forEach(s=>content.append(folderRow(state,s.name,`第 ${s.start}–${s.end} 课 · ${s.lessons.length} 个课次文件夹`,()=>choose(state,s.id,null),{'data-stage-folder':s.id})));
    } else if(!lesson) {
      content.append(button('yx-back-link','‹ 返回全部阶段',()=>choose(state,null,null)));
      stage.lessons.forEach(l=>content.append(folderRow(state,l.name,l.projects.length?`${l.projects.length} 个教学项目 · 已准备`:'空文件夹 · 待添加教学项目',()=>choose(state,stage.id,l.id),{'data-lesson-folder':l.id})));
    } else {
      content.append(button('yx-back-link','‹ 返回本阶段课次',()=>choose(state,stage.id,null)));
      if(!lesson.projects.length) {
        const empty=element('div','yx-teaching-empty');empty.append(icon(),element('h2','','这个课次的文件夹已准备好'),element('p','','教学项目尚未添加。你可以先体验第19课的三个工程。'));
        const sample=button('yx-primary-button','查看第19课示例',()=>choose(state,'03',19));empty.append(sample);content.append(empty);
      } else {
        const note=element('p','yx-sample-note',`第 ${lesson.id} 课 · 选择适合你的起点`);content.append(note);
        if(lesson.materials?.length){
          const materials=element('section','yx-lesson-materials');
          materials.setAttribute('aria-label','本课教学资料');
          materials.append(element('h2','','教学资料'),element('p','','课件、教案与任务单，和本课工程配套使用。'));
          const links=element('div','yx-material-links');
          for(const file of lesson.materials){
            const link=element('a','yx-material-link',file.name);link.href=file.url;link.download=file.file;
            links.append(link);
          }
          materials.append(links);content.append(materials);
        }
        lesson.projects.forEach((project,i)=>{
          const item=element('article','yx-template');item.setAttribute('data-teaching-project',project.id);
          const heading=element('div','yx-template-heading');heading.append(element('span','yx-project-index',String(i+1).padStart(2,'0')),element('h2','',project.name));
          item.append(heading,element('p','yx-template-description',project.description));
          const actions=element('div','yx-template-actions');const open=button('yx-primary-button','打开项目',()=>openProject(state,project,open));open.disabled=!!state.opening;
          const download=element('a','yx-download-link','下载 AIA');download.href=project.url;download.download=project.file;
          actions.append(open,download);item.append(actions);content.append(item);
        });
        content.append(element('p','yx-copy-note','打开后可继续编辑；你的课程副本会保存在“我的项目”中。'));
      }
    }
    left.append(content,state.status);
    renderRoute(state,stage);
    nativeView(state);
  }
  async function openProject(state,project,control) {
    if(state.opening)return;
    const bridge=window.YuxuanTeaching;
    if(!bridge){state.status.textContent='编辑器尚未准备好，请稍后重试。';return;}
    state.opening=true;state.panel.querySelectorAll('.yx-template button').forEach(b=>b.disabled=true);
    const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),30000);
    state.status.textContent='正在打开'+project.name+'…';control.textContent='正在打开…';
    try {
      const found=bridge.openExisting(project.projectName);
      if(found==='opened'){state.status.textContent='';return;}
      if(found==='trash')throw Error('你的课程副本在回收站中，请先恢复后再打开。');
      const resource=await fetch(project.url,{credentials:'same-origin',signal:controller.signal});
      if(!resource.ok)throw Error('教学工程文件无法读取，请检查软件文件是否完整。');
      const archive=await resource.blob();const data=new FormData();data.append('uploadProjectArchive',archive,project.file);
      const response=await fetch('ode/upload/project/'+encodeURIComponent(project.projectName),{method:'POST',body:data,credentials:'same-origin',signal:controller.signal});
      if(!response.ok)throw Error('工程导入失败，请稍后重试。');
      const result=bridge.openImported(await response.text());
      if(result!=='opened')throw Error('未能导入教学工程，请确认已进入本地工作区后重试。');
      state.status.textContent='';
    } catch(error) {state.status.textContent=error.name==='AbortError'?'打开超时，请稍后再试。':error.message;}
    finally {clearTimeout(timeout);state.opening=false;control.textContent='打开项目';state.panel.querySelectorAll('.yx-template button').forEach(b=>b.disabled=false);}
  }
  function mount(host) {
    if(states.has(host))return;
    const personal=host.querySelector('[data-yuxuan-personal-projects]'),box=host.closest('[data-yuxuan-project-box]');if(!personal||!box)return;
    const state={host,personal,box,active:false,stage:null,lesson:null,nativeActive:undefined};
    try{const saved=JSON.parse(sessionStorage.getItem('yuxuan-teaching-view-v1'));if(saved){state.active=saved.active===true;state.stage=saved.stage;state.lesson=saved.lesson;}}catch(_){}
    states.set(host,state);
    document.querySelectorAll('.ya-Toolbar').forEach(toolbar=>{
      // Native project and trash titles share this toolbar in every locale.
      if(toolbar.querySelectorAll('.left>.ya-ProjectName').length===2)
        toolbar.setAttribute('data-yuxuan-project-toolbar','true');
    });
    const tabs=element('div','yx-project-view-switch');state.tabs=tabs;
    tabs.append(button('yx-view-tab','我的项目',()=>{state.active=false;save(state);nativeView(state);}),button('yx-view-tab','教学项目',()=>{state.active=true;save(state);nativeView(state);}));
    tabs.children[0].dataset.view='personal';tabs.children[1].dataset.view='teaching';
    tabs.children[1].setAttribute('aria-label','切换到教学项目');tabs.children[0].setAttribute('aria-label','切换到我的项目');
    tabs.append(element('span','yx-view-count','8阶段 / 56课'));
    state.panel=element('section','yx-teaching-browser');state.panel.setAttribute('aria-label','教学项目');state.panel.hidden=true;
    state.left=element('section','yx-library-pane');state.left.setAttribute('aria-label','教学项目文件夹');
    state.route=element('aside','yx-curriculum-pane');state.route.setAttribute('aria-label','教学大纲示意图');
    state.status=element('p','yx-teaching-status');state.status.setAttribute('role','status');state.status.setAttribute('aria-live','polite');
    state.panel.append(state.left,state.route);host.insertBefore(tabs,personal);host.append(state.panel);
    state.left.append(element('p','yx-loading','正在载入课程目录…'));
    getCatalog().then(c=>{state.catalog=c;render(state);}).catch(error=>{state.left.replaceChildren(element('p','yx-loading',error.message),button('yx-primary-button','重新加载',()=>{getCatalog().then(c=>{state.catalog=c;render(state);}).catch(e=>state.status.textContent=e.message);}));});
    new MutationObserver(()=>{state.nativeActive=undefined;nativeView(state);}).observe(box,{attributes:true,attributeFilter:['data-yuxuan-project-box']});
    window.addEventListener('resize',()=>resize(state));
    window.addEventListener('yuxuan-teaching-ready',()=>nativeView(state));
    nativeView(state);
  }
  function scan() {
    const hosts=[...document.querySelectorAll('[data-yuxuan-teaching-host]')];hosts.forEach(mount);
    // ProjectListBox is a singleton. Stop watching the document once mounted so
    // dragging Blockly blocks does not keep scanning unrelated SVG subtrees.
    if(hosts.length&&hosts.every(h=>states.has(h)))observer.disconnect();
  }
  let scheduled=false;const observer=new MutationObserver(records=>{
    if(scheduled||!records.some(r=>[...r.addedNodes].some(n=>n.nodeType===1&&(n.matches?.('[data-yuxuan-teaching-host]')||n.querySelector?.('[data-yuxuan-teaching-host]')))))return;
    scheduled=true;requestAnimationFrame(()=>{scheduled=false;scan();});
  });observer.observe(document.documentElement,{subtree:true,childList:true});
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',scan,{once:true});else scan();
})();

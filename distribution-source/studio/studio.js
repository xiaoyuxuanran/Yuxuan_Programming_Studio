'use strict';
const $ = id => document.getElementById(id);
const token = location.hash.slice(1);
let state, current, editor, active, selected = '', selectedFolder = false, jobId, polling, theme = 'light';
let fontSize = 14, sidebarVisible = true, packagePanelSelected = false, viewPreferenceWrite = Promise.resolve();
let mode = new URLSearchParams(location.search).get('mode') === 'cpp' ? 'cpp' : 'python';
const files = new Map();
async function api(path, body) {
  const response = await fetch('/api/' + path, {method:body ? 'POST':'GET', headers:{'X-Studio-Token':token,'Content-Type':'application/json'}, body:body ? JSON.stringify(body):undefined});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || '操作失败');
  return data;
}
function toast(text) { $('toast').textContent = text; $('toast').hidden = false; clearTimeout(toast.timer); toast.timer = setTimeout(() => $('toast').hidden = true, 5000); }
function guarded(fn) { return (...args) => Promise.resolve().then(() => fn(...args)).catch(e => toast(e.message)); }
function promptText(title, hint, value = '', label = '名称') {
  return new Promise(resolve => { const dialog = $('promptDialog'); $('promptTitle').textContent = title; $('promptHint').textContent = hint; $('promptLabel').textContent = label; $('promptValue').value = value; dialog.returnValue = 'cancel'; dialog.onclose = () => resolve(dialog.returnValue === 'ok' ? $('promptValue').value.trim() : null); dialog.showModal(); $('promptValue').focus(); $('promptValue').select(); });
}
function applyTheme(value) { theme = value; document.documentElement.dataset.theme = value; $('theme').textContent = value === 'light' ? '☀ Light' : '☾ Dark'; if (window.monaco) monaco.editor.setTheme(value === 'light' ? 'vs' : 'vs-dark'); }
function applyFontSize(value) {
  fontSize = Number.isInteger(value) ? Math.max(10,Math.min(32,value)) : 14;
  editor?.updateOptions({fontSize});
  document.documentElement.style.setProperty('--editor-font-size',fontSize + 'px');
  $('fontReset').textContent = fontSize + ' px';
  $('fontSmaller').disabled = fontSize === 10; $('fontLarger').disabled = fontSize === 32;
}
function applySidebarVisibility(value) {
  sidebarVisible = value !== false; $('sidebar').hidden = !sidebarVisible;
  $('toggleSidebar').setAttribute('aria-expanded',String(sidebarVisible));
  const label = (sidebarVisible ? '隐藏':'显示') + '侧边栏 (Ctrl+B)';
  $('toggleSidebar').title = label; $('toggleSidebar').setAttribute('aria-label',label);
  $('filesPanel').classList.toggle('active',sidebarVisible && !packagePanelSelected);
  $('packagesPanel').classList.toggle('active',sidebarVisible && packagePanelSelected);
  editor?.layout();
}
function persistViewPreferences() {
  const preferences = {editorFontSize:fontSize,sidebarVisible};
  viewPreferenceWrite = viewPreferenceWrite.catch(()=>{}).then(()=>api('preferences',preferences));
  return viewPreferenceWrite;
}
function changeFontSize(value) { applyFontSize(value); return persistViewPreferences(); }
function toggleSidebar() { applySidebarVisibility(!sidebarVisible); return persistViewPreferences(); }
function togglePanel(packages) {
  if(sidebarVisible && packagePanelSelected === packages) return toggleSidebar();
  showPanel(packages); applySidebarVisibility(true); return persistViewPreferences();
}
function renderTabs() {
  $('tabs').replaceChildren();
  for (const [path, f] of files) { const tab = document.createElement('button'); tab.className = 'fileTab' + (active === path ? ' active':''); tab.setAttribute('role','tab'); tab.setAttribute('aria-selected',active === path); tab.title = path; tab.append(document.createTextNode((f.dirty ? '● ' : '') + path.split('/').pop())); const close = document.createElement('span'); close.className = 'close'; close.textContent = ' ×'; close.setAttribute('aria-label','关闭文件'); close.onclick = e => { e.stopPropagation(); guarded(async () => { if(f.dirty) await saveFile(path); const wasActive = active === path; files.delete(path); f.model.dispose(); if(wasActive) { active = undefined; editor.setModel(null); const next = files.keys().next().value; if(next) activate(next); } renderTabs(); })(); }; tab.append(close); tab.onclick = () => activate(path); $('tabs').append(tab); }
  $('savedState').textContent = files.get(active)?.dirty ? '未保存' : '已保存';
}
function activate(path) { active = path; selected = path; selectedFolder = false; editor.setModel(files.get(path).model); editor.focus(); renderTabs(); highlightTree(); $('fileStatus').textContent = 'UTF-8 · ' + path; }
async function openFile(path) { if(!files.has(path)) { const data = await api('file?project=' + current.id + '&path=' + encodeURIComponent(path)); const language = /\.py$/i.test(path) ? 'python' : /\.(cpp|cc|cxx|h|hpp)$/i.test(path) ? 'cpp' : /\.json$/i.test(path) ? 'json' : 'plaintext'; const model = monaco.editor.createModel(data.text, language, monaco.Uri.parse('file:///' + current.id + '/' + path)); const f = {model,mtime:data.mtime,dirty:false}; model.onDidChangeContent(() => { f.dirty = true; renderTabs(); clearTimeout(f.timer); f.timer = setTimeout(guarded(() => saveFile(path)),900); }); files.set(path,f); } activate(path); }
async function saveFile(path) { const f = files.get(path); if(!f) return; if(f.saving) { await f.saving; if(f.dirty) return saveFile(path); return; } if(!f.dirty) return; const text = f.model.getValue(); f.saving = (async () => { const data = await api('file/save',{project:current.id,path,text,mtime:f.mtime}); f.mtime = data.mtime; f.dirty = f.model.getValue() !== text; renderTabs(); })(); try { await f.saving; } finally { f.saving = null; } if(f.dirty) await saveFile(path); }
async function saveAll() { for(const [path] of files) await saveFile(path); }
function highlightTree() { document.querySelectorAll('[data-file]').forEach(row => row.classList.toggle('selected',row.dataset.file === selected)); }
async function refreshTree() {
  const nodes = await api('tree?project=' + current.id); $('tree').replaceChildren();
  function append(items, target, depth = 0) { for(const node of items) { const row = document.createElement('button'); row.className = 'treeRow'; row.style.paddingLeft = (12 + depth * 16) + 'px'; row.dataset.file = node.path; row.title = node.path; row.textContent = (node.folder ? '▾  ' : /\.py$/i.test(node.name) ? 'Py  ' : /\.(cpp|h|hpp)$/i.test(node.name) ? 'C++  ' : '··  ') + node.name; target.append(row); if(node.folder) { const group = document.createElement('div'); target.append(group); append(node.children,group,depth+1); row.onclick = () => { selected = node.path; selectedFolder = true; group.hidden = !group.hidden; row.textContent = (group.hidden ? '▸  ' : '▾  ') + node.name; highlightTree(); }; } else row.onclick = guarded(() => openFile(node.path)); } }
  append(nodes,$('tree')); highlightTree(); return nodes;
}
async function selectProject(id) { await saveAll(); for(const f of files.values()) f.model.dispose(); files.clear(); active = undefined; selected = ''; selectedFolder = false; editor.setModel(null); current = state.projects.find(p => p.id === id); $('project').value = id; $('projectTitle').textContent = current.name; $('projectPath').textContent = current.path; $('pythonVersion').value = current.python; updateRuntime(); renderTabs(); const nodes = await refreshTree(); const first = nodes.find(n => !n.folder && n.name === (mode === 'python' ? 'main.py' : 'main.cpp')) || nodes.find(n => !n.folder); if(first) await openFile(first.path); }
function updateRuntime() { $('runtimeStatus').textContent = mode === 'python' ? 'Python ' + $('pythonVersion').value + ' · 项目独立环境' : 'Clang++ · C++17'; }
async function selectMode(value) { if(state.installedModes && !state.installedModes.includes(value)) throw new Error('此项目尚未安装，请运行完整安装包添加'); await saveAll(); mode = value; $('mode').value = mode; $('workspaceLabel').textContent = mode === 'python' ? 'Python Workspace' : 'C++ Workspace'; $('pythonVersion').hidden = mode !== 'python'; $('packagesPanel').hidden = mode !== 'python'; showPanel(false); const projects = state.projects.filter(p => p.mode === mode); $('project').replaceChildren(); for(const p of projects) { const option = document.createElement('option'); option.value = p.id; option.textContent = p.name; $('project').append(option); } $('projectCount').textContent = projects.length; if(projects.length) await selectProject(projects[0].id); else { const p = await api('project/create',{name:(mode === 'python' ? 'Python' : 'C++') + ' 项目 ' + Date.now().toString().slice(-6),mode}); state.projects.push(p); await selectMode(mode); } }
function showPanel(packages) { packagePanelSelected = packages; $('projectPanel').hidden = packages; $('packagePanel').hidden = !packages; applySidebarVisibility(sidebarVisible); }
async function startJob(id) { jobId = id; clearTimeout(polling); let cursor = 0; $('output').textContent = ''; $('run').disabled = true; $('stop').disabled = false; $('runStatus').textContent = '运行中';
  async function poll() { try { const data = await api('job?id=' + id + '&cursor=' + cursor); if(jobId !== id) return; cursor = data.cursor; const output = $('output'); const atBottom = output.scrollHeight - output.scrollTop - output.clientHeight < 50; output.textContent += data.output; if(atBottom) output.scrollTop = output.scrollHeight; $('runTitle').textContent = data.title; $('runStatus').textContent = data.running ? '运行中 · ' + data.elapsed + 's' : '退出码 ' + data.code; if(data.running) polling = setTimeout(poll,250); else { $('run').disabled = false; $('stop').disabled = true; jobId = null; } } catch(e) { toast(e.message); $('run').disabled = false; $('stop').disabled = true; jobId = null; } } await poll(); }
async function run() { if(jobId) throw new Error('请先停止或等待当前任务结束'); if(!active) throw new Error('请先选择代码文件'); await saveAll(); const data = await api('run',{project:current.id,path:active,version:$('pythonVersion').value}); await startJob(data.id); }
async function searchPackage() { const name = $('packageQuery').value.trim(); const panel = $('packageResult'); panel.textContent = '正在搜索…'; try { const data = await api('package?name=' + encodeURIComponent(name)); panel.replaceChildren(); const title = document.createElement('h3'); title.textContent = data.name; const version = document.createElement('span'); version.className = 'badge'; version.textContent = '最新 ' + data.version; const summary = document.createElement('p'); summary.textContent = data.summary; const requirement = document.createElement('p'); requirement.textContent = 'Python 要求：' + (data.requiresPython || '未声明'); const input = document.createElement('input'); input.value = data.name; input.setAttribute('aria-label','安装名称或指定版本'); input.title = '可以输入 名称==版本'; const install = document.createElement('button'); install.className = 'primary'; install.textContent = '安装到 Python ' + $('pythonVersion').value; install.onclick = guarded(async () => { if(jobId) throw new Error('请先停止或等待当前任务结束'); const result = await api('package/install',{project:current.id,version:$('pythonVersion').value,package:input.value.trim()}); await startJob(result.id); }); panel.append(title,version,summary,requirement,input,install); } catch(e) { panel.textContent = e.message; } }
function setupCompletions() {
  monaco.languages.registerCompletionItemProvider('python',{triggerCharacters:['.'],provideCompletionItems:async (model,position) => { try { const names = await api('complete',{source:model.getValue(),line:position.lineNumber,column:position.column}); const word = model.getWordUntilPosition(position); return {suggestions:names.map(name => ({label:name,kind:monaco.languages.CompletionItemKind.Function,insertText:name,range:{startLineNumber:position.lineNumber,endLineNumber:position.lineNumber,startColumn:word.startColumn,endColumn:word.endColumn}}))}; } catch { return {suggestions:[]}; } }});
  const cppWords = ['std::cout','std::cin','std::endl','std::string','std::vector','std::map','std::sort','std::getline','size_t','nullptr','constexpr','auto','int','double','bool','char','void','return','if','else','for','while','class','struct','public','private','const','include'];
  monaco.languages.registerCompletionItemProvider('cpp',{triggerCharacters:[':'],provideCompletionItems:(model,position) => { const word = model.getWordUntilPosition(position); const names = new Set([...cppWords,...(model.getValue().match(/\b[A-Za-z_]\w{2,}\b/g) || [])]); return {suggestions:[...names].slice(0,500).map(name => ({label:name,kind:monaco.languages.CompletionItemKind.Keyword,insertText:name,range:{startLineNumber:position.lineNumber,endLineNumber:position.lineNumber,startColumn:word.startColumn,endColumn:word.endColumn}}))}; }});
  for(const lang of ['python','cpp']) monaco.languages.registerCompletionItemProvider(lang,{provideCompletionItems:(model,position) => { const word = model.getWordUntilPosition(position); const snippets = lang === 'python' ? [['for loop','for ${1:i} in range(${2:10}):\n    ${3:print(i)}'],['main',"def main():\n    ${1:pass}\n\nif __name__ == '__main__':\n    main()"]] : [['main','#include <iostream>\n\nint main() {\n    ${1:std::cout << "Hello!" << std::endl;}\n    return 0;\n}'],['for loop','for (int ${1:i} = 0; ${1:i} < ${2:10}; ++${1:i}) {\n    ${3}\n}']]; return {suggestions:snippets.map(([label,text]) => ({label,kind:monaco.languages.CompletionItemKind.Snippet,insertText:text,insertTextRules:monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,range:{startLineNumber:position.lineNumber,endLineNumber:position.lineNumber,startColumn:word.startColumn,endColumn:word.endColumn}}))}; }});
}
async function initialize() {
  if(!token) throw new Error('请通过羽轩启动器打开代码工作区');
  state = await api('state'); if(state.installedModes) { for(const option of $('mode').options) option.disabled = !state.installedModes.includes(option.value); if(!state.installedModes.includes(mode)) mode = state.installedModes[0]; } applyTheme(state.theme || 'light'); applyFontSize(state.editorFontSize); applySidebarVisibility(state.sidebarVisible);
  require.config({paths:{vs:'vs'}});
  await new Promise((resolve,reject) => require(['vs/editor/editor.main'],resolve,reject));
  $('editor').replaceChildren(); editor = monaco.editor.create($('editor'),{theme:theme === 'light' ? 'vs':'vs-dark',editContext:false,automaticLayout:true,fontSize,mouseWheelZoom:false,fontFamily:'Consolas, "Cascadia Code", monospace',minimap:{enabled:false},scrollBeyondLastLine:false,padding:{top:18},tabSize:4,insertSpaces:true,wordWrap:'off',model:null});
  editor.onDidChangeCursorPosition(e => $('position').textContent = '行 ' + e.position.lineNumber + '，列 ' + e.position.column);
  editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS,guarded(saveAll)); editor.addCommand(monaco.KeyCode.F5,guarded(run)); editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter,guarded(run)); setupCompletions();
  $('save').onclick = guarded(async () => { await saveAll(); toast('所有文件已保存'); }); $('run').onclick = guarded(run);
  $('stop').onclick = guarded(() => api('stop',{id:jobId})); $('clearOutput').onclick = () => $('output').textContent = '';
  $('inputForm').onsubmit = guarded(async e => { e.preventDefault(); if(!jobId) throw new Error('当前没有运行中的程序'); const text = $('stdin').value; await api('input',{id:jobId,text}); $('output').textContent += '> ' + text + '\n'; $('stdin').value = ''; });
  $('theme').onclick = guarded(async () => { const next = theme === 'light' ? 'dark':'light'; await api('preferences',{theme:next}); applyTheme(next); });
  $('mode').onchange = guarded(() => selectMode($('mode').value)); $('project').onchange = guarded(() => selectProject($('project').value));
  $('pythonVersion').onchange = guarded(async () => { await api('version',{project:current.id,version:$('pythonVersion').value}); current.python = $('pythonVersion').value; updateRuntime(); });
  $('fontSmaller').onclick = guarded(()=>changeFontSize(fontSize - 1)); $('fontLarger').onclick = guarded(()=>changeFontSize(fontSize + 1)); $('fontReset').onclick = guarded(()=>changeFontSize(14));
  $('toggleSidebar').onclick = guarded(toggleSidebar);
  $('filesPanel').onclick = guarded(()=>togglePanel(false)); $('packagesPanel').onclick = guarded(()=>togglePanel(true));
  document.addEventListener('keydown',e=>{
    if(!(e.ctrlKey || e.metaKey) || e.altKey || e.isComposing) return;
    let action;
    if(e.code === 'Equal' || e.code === 'NumpadAdd') action = ()=>changeFontSize(fontSize + 1);
    else if(e.code === 'Minus' || e.code === 'NumpadSubtract') action = ()=>changeFontSize(fontSize - 1);
    else if(e.code === 'Digit0' || e.code === 'Numpad0') action = ()=>changeFontSize(14);
    else if(e.code === 'KeyB' && !e.shiftKey) action = toggleSidebar;
    if(action) { e.preventDefault(); e.stopPropagation(); guarded(action)(); }
  },true);
  $('editor').addEventListener('wheel',e=>{
    if((e.ctrlKey || e.metaKey) && e.deltaY !== 0) { e.preventDefault(); e.stopPropagation(); guarded(()=>changeFontSize(fontSize + (e.deltaY < 0 ? 1:-1)))(); }
  },{passive:false,capture:true});
  $('searchPackage').onclick = guarded(searchPackage); $('packageQuery').onkeydown = e => { if(e.key === 'Enter') guarded(searchPackage)(); };
  document.querySelectorAll('[data-package]').forEach(button => button.onclick = guarded(async () => { $('packageQuery').value = button.dataset.package; await searchPackage(); }));
  $('refresh').onclick = guarded(refreshTree);
  $('newProject').onclick = guarded(async () => { const name = await promptText('新建 ' + (mode === 'python' ? 'Python':'C++') + ' 项目','项目保存在本地工作区，创建后会提供一个示例文件。'); if(name) { const p = await api('project/create',{name,mode}); state.projects.push(p); await selectMode(mode); await selectProject(p.id); } });
  $('openProject').onclick = guarded(async () => { const path = await promptText('打开项目文件夹','输入已有文件夹的完整路径，例如 D:\\Projects\\Hello。文件将直接在这个文件夹内编辑。','','文件夹路径'); if(path) { const p = await api('project/open',{path,mode}); if(!state.projects.some(x => x.id === p.id)) state.projects.push(p); await selectMode(p.mode); await selectProject(p.id); } });
  const parentPath = () => selectedFolder ? selected + '/' : selected.includes('/') ? selected.slice(0,selected.lastIndexOf('/')+1) : '';
  $('newFile').onclick = guarded(async () => { const path = await promptText('新建文件','可以使用相对路径创建子目录。',parentPath() + (mode === 'python' ? 'new.py':'new.cpp'),'文件路径'); if(path) { await api('file/create',{project:current.id,path}); await refreshTree(); await openFile(path); } });
  $('newFolder').onclick = guarded(async () => { const path = await promptText('新建文件夹','文件夹会创建在当前项目内。',parentPath(),'文件夹路径'); if(path) { await api('folder/create',{project:current.id,path}); await refreshTree(); } });
  $('renameFile').onclick = guarded(async () => { if(!selected) throw new Error('请先选择文件或文件夹'); await saveAll(); const to = await promptText('重命名','输入新的项目内相对路径。',selected,'新路径'); if(to && to !== selected) { const old = selected; await api('file/rename',{project:current.id,path:old,to}); for(const [path,f] of [...files]) if(path === old || path.startsWith(old + '/')) { files.delete(path); f.model.dispose(); } active = undefined; editor.setModel(null); selected = to; await refreshTree(); renderTabs(); if(!selectedFolder) await openFile(to); } });
  $('trashFile').onclick = guarded(async () => { if(!selected) throw new Error('请先选择文件或文件夹'); const path = selected; const answer = await promptText('移入回收目录','此项将移动到项目的 .studio-trash 文件夹，可在资源管理器中恢复。输入 DELETE 确认。','','确认'); if(answer !== 'DELETE') return; await saveAll(); await api('file/trash',{project:current.id,path}); for(const [name,f] of [...files]) if(name === path || name.startsWith(path + '/')) { files.delete(name); f.model.dispose(); } active = undefined; editor.setModel(null); selected = ''; await refreshTree(); renderTabs(); toast('已移入项目回收目录'); });
  const resize = $('consoleResize'); resize.onpointerdown = e => { resize.setPointerCapture(e.pointerId); }; resize.onpointermove = e => { if(resize.hasPointerCapture(e.pointerId)) document.querySelector('.console').style.height = Math.max(110,Math.min(innerHeight - 260,innerHeight - e.clientY - 24)) + 'px'; }; resize.onkeydown = e => { if(e.key === 'ArrowUp' || e.key === 'ArrowDown') { e.preventDefault(); const box = document.querySelector('.console'); box.style.height = Math.max(110,box.clientHeight + (e.key === 'ArrowUp' ? 20:-20)) + 'px'; } };
  window.addEventListener('beforeunload',e => { if([...files.values()].some(f => f.dirty)) { e.preventDefault(); e.returnValue = ''; } });
  await selectMode(mode);
}
initialize().catch(e => { $('connection').textContent = '连接失败'; toast(e.message); });

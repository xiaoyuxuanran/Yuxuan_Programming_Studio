// Desktop integration for Mixly 2.0 rc4. Original Mixly authors and license retained.
const {app, ipcMain, BrowserWindow, shell} = require('electron');
const fs = require('fs');
const path = require('path');
const http = require('http');
const {fileURLToPath} = require('url');
const args = process.argv;
const argument = (name, fallback) => args.includes(name) ? args[args.indexOf(name)+1] : fallback;
const root = path.resolve(__dirname, '../../../..');
const data = path.resolve(argument('--data-dir', path.join(app.getPath('appData'), 'AppInventorOffline/mixly')));
fs.mkdirSync(data, {recursive:true});
app.setName('Mixly4Yuxuan');
app.setPath('userData', path.join(data, 'profile'));
process.env.NODE_PATH = path.join(__dirname, 'node_modules');
require('module').Module._initPaths();
const paths = {data, root, src:path.join(data,'src'), cliRoot:path.join(root,'mixly/arduino-cli'),
  python:path.join(root,'runtime/python3.8.9/python.exe'), preload:path.join(__dirname,'preload.js')};
const compilers=JSON.parse(require('child_process').execFileSync(paths.python,['-X','utf8',path.join(__dirname,'compiler-paths.py'),paths.cliRoot,data],{encoding:'utf8',windowsHide:true,timeout:10000}));
paths.compilerPaths=compilers.paths;paths.compilerProperties=compilers.properties;
process.env.PYTHONPATH = path.join(root,'mixly/python-libs');
delete process.env.PYTHONHOME;
process.env.PYTHONUTF8 = '1';
// Refresh shipped files only. User libraries and generated artifacts stay in place.
const revision = '2.3.2-desktop-rc4-5';
const marker = path.join(data,'source-version.txt');
if (!fs.existsSync(marker) || fs.readFileSync(marker,'utf8') !== revision) {
  const source = path.join(root,'mixly/src');
  function copy(dir, dest) {
    fs.mkdirSync(dest,{recursive:true});
    for (const item of fs.readdirSync(dir,{withFileTypes:true})) {
      if (['ThirdParty','myLib','upload','cloudLibsUrl.json'].includes(item.name)) continue;
      const from=path.join(dir,item.name), to=path.join(dest,item.name);
      if(item.isDirectory()) copy(from,to); else fs.copyFileSync(from,to);
    }
  }
  copy(source, paths.src);
  fs.writeFileSync(marker,revision);
}
const cliConfig = {directories:{data:path.join(paths.cliRoot,'Arduino15'),downloads:path.join(data,'staging'),user:path.join(data,'Arduino')},metrics:{enabled:false},updater:{enable_notification:false}};
fs.writeFileSync(path.join(data,'arduino-cli.json'),JSON.stringify(cliConfig,null,2));
const allowed = new Set(['https://www.wch.cn/downloads/CH341SER_EXE.html','https://www.wch.cn/downloads/CH343SER_EXE.html',
  'https://www.silabs.com/software-and-tools/usb-to-uart-bridge-vcp-drivers','https://ftdichip.com/drivers/vcp-drivers/',
  'https://gitee.com/mixly2/mixly2.0_src','https://mixly.cn/']);
function isLocal(url) {
  try { const filename=path.resolve(fileURLToPath(url)); const rel=path.relative(paths.src,filename);return !rel.startsWith('..')&&!path.isAbsolute(rel); } catch {return false;}
}
ipcMain.on('yuxuan-paths', (event) => {if(isLocal(event.sender.getURL())) event.returnValue=paths;else event.returnValue=null;});
ipcMain.handle('yuxuan-open-driver', async (event,url) => {if(!isLocal(event.sender.getURL())||!allowed.has(url))throw Error('Invalid manufacturer link');await shell.openExternal(url);});
app.on('web-contents-created', (_, contents) => {
  require('@electron/remote/main').enable(contents);
  contents.on('will-navigate',(event,url)=>{if(!isLocal(url)){event.preventDefault();if(/^https:\/\//i.test(url))shell.openExternal(url);}});
  contents.setWindowOpenHandler(({url})=>{if(/^https:\/\//i.test(url))shell.openExternal(url);return {action:'deny'};});
});
const token = argument('--suite-token','');
let openWindow = null, server;
function registerOpen(fn) {openWindow=fn;}
app.whenReady().then(()=>{
  if (!token) return;
  server=http.createServer((req,res)=>{
    const send=(status,obj)=>{res.writeHead(status,{'Content-Type':'application/json'});res.end(JSON.stringify(obj));};
    if(req.method==='GET'&&req.url==='/health')return send(200,{app:'YuxuanMixly',version:'2.3.2'});
    if(req.headers['x-suite-token']!==token)return send(403,{error:'Forbidden'});
    if(req.method==='POST'&&req.url==='/focus'){
      const wins=BrowserWindow.getAllWindows(); if(!wins.length&&openWindow)openWindow();else {if(wins[0].isMinimized())wins[0].restore();wins[0].show();wins[0].focus();}return send(200,{ok:true});
    }
    if(req.method==='POST'&&req.url==='/shutdown'){send(200,{ok:true});for(const win of BrowserWindow.getAllWindows())win.close();return;}
    send(404,{error:'Not found'});
  });
  server.listen(0,'127.0.0.1',()=>fs.writeFileSync(path.join(data,'mixly-running.json'),JSON.stringify({pid:process.pid,port:server.address().port,app:'YuxuanMixly'})));
});
app.on('will-quit',()=>{if(server)server.close();try{fs.unlinkSync(path.join(data,'mixly-running.json'));}catch{}});
module.exports={paths,registerOpen};

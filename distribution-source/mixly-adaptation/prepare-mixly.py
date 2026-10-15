"""Stage the four requested Mixly 2.0 environments with the official desktop runtime."""
import json, pathlib, shutil, re
here = pathlib.Path(__file__).resolve().parent
native = here.parent / 'native'
dest = native / 'mixly'
upstream = here / 'upstream'
runtime = dest / 'runtime'
def copyfile(src, target):
    src, target = pathlib.Path(src), pathlib.Path(target)
    if target.exists() and src.stat().st_size == target.stat().st_size and src.stat().st_mtime_ns == target.stat().st_mtime_ns:
        return str(target)
    return shutil.copy2(src,target)
def copytree(src, target, exclude=()):
    shutil.copytree(src, target, dirs_exist_ok=True, copy_function=copyfile, ignore=shutil.ignore_patterns('.git','__pycache__',*exclude))
def patch(relative, before, after):
    filename=dest/'src'/relative
    text=filename.read_text(encoding='utf-8')
    if before not in text: raise RuntimeError(f'Missing patch target: {relative}: {before[:50]}')
    filename.write_text(text.replace(before,after),encoding='utf-8')
runtime.mkdir(parents=True,exist_ok=True)
desktop=here/'desktop-upstream'
for item in desktop.iterdir():
    if item.is_file() and (item.suffix.lower() in ('.exe','.dll','.pak','.dat','.bin') or item.name in ('version','LICENSE','LICENSES.chromium.html')):
        copyfile(item,runtime/item.name)
copytree(desktop/'locales',runtime/'locales')
app=runtime/'resources/app';app.mkdir(parents=True,exist_ok=True)
copytree(desktop/'resources/app/node_modules',app/'node_modules')
for name in ('suite-main.js','preload.js','compiler-paths.py','sdk-junction.ps1'):shutil.copy2(here/name,app/name)
(app/'package.json').write_text(json.dumps({'name':'Mixly4Yuxuan','version':'2.1.0','description':'Mixly 2.0 rc4 integrated into Yuxuan programming suite','main':'main.js','author':'Mixly development team; Yuxuan suite adaptation'},ensure_ascii=False,indent=2),encoding='utf-8')
main=upstream.joinpath('main.js').read_text(encoding='utf-8')
main="const suite = require('./suite-main.js');\n"+main
main=main.replace("process.env['ELECTRON_DISABLE_SECURITY_WARNINGS'] = 'true';",'')
main=main.replace('minHeight: 400','minHeight: 600').replace('minWidth: 700','minWidth: 900').replace('width: 0','width: 1280').replace('height: 0','height: 800')
main=main.replace("icon: __dirname + '/files/mixly_uncompressed.ico'","icon: nodePath.join(suite.paths.root, 'resources/brand.ico')")
main=main.replace('allowRunningInsecureContent: true,','')
main=main.replace('webPreferences: {', 'webPreferences: {\n            preload: suite.paths.preload,')
main=main.replace("win.loadFile('./src/index.html')","win.loadFile(nodePath.join(suite.paths.src,'index.html'))")
main=main.replace("nodeFs.appendFileSync('./log.txt',", "nodeFs.appendFileSync(nodePath.join(suite.paths.data,'log.txt'),")
start=main.index("app.on('ready', () => {");end=main.index("app.on('activate'",start)
main=main[:start]+"suite.registerOpen(() => createWindow(null));\napp.on('ready', () => createWindow(null));\n\n"+main[end:]
start=main.index("    app.on('second-instance'");end=main.index('} else {\n    app.quit();',start)
main=main[:start]+"    app.on('second-instance', () => { const wins=BrowserWindow.getAllWindows(); if(wins.length){wins[0].restore();wins[0].focus();}else createWindow(null); });\n"+main[end:]
(app/'main.js').write_text(main,encoding='utf-8')
source=dest/'src';source.mkdir(parents=True,exist_ok=True)
for name in ('common','files','pyTools','usbcdc'):
    if (upstream/name).exists():copytree(upstream/name,source/name)
for name in ('LICENSE','sw-config.json','user-config.json'):
    if (upstream/name).exists():shutil.copy2(upstream/name,source/name)
boards=['arduino_avr','arduino_esp8266','micropython_esp32','arduino_esp32']
for name in boards+['micropython_common']:
    copytree(upstream/'boards/default'/name,source/'boards/default'/name)
allboards=json.loads((upstream/'boards.json').read_text(encoding='utf-8'))
filtered=[next(b for b in allboards if b['boardIndex'].split('/')[-2]==name) for name in boards]
(source/'boards.json').write_text(json.dumps(filtered,ensure_ascii=False,indent=2),encoding='utf-8')
for name in boards:
    cfg=source/'boards/default'/name/'config.json';data=json.loads(cfg.read_text(encoding='utf-8'))
    data['lib']['mixly']['url']=[f'https://download.mixlylibs.cloud/mixly-packages/cloud-libs/{name}/libs.json']
    cfg.write_text(json.dumps(data,ensure_ascii=False,indent=4),encoding='utf-8')
    entry=next(b for b in filtered if b['boardIndex'].split('/')[-2]==name)
    index=source/entry['boardIndex'].removeprefix('./');text=index.read_text(encoding='utf-8').replace('<head>','<head>\n  <link rel="stylesheet" href="../../../yuxuan-workspace.css">')
    text=text.replace('</head>','  <script src="../../../yuxuan-recovery.js"></script>\n</head>')
    index.write_text(text,encoding='utf-8')
for original,renamed in [('home.html','index.html'),('home.js','yuxuan-home.js'),('home.css','yuxuan-home.css'),('workspace-theme.css','yuxuan-workspace.css'),('workspace-recovery.js','yuxuan-recovery.js')]:shutil.copy2(here/original,source/renamed)
for name in ('brand-logo.png','brand.ico'):shutil.copy2(native/'resources'/name,source/'files'/name)
sw=json.loads((source/'sw-config.json').read_text(encoding='utf-8'));sw['version']='Mixly4Yuxuan · Mixly 2.0 rc4';sw['board']={'url':''};(source/'sw-config.json').write_text(json.dumps(sw,ensure_ascii=False,indent=2),encoding='utf-8')
patch('common/modules/mixly-modules/common/modules.js',"Env.srcDirPath = path.resolve(Env.indexDirPath, '../../../');","const suitePaths = Modules.electron.ipcRenderer.sendSync('yuxuan-paths');\n    if (!suitePaths) throw Error('Mixly suite paths unavailable');\n    Env.clientPath = suitePaths.data;\n    Env.python3Path = suitePaths.python;\n    Env.arduinoRoot = suitePaths.cliRoot;\n    Env.srcDirPath = path.resolve(Env.indexDirPath, '../../../');")
ardu='common/modules/mixly-modules/electron/arduino-shell.js'
patch(ardu,"path.resolve(Env.clientPath, './arduino-cli')","Env.arduinoRoot")
patch(ardu,"path.resolve(ArduShell.shellPath, '../arduino-cli.json')","path.resolve(Env.clientPath, 'arduino-cli.json')")
patch(ardu,"downloads: path.resolve(ArduShell.shellPath, '../staging')","downloads: path.resolve(Env.clientPath, 'staging')")
patch(ardu,"user: path.resolve(ArduShell.shellPath, '../Arduino')","user: path.resolve(Env.clientPath, 'Arduino')")
patch(ardu,'"enabled": true','"enabled": false')
filename=dest/'src'/ardu;text=filename.read_text(encoding='utf-8')
start=text.index('        let myLibPath = ');end=text.index("        ArduShell.runCmd(layerNum, 'compile'",start)
text=text[:start]+'''        const myLibPath = path.join(Env.indexDirPath,'libraries/myLib');
        const libPaths = fs_extend.isdir(myLibPath) ? [myLibPath] : [];
        const thirdPartyPath=path.join(Env.indexDirPath,'libraries/ThirdParty');
        if(fs_extend.isdir(thirdPartyPath)) for(const name of fs.readdirSync(thirdPartyPath)) {
            const lib=path.join(thirdPartyPath,name,'libraries'); if(fs_extend.isdir(lib))libPaths.push(lib);
        }
        libPaths.push(path.resolve(ArduShell.shellPath,'../libraries'));
        const compilerProperties=Modules.electron.ipcRenderer.sendSync('yuxuan-paths').compilerProperties[boardType.split(':').slice(0,2).join(':')] ?? [];
        const cmdStr=['compile','-b',boardType,'--config-file',path.join(Env.clientPath,'arduino-cli.json'),
            '--build-cache-path',path.join(Env.clientPath,'mixlyBuildCache'),'--verbose','--libraries',libPaths.join(','),
            '--build-path',path.join(Env.clientPath,'mixlyBuild'),path.join(Env.clientPath,'testArduino/testArduino.ino'),'--no-color'];
        for(const [name,value] of compilerProperties)cmdStr.push('--build-property',name+'='+value);
''' +text[end:]
text=text.replace('ArduShell.shell = child_process.exec(cmd,', "ArduShell.shell = Array.isArray(cmd) ? child_process.spawn(ArduShell.shellPath,cmd,{windowsHide:true,cwd:Env.clientPath}) : child_process.exec(cmd,")
text=text.replace("        ArduShell.shell.stdout.on('data',", "        ArduShell.shell.stdout.setEncoding('utf8');\n        ArduShell.shell.stderr.setEncoding('utf8');\n        ArduShell.shell.stdout.on('data',")
text=text.replace("            if (data.length < 1000) {\n                statusBarTerminal.addValue(data);\n            }", "            statusBarTerminal.addValue(data);")
filename.write_text(text,encoding='utf-8')
patch('common/modules/mixly-modules/electron/electron.js','webPreferences: {',"webPreferences: {\n                preload: Modules.electron.ipcRenderer.sendSync('yuxuan-paths').preload,")
patch('common/modules/mixly-modules/electron/file.js',"path.resolve(app.getAppPath(), 'src/sample')","path.resolve(Env.clientPath, 'projects')")
# Make official archive URLs use TLS if an upstream catalog still uses HTTP.
patch('common/modules/mixly-modules/electron/cloud-download.js','return new Promise((resolve, reject) => {',"if (typeof url === 'string' && /^http:\\/\\/download\\.mixlylibs\\.cloud\\//i.test(url)) url=url.replace(/^http:/i,'https:');\n    return new Promise((resolve, reject) => {")
copytree(here/'arduino-libs/arduino-cli/libraries',dest/'arduino-cli/libraries',('examples','example','tests','test','docs'))
metadata={'suiteVersion':'2.1.0','source':'https://gitee.com/mixly2/mixly2.0_src','tag':'2.0-rc4','commit':'a7d91f1e3c621a3132fb8ea38c92877bb0834830','runtime':'Electron 19.0.6, official Mixly Windows distribution','environments':boards,'cloudLibraries':'Official Mixly2 HTTPS catalogs; user libraries live in per-user data','drivers':'Official manufacturer download pages; no silent driver installation'}
metadata.update({
    'windowsRuntimeSource':'https://gitee.com/mixly2/mixly2.0-win32-x64',
    'windowsRuntimeCommit':'d1bb6950c91f3b8f68d571188393b3d6b6603eb7',
    'arduinoLibrariesSource':'https://gitee.com/mixly2/arduino-libs',
    'arduinoLibrariesCommit':'2b7ca7d23afec725d23f80b3d995d4cf5fa57a01',
    'arduinoCli':'0.35.3',
    'cores':{'avr':'1.8.6','esp8266':'3.1.2','esp32':'2.0.17'},
})
(dest/'UPSTREAM.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
print('Staged Mixly rc4, four environments, official native runtime and Arduino libraries.')

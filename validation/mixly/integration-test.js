// Development-only functional acceptance, loaded from the workspace, never shipped in the runtime.
const {app,BrowserWindow}=require('electron');
const fs=require('fs'),path=require('path');
const resultFile=process.env.YUXUAN_MIXLY_TEST_RESULT;
const results=[];const errors=[];
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
function record(name,data){results.push({name,...data});fs.writeFileSync(resultFile,JSON.stringify({results,errors},null,2));}
app.whenReady().then(async()=>{
  try{
    await delay(1200);const win=BrowserWindow.getAllWindows()[0];
    if(!win)throw Error('No Mixly window');
    const wc=win.webContents;
    wc.on('console-message',(_,level,message,line,source)=>{if(level>=2)errors.push({message,line,source});});
    const paths=require(path.join(app.getAppPath(),'suite-main.js')).paths;
    const output=path.dirname(resultFile);
    const run=code=>wc.executeJavaScript(code,true);
    async function waitFor(code,timeout=35000){const start=Date.now();while(Date.now()-start<timeout){try{if(await run('Boolean('+code+')'))return;}catch{}await delay(250);}throw Error('Timed out: '+code);}
    await waitFor("document.querySelectorAll('.board').length===4");
    record('home',{boards:await run("Array.from(document.querySelectorAll('.board h3')).map(el=>el.textContent)"),drivers:await run("Array.from(document.querySelectorAll('.driver h3')).map(el=>el.textContent)")});
    fs.writeFileSync(path.join(output,'mixly-home.png'),(await wc.capturePage()).toPNG());
    const entries=JSON.parse(fs.readFileSync(path.join(paths.src,'boards.json'),'utf8'));
    for(const entry of entries){
      const query=Object.entries({thirdPartyBoard:'false',boardIndex:entry.boardIndex,boardType:entry.boardType,language:entry.language}).map(([k,v])=>encodeURIComponent(k)+'='+encodeURIComponent(v)).join('&');
      await wc.loadURL(require('url').pathToFileURL(path.join(paths.src,entry.boardIndex)).href+'?'+query);
      await delay(3000);
      record('boot-'+entry.boardType,await run("({mixly:typeof Mixly,keys:typeof Mixly==='object'?Object.keys(Mixly):[],editor:!!window.Mixly?.Editor?.blockEditor,serial:!!window.Mixly?.Electron?.Serial,file:!!window.Mixly?.Electron?.File,recovery:!!window.Mixly?.YuxuanRecovery,scripts:Array.from(document.scripts).filter(s=>s.src.includes('yuxuan')).map(s=>s.src),ready:document.readyState})"));
      await waitFor("window.Mixly?.Editor?.blockEditor && Mixly.Electron?.Serial && Mixly.YuxuanRecovery");
      const boardDir=entry.boardIndex.split('/').slice(-2)[0];
      const before=await run("({title:document.title,board:Mixly.Config.BOARD.boardType,fqbn:Mixly.Boards.getSelectedBoardCommandParam(),serial:typeof Mixly.Electron.Serial.refreshPorts,python:Mixly.Env.python3Path,cli:Mixly.Electron.ArduShell?.shellPath,ports:Mixly.Electron.Serial.ports})");
      if(before.board!==entry.boardType)throw Error('Board query mismatch '+before.board);
      // Choose a simple native block from this environment's actual toolbox.
      const setup=await run(`(()=>{const ws=Mixly.Editor.blockEditor;ws.clear();const types=Array.from(document.querySelectorAll('#toolbox block')).map(el=>el.getAttribute('type'));const wanted=${JSON.stringify(entry.language==='MicroPython'?['mp_print','text_print','controls_repeat_ext']:['inout_digital_write','controls_repeat_ext'])};const type=wanted.find(t=>Blockly.Blocks[t])||types.find(t=>Blockly.Blocks[t]&&t.includes('print'));if(!type)throw Error('No sample block');const block=ws.newBlock(type);block.initSvg();block.render();Mixly.Editor.mainEditor.selected='BLOCK';const code=Mixly.MFile.getCode();return {type,code,xml:Mixly.MFile.getMix()};})()`);
      if(!setup.code||setup.code.length<5)throw Error('No generated code '+boardDir);
      fs.writeFileSync(path.join(output,boardDir+(entry.language==='MicroPython'?'.py':'.ino')),setup.code);
      const savePath=path.join(paths.data,'projects',boardDir+'.mix');
      await run(`new Promise(resolve=>{Mixly.Electron.File.openedFilePath=${JSON.stringify(savePath)};Mixly.Electron.File.save(()=>resolve(true));})`);
      if(!fs.existsSync(savePath))throw Error('Save failed '+boardDir);
      const roundtrip=await run(`(()=>{Mixly.Editor.blockEditor.clear();Mixly.MFile.parseMix($(Mixly.Modules.fs.readFileSync(${JSON.stringify(savePath)},'utf8')),false,true);Mixly.YuxuanRecovery.save();return Mixly.Editor.blockEditor.getAllBlocks(false).length;})()`);
      if(roundtrip<1)throw Error('Project reopen lost blocks');
      const cloud=await run("new Promise(resolve=>Mixly.Electron.CloudDownload.getJson(Mixly.Electron.LibManager.URL.mixly,Mixly.Modules.path.join(Mixly.Env.clientPath,'download'),resolve))");
      if(cloud[0]||!Array.isArray(cloud[1])||!cloud[1].length)throw Error('Cloud catalog unavailable '+boardDir+': '+JSON.stringify(cloud[0]));
      record(boardDir,{...before,block:setup.type,code:setup.code,projectRoundtripBlocks:roundtrip,cloudLibraryCount:cloud[1].length});
      if(boardDir==='arduino_avr'){
        const installed=await run(`(async()=>{const lm=Mixly.Electron.LibManager;const info=lm.compareLibConfig(${JSON.stringify(cloud[1][0])});info.index=0;info.desPath=Mixly.Modules.path.join(Mixly.Env.indexDirPath,'libraries/ThirdParty');const result=await lm.importWithUrl(info);if(result.error)throw Error(String(result.error));return {name:info.name,dir:info.desPath,loaded:lm.getLibs(info.desPath),status:lm.compareLibConfig(info).status};})()`);
        record('cloud-library-install',{library:installed.name,status:installed.status,loadedXml:installed.loaded.xml.length,loadedJs:installed.loaded.js});
      }
      if(entry.language==='MicroPython'){
        await run("Mixly.Electron.LibManager.showManageDialog()");await delay(1300);fs.writeFileSync(path.join(output,'mixly-cloud-libraries.png'),(await wc.capturePage()).toPNG());await run('layer.closeAll()');
        record('python-esp32-firmware',{commands:await run('Mixly.Config.BOARD.burn'),upload:await run('Mixly.Config.BOARD.upload')});
      }else{
        // Run the original UI compilation route, including code writing and bundled library resolution.
        const compiled=await run(`new Promise(resolve=>{const start=Date.now();Mixly.Electron.ArduShell.compile(()=>resolve({ok:true,seconds:(Date.now()-start)/1000}));const timer=setInterval(()=>{const shell=Mixly.Electron.ArduShell.shell;if(shell?.exitCode!==null&&shell?.exitCode!==undefined){clearInterval(timer);if(shell.exitCode!==0)resolve({ok:false,exit:shell.exitCode});}if(Date.now()-start>240000){clearInterval(timer);Mixly.Electron.ArduShell.cancel();resolve({ok:false,timeout:true});}},500);})`);
        record(boardDir+'-compile',compiled);if(!compiled.ok)throw Error('Compilation failed '+boardDir);
      }
      fs.writeFileSync(path.join(output,boardDir+'.png'),(await wc.capturePage()).toPNG());
    }
    // Native serial enumeration and a real stream-level mock echo, without touching connected hardware.
    const serial=require('serialport');const ports=await serial.SerialPort.list();
    const {MockBinding}=require('@serialport/binding-mock');const {SerialPortStream}=require('@serialport/stream');
    MockBinding.createPort('/dev/YUXUAN_MIXLY_TEST',{echo:true,record:true});
    const port=new SerialPortStream({binding:MockBinding,path:'/dev/YUXUAN_MIXLY_TEST',baudRate:115200,autoOpen:false});
    await new Promise((resolve,reject)=>port.open(err=>err?reject(err):resolve()));
    const echo=await new Promise((resolve,reject)=>{port.once('data',data=>resolve(data.toString()));port.write('Mixly serial echo\r\n',err=>{if(err)reject(err);});setTimeout(()=>reject(Error('Serial echo timeout')),2000);});
    await new Promise((resolve,reject)=>port.close(err=>err?reject(err):resolve()));
    record('serial',{nativePortCount:ports.length,ports,baudRate:115200,mockEcho:echo});
    const failures=errors.filter(error=>!error.message.includes('was deprecated'));
    if(failures.length)throw Error('Renderer errors: '+JSON.stringify(failures.slice(0,3)));
    record('acceptance',{ok:true});app.exit(0);
  }catch(error){record('acceptance',{ok:false,error:error.stack});app.exit(1);}
});

const {app,BrowserWindow}=require('electron');
const fs=require('fs'),path=require('path'),{pathToFileURL}=require('url');
const target=process.env.YUXUAN_MIXLY_TEST_RESULT;
const report={ok:false,boards:[],errors:[]};
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
app.whenReady().then(async()=>{try{
  await delay(1000);const win=BrowserWindow.getAllWindows()[0],wc=win.webContents;
  const paths=require(path.join(app.getAppPath(),'suite-main.js')).paths;
  const run=async code=>{const value=await wc.executeJavaScript('(async()=>{try{return {ok:true,value:await eval('+JSON.stringify(code)+')}}catch(e){return {ok:false,error:e.stack}}})()',true);if(!value.ok)throw Error(value.error);return value.value;};
  const entries=JSON.parse(fs.readFileSync(path.join(paths.src,'boards.json'),'utf8'));
  if(entries.length!==4||!await run("document.querySelectorAll('.board').length===4 && !document.body.textContent.includes('仿真')"))throw Error('Desktop home should have four boards and no simulation');
  for(const entry of entries.filter(e=>!process.env.YUXUAN_MIXLY_ONLY_BOARD||e.boardType===process.env.YUXUAN_MIXLY_ONLY_BOARD)){
    const query=new URLSearchParams({thirdPartyBoard:'false',boardIndex:entry.boardIndex,boardType:entry.boardType,language:entry.language});
    await wc.loadURL(pathToFileURL(path.join(paths.src,entry.boardIndex)).href+'?'+query);
    let ready=false;for(let i=0;i<180;i++){try{ready=await run('!!Mixly?.YuxuanRecovery?.ready');if(ready)break;}catch{}await delay(150);}if(!ready)throw Error('Editor not ready '+entry.boardType);
    const fixture=await run(`(()=>{const ws=Mixly.Editor.blockEditor;ws.clear();const type=${JSON.stringify(entry.language==='MicroPython'?'system_print':'serial_println')};const b=ws.newBlock(type);b.initSvg();b.render();const input=b.getInput('VAR')||b.getInput('CONTENT');if(input&&Blockly.Blocks.text){const t=ws.newBlock('text');t.setFieldValue('Yuxuan 232','TEXT');t.initSvg();t.render();input.connection.connect(t.outputConnection);}Mixly.Editor.mainEditor.selected='BLOCK';Mixly.YuxuanRecovery.save();return {count:ws.getAllBlocks(false).length,code:Mixly.MFile.getCode(),fqbn:Mixly.Boards.getSelectedBoardCommandParam()};})()`);
    let cloud=await run("new Promise(resolve=>{const timer=setTimeout(()=>resolve(['timeout',[]]),30000);Mixly.Electron.CloudDownload.getJson(Mixly.Electron.LibManager.URL.mixly,Mixly.Modules.path.join(Mixly.Env.clientPath,'download'),value=>{clearTimeout(timer);resolve(value)});})");
    if(cloud[0]||!Array.isArray(cloud[1])||!cloud[1].length)throw Error('Cloud catalog failed '+entry.boardType+': '+JSON.stringify(cloud[0]));
    const info={board:entry.boardType,...fixture,cloudLibraries:cloud[1].length};
    if(entry.boardType==='Arduino AVR'){
      info.cloudInstall=await run(`(async()=>{const lm=Mixly.Electron.LibManager;const info=lm.compareLibConfig(${JSON.stringify(cloud[1][0])});info.index=0;info.desPath=Mixly.Modules.path.join(Mixly.Env.indexDirPath,'libraries/ThirdParty');const result=await lm.importWithUrl(info);if(result.error)throw Error(String(result.error));const loaded=lm.getLibs(info.desPath);return {name:info.name,xml:loaded.xml.length,installed:lm.compareLibConfig(info).status};})()`);
      if(!info.cloudInstall.xml)throw Error('Downloaded cloud library did not load');
    }
    if(entry.language!=='MicroPython'){
      info.compile=await run("new Promise(resolve=>{let done=false;const start=Date.now();const finish=value=>{if(!done){done=true;clearInterval(timer);resolve(value)}};const timer=setInterval(()=>{const p=Mixly.Electron.ArduShell.shell;if(p?.exitCode!=null&&p.exitCode!==0)finish({ok:false,exit:p.exitCode});if(Date.now()-start>240000){Mixly.Electron.ArduShell.cancel();finish({ok:false,timeout:true})}},300);Mixly.Electron.ArduShell.compile(()=>finish({ok:true,seconds:(Date.now()-start)/1000}));})");
      if(!info.compile.ok){info.compile.output=await run("Mixly.mainStatusBarTab.getStatusBarById('output').editor.getValue()");report.boards.push(info);throw Error('Desktop compile failed '+entry.boardType+JSON.stringify(info.compile));}
    }
    if(entry.boardType==='Arduino ESP32'){
      const bt=await run(`(()=>{const ws=Mixly.Editor.blockEditor;ws.clear();const types=['serialBT_Init','serialBT_available','serialBT_read','serialBT_write','serialBT_print'];if(!types.every(t=>Blockly.Blocks[t]&&document.querySelector('#toolbox block[type="'+t+'"]')))throw Error('Bluetooth entries missing');const init=ws.newBlock('serialBT_Init');init.initSvg();init.render();const text=ws.newBlock('text');text.setFieldValue('DesktopBT','TEXT');text.initSvg();text.render();init.getInput('CONTENT').connection.connect(text.outputConnection);const gate=ws.newBlock('controls_if');gate.initSvg();gate.render();const available=ws.newBlock('serialBT_available');available.initSvg();available.render();gate.getInput('IF0').connection.connect(available.outputConnection);const print=ws.newBlock('serialBT_print');print.initSvg();print.render();const read=ws.newBlock('serialBT_read');read.initSvg();read.render();print.getInput('CONTENT').connection.connect(read.outputConnection);gate.getInput('DO0').connection.connect(print.previousConnection);init.nextConnection.connect(gate.previousConnection);const code=Mixly.MFile.getCode();if(!code.includes('SerialBT.begin("DesktopBT")')||!code.includes('if (SerialBT.available() > 0)'))throw Error('Bluetooth generation mismatch '+code);return {types,code};})()`);
      info.bluetooth=bt;
      info.bluetooth.compile=await run("new Promise(resolve=>{let done=false;const start=Date.now();const finish=value=>{if(!done){done=true;clearInterval(timer);resolve(value)}};const timer=setInterval(()=>{const p=Mixly.Electron.ArduShell.shell;if(p?.exitCode!=null&&p.exitCode!==0)finish({ok:false,exit:p.exitCode});if(Date.now()-start>240000){Mixly.Electron.ArduShell.cancel();finish({ok:false,timeout:true})}},300);Mixly.Electron.ArduShell.compile(()=>finish({ok:true,seconds:(Date.now()-start)/1000}));})");
      if(!info.bluetooth.compile.ok){info.bluetooth.compile.output=await run("Mixly.mainStatusBarTab.getStatusBarById('output').editor.getValue()");report.boards.push(info);throw Error('Bluetooth compile failed');}
    }
    report.boards.push(info);fs.writeFileSync(target,JSON.stringify(report,null,2));
  }
  const {MockBinding}=require('@serialport/binding-mock');const {SerialPortStream}=require('@serialport/stream');
  MockBinding.createPort('/dev/YUXUAN_232',{echo:true,record:true});const port=new SerialPortStream({binding:MockBinding,path:'/dev/YUXUAN_232',baudRate:115200,autoOpen:false});
  await new Promise((resolve,reject)=>port.open(e=>e?reject(e):resolve()));
  const echo=await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('Echo timeout')),2500);port.once('data',data=>{clearTimeout(timer);resolve(data.toString())});port.write('Yuxuan serial 232\r\n')});
  await new Promise((resolve,reject)=>port.close(e=>e?reject(e):resolve()));if(echo!=='Yuxuan serial 232\r\n')throw Error('Serial echo mismatch');
  report.serial={ok:true,baud:115200,echo};report.ok=true;fs.writeFileSync(target,JSON.stringify(report,null,2));win.close();
}catch(error){report.errors.push(error.stack);fs.writeFileSync(target,JSON.stringify(report,null,2));app.exit(1);}});

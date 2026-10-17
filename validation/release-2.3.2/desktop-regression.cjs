// Development-only Electron acceptance. Never installed in the product.
const {app,BrowserWindow}=require('electron');
const fs=require('fs'),path=require('path'),{pathToFileURL}=require('url');
const output=process.env.YUXUAN_MIXLY_TEST_RESULT;
const baseline=process.env.YUXUAN_MIXLY_BASELINE==='1';
const restart=process.env.YUXUAN_MIXLY_RESTART==='1';
const result={ok:false,baseline,boards:[],errors:[]};
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
app.whenReady().then(async()=>{try{
  await delay(1000);const win=BrowserWindow.getAllWindows()[0],wc=win.webContents;
  const suite=require(path.join(app.getAppPath(),'suite-main.js'));const paths=suite.paths;
  const run=async code=>{const value=await wc.executeJavaScript('(async()=>{try{return {ok:true,value:await eval('+JSON.stringify(code)+')}}catch(error){return {ok:false,error:error.stack}}})()',true);if(!value.ok)throw Error(value.error);return value.value;};
  async function ready(){for(let i=0;i<160;i++){try{if(await run('!!window.Mixly?.YuxuanRecovery?.save && !!Mixly.Editor?.blockEditor')){await delay(700);return;}}catch{}await delay(150);}throw Error('Editor not ready');}
  const entries=JSON.parse(fs.readFileSync(path.join(paths.src,'boards.json'),'utf8'));
  for(const entry of baseline?entries.slice(0,1):entries){
    const query=new URLSearchParams({thirdPartyBoard:'false',boardIndex:entry.boardIndex,boardType:entry.boardType,language:entry.language});
    await wc.loadURL(pathToFileURL(path.join(paths.src,entry.boardIndex)).href+'?'+query);await ready();
    if(restart){
      const expected=JSON.parse(fs.readFileSync(path.join(paths.data,'restart-expectations.json'),'utf8')).find(x=>x.board===entry.boardType);
      const restored=await run('({count:Mixly.Editor.blockEditor.getAllBlocks(false).length,code:Mixly.MFile.getCode(),opened:Mixly.Electron.File.openedFilePath})');
      if(restored.count!==expected.initial.count||restored.code!==expected.initial.code||restored.opened!==expected.savedFile)throw Error('Process restart changed project '+entry.boardType);
      result.boards.push({board:entry.boardType,processRestartVerified:true,...restored});continue;
    }
    const initial=await run(`(()=>{const ws=Mixly.Editor.blockEditor;ws.clear();const types=${JSON.stringify(entry.language==='MicroPython'?['system_print','serial_println']:['serial_println'])};const type=types.find(t=>Blockly.Blocks[t]);if(!type)throw Error('No fixture block');const b=ws.newBlock(type);b.initSvg();b.render();const input=b.getInput('VAR')||b.getInput('CONTENT');if(input&&Blockly.Blocks.text){const text=ws.newBlock('text');text.setFieldValue('Yuxuan 232','TEXT');text.initSvg();text.render();input.connection.connect(text.outputConnection);}b.moveBy(40,50);Mixly.Editor.mainEditor.selected='BLOCK';Mixly.YuxuanRecovery.save();return {count:ws.getAllBlocks(false).length,code:Mixly.MFile.getCode(),type};})()`);
    const counts=[];
    for(let cycle=0;cycle<3;cycle++){
      await wc.reload();await ready();
      const state=await run('({count:Mixly.Editor.blockEditor.getAllBlocks(false).length,code:Mixly.MFile.getCode()})');counts.push(state.count);
      if(!baseline&&(state.count!==initial.count||state.code!==initial.code))throw Error('Reload changed blocks/code '+entry.boardType+': '+JSON.stringify(state));
    }
    result.boards.push({board:entry.boardType,initial,counts});
    if(baseline)continue;
    const manual=initial.code+(entry.language==='MicroPython'?'\n# handwritten code\n':'\n// handwritten code\n');
    await run(`(()=>{Mixly.Editor.mainEditor.drag.full('NEGATIVE');Mixly.Editor.codeEditor.setValue(${JSON.stringify(manual)},-1);Mixly.YuxuanRecovery.save();})()`);
    await wc.reload();await ready();
    const codeState=await run('({count:Mixly.Editor.blockEditor.getAllBlocks(false).length,code:Mixly.MFile.getCode(),selected:Mixly.Editor.mainEditor.selected,ready:Mixly.YuxuanRecovery.ready})');
    if(codeState.count!==initial.count||codeState.code!==manual)throw Error('Code-view recovery lost blocks or manual code '+JSON.stringify(codeState));
    await run("Mixly.Editor.mainEditor.drag.full('POSITIVE');Mixly.YuxuanRecovery.save()");
    const savedFile=path.join(paths.data,'projects',entry.boardType.replaceAll(' ','-')+'.mix');fs.mkdirSync(path.dirname(savedFile),{recursive:true});
    await run(`new Promise(resolve=>{Mixly.Electron.File.openedFilePath=${JSON.stringify(savedFile)};Mixly.Electron.File.save(()=>resolve(true));})`);
    await run(`(()=>{Mixly.Electron.File.openFile(${JSON.stringify(savedFile)});Mixly.YuxuanRecovery.save();})()`);
    if(!await run(`Mixly.Editor.blockEditor.getAllBlocks(false).length===${initial.count}`))throw Error('Explicit file reopen duplicated blocks');
    result.boards[result.boards.length-1].codeViewPreserved=true;
    result.boards[result.boards.length-1].savedFile=savedFile;
    // Use the actual serial dialog; no physical serial port is opened.
    await run(`(()=>{window.__serialClosed=0;window.__serialTest=Mixly.LayerExt.openSerialTool({},()=>{},()=>window.__serialClosed++);})()`);await delay(300);
    const close=await run(`(()=>{const b=document.querySelector('.yuxuan-serial-close');if(!b)throw Error('No explicit serial close button');const r=b.getBoundingClientRect();if(r.width<25||r.height<20)throw Error('Close button not visible');return {label:b.textContent,top:r.top,left:r.left,width:r.width,height:r.height};})()`);
    fs.writeFileSync(path.join(path.dirname(output),entry.boardType.replaceAll(' ','-')+'-serial.png'),(await wc.capturePage()).toPNG());
    await run("document.querySelector('.yuxuan-serial-close').click()");await delay(300);
    if(!await run('window.__serialClosed===1 && !document.querySelector(".layui-layer-page")'))throw Error('Serial dialog did not close once');
    await run('__serialTest.open(()=>{},()=>window.__serialClosed++)');await delay(200);await run("document.querySelector('.yuxuan-serial-close').click()");await delay(250);
    if(!await run('window.__serialClosed===2'))throw Error('Serial reopen/close callback duplicated');
    result.boards[result.boards.length-1].serialClose=close;
  }
  result.ok=baseline?result.boards[0].counts.some(c=>c>result.boards[0].initial.count):true;
  if(!baseline&&!restart)fs.writeFileSync(path.join(paths.data,'restart-expectations.json'),JSON.stringify(result.boards));
  fs.writeFileSync(output,JSON.stringify(result,null,2));win.close();
}catch(error){result.errors.push(error.stack);fs.writeFileSync(output,JSON.stringify(result,null,2));app.exit(1);}});

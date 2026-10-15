const fs=require('fs'),path=require('path');
const {chromium}=require('C:/Users/Yuxuan/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const report={errors:[],failed:[],simulation:[]};
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 page.on('pageerror',e=>report.errors.push(e.stack));
 page.on('response',r=>{if(r.status()>=400)report.failed.push({url:r.url(),status:r.status()})});
 page.on('dialog',d=>d.accept());
 try{
  await page.goto('http://127.0.0.1:8768/#'+'1'.repeat(64));await page.getByText('服务已就绪',{exact:false}).waitFor();
  await page.locator('[data-board="arduino_avr"]').click();await page.waitForTimeout(4000);
  const avr=page.frames().find(f=>f.url().includes('/boards/index.html'));
  const began=Date.now();
  await avr.getByText('编译',{exact:true}).first().click();
  await avr.waitForFunction(()=>document.body.innerText.includes('==编译成功=='),{},{timeout:120000});
  report.editorCompile={ok:true,seconds:(Date.now()-began)/1000};
  await page.screenshot({path:path.join(__dirname,'web-compile.png'),fullPage:true});
  await page.getByRole('button',{name:'仿真平台',exact:true}).click();await page.waitForTimeout(5000);
  const sim=page.frames().find(f=>f.url().includes('/mixvm/index.html'));
  report.simulatorOptions=await sim.locator('#board-selector option').evaluateAll(options=>options.map(o=>({value:o.value,text:o.textContent})));
  for(const text of ['Arduino UNO','ESP32 Generic','MixCK 电路仿真']){
   const opt=report.simulatorOptions.find(o=>o.text===text);if(!opt)throw new Error('Missing simulator '+text);
   await sim.locator('#board-selector').selectOption(opt.value);await page.waitForTimeout(7000);
   if(await sim.locator('.app-container:not(.show-toolbar)').count())await sim.locator('#toolbar-trigger').click();
   const editorFrame=sim.childFrames().find(f=>f.url().includes('/boards/index.html'));
   if(editorFrame&&text==='ESP32 Generic')await editorFrame.evaluate(()=>Mixly.Workspace.getMain().getEditorsManager().getActive().setValue("print('Yuxuan simulator OK')",'.py'));
   if(editorFrame&&text==='Arduino UNO')await editorFrame.evaluate(()=>Mixly.Workspace.getMain().getEditorsManager().getActive().setValue('void setup(){pinMode(13,OUTPUT);}\nvoid loop(){digitalWrite(13,HIGH);delay(100);digitalWrite(13,LOW);delay(100);}', '.ino'));
   if(!await sim.evaluate(()=>window.mixvmDebugUrlExampleState?.().simulationVisible))await sim.locator('#btn-simulation-toggle').click();
   await page.waitForTimeout(6000);
   if(await sim.locator('.app-container:not(.show-toolbar)').count())await sim.locator('#toolbar-trigger').click();
   const state=await sim.evaluate(()=>({text:document.body.innerText.slice(0,600),frames:[...document.querySelectorAll('iframe')].map(f=>({src:f.src,rect:f.getBoundingClientRect().toJSON()})),debug:window.mixvmDebugUrlExampleState?.(),run:document.querySelector('#btn-run-stop-toolbar').getBoundingClientRect().toJSON()}));
   report.simulation.push({board:text,...state});
   report.geometry=await page.evaluate(()=>({scrollY,frame:document.querySelector('#simulation-frame').getBoundingClientRect().toJSON()}));
   await page.screenshot({path:path.join(__dirname,'sim-before-run.png'),fullPage:true});
   fs.writeFileSync(path.join(__dirname,'interaction-verification.json'),JSON.stringify(report,null,2));
   await sim.locator('#btn-run-stop-toolbar').click();await page.waitForTimeout(4000);
   state.afterRun=await sim.locator('#btn-run-stop-toolbar').innerText();
   state.nested=[];for(const f of sim.childFrames())state.nested.push({url:f.url(),text:(await f.locator('body').innerText()).slice(0,1000)});
   report.simulation[report.simulation.length-1]={board:text,...state};
   await page.screenshot({path:path.join(__dirname,'sim-'+opt.value.replace(/[^a-zA-Z0-9]/g,'_')+'.png'),fullPage:true});
   if(state.afterRun.includes('停止'))await sim.locator('#btn-run-stop-toolbar').click();
  }
  report.ok=report.errors.length===0&&report.failed.length===0;
 }finally{fs.writeFileSync(path.join(__dirname,'interaction-verification.json'),JSON.stringify(report,null,2));await browser.close();}
 console.log(JSON.stringify(report,null,2));
})().catch(e=>{console.error(e);process.exitCode=1});

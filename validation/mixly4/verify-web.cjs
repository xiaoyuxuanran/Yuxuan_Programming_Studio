const fs=require('fs'),path=require('path');
const {chromium}=require('C:/Users/Yuxuan/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const report={boards:[],errors:[],failed:[]};
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 page.on('pageerror',e=>report.errors.push(e.stack));
 page.on('response',r=>{if(r.status()>=400)report.failed.push({url:r.url(),status:r.status()});});
 page.on('dialog',d=>d.accept());
 try{
  await page.goto('http://127.0.0.1:8768/#'+'1'.repeat(64));
  await page.getByText('服务已就绪',{exact:false}).waitFor();
  for(const board of ['arduino_avr','arduino_esp32','arduino_esp8266','micropython_esp32']){
   await page.locator('#home-brand').click();
   await page.locator(`[data-board="${board}"]`).click();
   const frame=await page.locator('#editor-frame').contentFrame();
   await frame.locator('body').waitFor();
   await page.waitForTimeout(4000);
   const actual=page.frames().find(f=>f.url().includes('/boards/index.html'));
   const state=await actual.evaluate(()=>({title:document.title,workspace:!!Mixly.Workspace.getMain(),fqbn:Mixly.Boards.getSelectedBoardCommandParam(),blocks:Object.keys(Blockly.Blocks).length,code:Mixly.Workspace.getMain().getEditorsManager().getActive().getCode(),services:Object.keys(Mixly).filter(k=>/Shell|Plugin/.test(k))}));
   report.boards.push({board,...state});
   if(!state.workspace||state.blocks<100)throw new Error('Board failed: '+board);
   if(board==='arduino_avr'){
    report.cloud=await actual.evaluate(async()=>{
      const catalog=await (await fetch('/api/cloud/catalog?board=arduino_avr')).json();
      const item=catalog.find(x=>/PS2/i.test(x.name))||catalog.find(x=>/TM1637/i.test(x.name))||catalog[0];
      const response=await fetch(item.downloadUrl);if(!response.ok)throw new Error(await response.text());
      const result=await Mixly.PluginManager.installPlugin(item,item.version,await response.blob());
      await Mixly.PluginManager.mountInstalledPlugin(item.id);
      const record=Mixly.PluginManager.runtimePlugins.get(item.id);
      return {catalogCount:catalog.length,item:item.name,installed:result.pluginInfo.id,blocks:Object.keys(record?.blocks||{}),generators:Object.keys(record?.generators||{})};
    });
   }
  }
  await page.getByRole('button',{name:'仿真平台',exact:true}).click();
  await page.waitForTimeout(8000);
  const sim=page.frames().find(f=>f.url().includes('/mixvm/index.html'));
  report.simulation=await sim.evaluate(()=>({title:document.title,text:document.body.innerText.slice(0,2500),frames:[...document.querySelectorAll('iframe')].map(f=>f.src)}));
  await page.screenshot({path:path.join(__dirname,'web-simulation.png'),fullPage:true});
 }finally{fs.writeFileSync(path.join(__dirname,'web-verification.json'),JSON.stringify(report,null,2));await browser.close();}
 console.log(JSON.stringify(report,null,2));
})().catch(e=>{console.error(e);process.exitCode=1});

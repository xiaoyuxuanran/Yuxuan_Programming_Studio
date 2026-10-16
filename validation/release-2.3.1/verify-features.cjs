const fs=require('fs'),path=require('path'),assert=require('assert');
const {chromium}=require('C:/Users/Yuxuan/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const report={errors:[],failed:[]};
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true});const page=await browser.newPage({viewport:{width:1440,height:1000}});page.on('pageerror',e=>report.errors.push(e.stack));page.on('response',r=>{if(r.status()>=400)report.failed.push({url:r.url(),status:r.status()})});page.on('dialog',d=>d.accept());
try {
 await page.goto('http://127.0.0.1:8888/login');await page.locator('#username').fill('Release231');await page.getByRole('button',{name:'进入工作区'}).click();await page.getByText('优质扩展',{exact:true}).waitFor();await page.getByText('优质扩展',{exact:true}).click();
 report.extensions=[];
 for(const name of ['MqttTCP','BluetoothLE','ClientSocketAI2Ext']){
   const item=page.getByText(name,{exact:true});await item.waitFor();await item.scrollIntoViewIfNeeded();
   const icon=await item.evaluate(e=>{const p=e.closest('.ode-SimplePaletteItem')||e.parentElement;return [...p.querySelectorAll('img')].map(i=>({src:i.src,complete:i.complete,width:i.naturalWidth}))});
   assert(icon.some(i=>i.src.includes('/static/images/quality/')&&i.complete&&i.width>0),name+' icon unavailable');
   if(!await page.getByText(name+'1',{exact:true}).count())await item.dblclick();
   await page.getByText(name+'1',{exact:true}).first().waitFor();report.extensions.push({name,icon});
 }
 await page.screenshot({path:path.join(__dirname,'quality-extensions.png'),fullPage:true});
 await page.getByText('逻辑设计',{exact:true}).click();await page.waitForTimeout(4000);
 console.log('FRAMES',page.frames().map(f=>f.url()));
 let frame=page.frames().find(f=>f.url().includes('blockly'));
 if(!frame)for(const f of page.frames()){if(await f.evaluate(()=>!!window.Blockly).catch(()=>false)){frame=f;break}}
 assert(frame,'No Blockly editor');
 report.blockly=await frame.evaluate(()=>({rectType:typeof Blockly.utils.Rect,workspace:!!Blockly.getMainWorkspace(),selector:!!window.parent.document.querySelector('[data-yuxuan-block-selector]'),frameRect:window.frameElement?.getBoundingClientRect().toJSON()}));
 console.log('BLOCKLY',report.blockly);
 const block=await frame.evaluate(()=>{const w=Blockly.getMainWorkspace();const b=w.newBlock('math_number');b.initSvg();b.render();b.moveBy(260,160);b.getSvgRoot().setAttribute('id','yuxuan-drag-fixture');w.recordDeleteAreas();window.testDeleteBlockId=b.id;let view=b.getSvgRoot().ownerDocument.defaultView,dx=0,dy=0;while(view.frameElement){const r=view.frameElement.getBoundingClientRect();dx+=r.left;dy+=r.top;view=view.parent;}return {dx,dy,id:b.id,area:w.deleteAreaToolbox_,rect:b.getSvgRoot().getBoundingClientRect().toJSON(),hook:w.getDragTarget.toString().includes('yuxuanSidebar'),deleteType:typeof Blockly.DeleteArea,mutator:typeof w.isMutator,flyout:typeof w.isFlyout,mutatorValue:String(w.isMutator),flyoutValue:String(w.isFlyout),workspaceId:w.id,version:Blockly.VERSION}});console.log('NEW BLOCK',block);
 await page.waitForTimeout(400);block.rect=await page.locator('#yuxuan-drag-fixture').boundingBox();console.log('HIT GRID',await page.evaluate(r=>[8,16,25,35].map(x=>[6,12,20].map(y=>document.elementFromPoint(r.x+x,r.y+y)?.tagName+':'+document.elementFromPoint(r.x+x,r.y+y)?.getAttribute('class'))),block.rect));console.log('WORKSPACES',await frame.evaluate(()=>Blockly.Workspace.getAll().filter(w=>w.rendered&&!w.isFlyout).map(w=>({id:w.id,visible:w.isVisible(),parent:w.getParentSvg()?.outerHTML.slice(0,160),bbox:w.getParentSvg()?.getBoundingClientRect().toJSON(),main:w===Blockly.getMainWorkspace()}))));await page.screenshot({path:path.join(__dirname,'before-grab.png')} );const iframeOffset={x:0,y:0};const selector=await page.locator('[data-yuxuan-block-selector]:visible').boundingBox();assert(selector&&selector.width>0);
 await page.mouse.move(block.rect.x+iframeOffset.x+16,block.rect.y+iframeOffset.y+6);await page.mouse.down();await page.mouse.move(block.rect.x+iframeOffset.x+45,block.rect.y+iframeOffset.y+20,{steps:5});await page.mouse.move(selector.x+selector.width/2,selector.y+100,{steps:30});report.beforeDrop=await frame.evaluate(()=>({dragging:Blockly.getMainWorkspace().isDragging(),hook:!!Blockly.getMainWorkspace().yuxuanSidebarDeleteTarget_,workspaceId:Blockly.getMainWorkspace().id,selected:Blockly.getSelected()?.id,xy:Blockly.getMainWorkspace().getBlockById(window.testDeleteBlockId)?.getRelativeToSurfaceXY(),area:Blockly.getMainWorkspace().yuxuanSidebarDeleteTarget_?.getClientRect()}));console.log('DRAG',report.beforeDrop,selector);await page.screenshot({path:path.join(__dirname,'before-drop.png'),fullPage:true});await page.mouse.up();await page.waitForTimeout(700);
 report.dragDelete=await frame.evaluate(()=>!Blockly.getMainWorkspace().getBlockById(window.testDeleteBlockId));
 assert(report.dragDelete,'Dragging into category panel did not delete block');
 report.undo=await frame.evaluate(()=>{Blockly.getMainWorkspace().undo(false);return !!Blockly.getMainWorkspace().getBlockById(window.testDeleteBlockId)});assert(report.undo,'Deletion could not be undone');
 await page.screenshot({path:path.join(__dirname,'drag-delete.png'),fullPage:true});
 const projectId=new URL(page.url()).hash.slice(1);report.projectId=projectId;
 await page.waitForTimeout(1800);
 const source=await page.request.get('http://127.0.0.1:8888/ode/download/project-source/'+projectId);assert(source.ok(),await source.text());fs.writeFileSync(path.join(__dirname,'Extension231.aia'),await source.body());
 report.ok=report.errors.length===0&&report.failed.length===0;
}finally {fs.writeFileSync(path.join(__dirname,'feature-verification.json'),JSON.stringify(report,null,2));await browser.close()}
console.log(JSON.stringify(report,null,2));})().catch(e=>{console.error(e);process.exitCode=1});

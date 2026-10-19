const fs=require('fs'),path=require('path'),assert=require('assert');
const {chromium}=require('C:/Users/Yuxuan/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const HERE=path.resolve(__dirname,'..');
const lesson=Number(process.argv[2]),key='lesson'+String(lesson).padStart(2,'0');
const dir=path.join(HERE,'aia',key),spec=JSON.parse(fs.readFileSync(path.join(dir,'artifact-spec.json'),'utf8'));
const reportDir=path.join(HERE,'validation',key);fs.mkdirSync(reportDir,{recursive:true});
const images=path.join(HERE,'screenshots',key);fs.mkdirSync(images,{recursive:true});
const config=JSON.parse(fs.readFileSync(path.join(HERE,'services.json'),'utf8')),base=config.url;
// Compile last, after all imports; a completed GWT build popup otherwise retains menu focus.
const variants=[...(spec.versions||spec.variants)].sort((a,b)=>(a.kind==='answer'?1:0)-(b.kind==='answer'?1:0));
const report={lesson,started:new Date().toISOString(),projects:[],errors:[],runtime:'native App Inventor browser import and APK build; no Android device runtime test'};
function save(phase){report.phase=phase;fs.writeFileSync(path.join(reportDir,'native.json'),JSON.stringify(report,null,2));console.log('L'+lesson+' '+phase);}
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 const page=await browser.newPage({viewport:{width:1800,height:1200},deviceScaleFactor:2});
 if(process.env.COURSE_DEBUG_EXCEPTIONS){const cdp=await page.context().newCDPSession(page);await cdp.send('Debugger.enable');await cdp.send('Debugger.setPauseOnExceptions',{state:'all'});cdp.on('Debugger.paused',async e=>{if(e.reason==='exception'){(report.caughtExceptions??=[]).push({description:e.data?.description,frames:e.callFrames.slice(0,4).map(f=>({name:f.functionName,location:f.location}))});}await cdp.send('Debugger.resume').catch(()=>{});});}
 page.on('dialog',d=>d.accept());page.on('pageerror',e=>report.errors.push(e.message));
 page.on('console',m=>{(report.consoleLog??=[]).push(m.type()+': '+m.text());});
 try{
  for(let loginAttempt=0;loginAttempt<3;loginAttempt++){
   await page.goto(base+'login');
   if(await page.locator('#username').count()){
    await page.locator('#username').fill(process.env.COURSE_USER||'Course56');
    await Promise.all([page.waitForNavigation(),page.getByRole('button',{name:'进入工作区'}).click()]);
   }
   if(!(await page.locator('body').innerText()).includes('Error 403'))break;
   if(loginAttempt===2)throw new Error('Login CSRF session repeatedly rejected');
  }
  await page.getByText('项目 ▾',{exact:true}).waitFor();await page.waitForTimeout(3000);
  if(await page.getByText('关闭',{exact:true}).count())await page.getByText('关闭',{exact:true}).last().click();
  for(const variant of variants){
   save('import '+variant.name);
   const file=path.isAbsolute(variant.file)?variant.file:path.resolve(dir,variant.file);
   const old=new URL(page.url()).hash;let importedName=variant.name;
   for(let attempt=0;attempt<3;attempt++){
    await page.getByText('项目 ▾',{exact:true}).click();
    try{await page.getByText('导入项目(.aia)...',{exact:true}).waitFor({state:'visible',timeout:1500});break;}
    catch(e){await page.keyboard.press('Escape');await page.waitForTimeout(400);if(attempt===2)throw e;}
   }
   await page.getByText('导入项目(.aia)...',{exact:true}).click();
   await page.locator('input[accept=".aia"]').last().setInputFiles(file);await page.getByText('确定',{exact:true}).last().click();
   await page.waitForTimeout(1000);
   if((await page.locator('body').innerText()).includes('已存在要继续')){
    const inputs=page.locator('input:visible');let index=-1;
    for(let i=0;i<await inputs.count();i++){const r=await inputs.nth(i).boundingBox();if(r&&r.width>120)index=i;}
    assert(index>=0);importedName=variant.name+'V'+Date.now().toString().slice(-7);await inputs.nth(index).fill(importedName);await inputs.nth(index).press('End');await page.getByText('确定',{exact:true}).last().click();
   }
   await page.waitForFunction(old=>location.hash!==old,old,{timeout:60000});
   await page.getByText(importedName,{exact:true}).filter({visible:true}).waitFor({timeout:30000});
   await page.getByText('逻辑设计',{exact:true}).first().waitFor();await page.waitForTimeout(1500);
   const kind=variant.kind||variant.id;
   if(kind==='answer')await page.screenshot({path:path.join(images,'designer.png')});
   await page.getByText('逻辑设计',{exact:true}).first().click();await page.waitForTimeout(1200);
   // A new hash precedes asynchronous project and Blockly loading.
   // Wait for the expected document, then retain the independent bad-block checks.
   await page.waitForFunction(count=>typeof Blockly!=='undefined'&&Blockly.getMainWorkspace()&&Blockly.getMainWorkspace().getAllBlocks(false).length===count,variant.blockCount,{timeout:45000});
   const state=await page.evaluate(()=>{
    const w=Blockly.getMainWorkspace();
    return {blocks:w.getAllBlocks(false).length,top:w.getTopBlocks(false).map(b=>({id:b.id,type:b.type,text:b.toString()})),bad:w.getAllBlocks(false).filter(b=>typeof b.isBadBlock==='function'&&b.isBadBlock()).map(b=>({id:b.id,type:b.type,text:b.toString()})),empty:w.getAllBlocks(false).flatMap(b=>b.inputList.filter(i=>i.connection&&!i.connection.targetBlock()).map(i=>({block:b.id,type:b.type,input:i.name}))) };
   });
   const record={name:variant.name,kind,projectId:new URL(page.url()).hash.slice(1),...state};report.projects.push(record);
   save('blocks '+variant.name+': '+state.blocks);
   assert.equal(state.bad.length,0,'Bad blocks '+JSON.stringify(state.bad));
   if(variant.blockCount!==undefined)assert.equal(state.blocks,variant.blockCount,'Block count');
   if(kind==='starter')assert.equal(state.blocks,0);
   if(kind==='answer'){
    fs.writeFileSync(path.join(images,'blocks-all.json'),JSON.stringify(state.top,null,2));
    const captures=spec.captureGroups?.length?spec.captureGroups.map(g=>({id:state.top.find(b=>b.id===g.blockId)?.id||state.top[g.topLevelIndex]?.id,index:g.blockIndex,target:g.target})):state.top.map((b,i)=>({id:b.id,index:i+1,target:b.text}));
    fs.writeFileSync(path.join(images,'blocks.json'),JSON.stringify(captures,null,2));
    for(const capture of captures){
     const id=capture.id;assert(id,'Missing requested block screenshot '+capture.target);
     await require('./capture-block.cjs')(page,id,path.join(images,'block-'+String(capture.index).padStart(2,'0')+'.png'));
    }
    await page.evaluate(()=>{const w=Blockly.getMainWorkspace();w.setScale(.55);w.scroll(0,0)});
    await page.screenshot({path:path.join(images,'editor.png')});
    await page.getByText('打包 ▾',{exact:true}).click();await page.getByText('打包为.apk格式',{exact:false}).click();
    save('building '+variant.name);
    const started=Date.now();
    const checkpoint=setInterval(()=>page.screenshot({path:path.join(reportDir,'building.png')}).catch(()=>{}),15000);
    try{await page.locator('a.download-button').waitFor({timeout:180000});}
    catch(e){report.buildMessage=(await page.locator('body').innerText()).slice(-7000);throw e;}
    finally{clearInterval(checkpoint);}
    const href=await page.locator('a.download-button').getAttribute('href');const response=await page.request.get(new URL(href,page.url()).href);assert(response.ok());
    const apk=await response.body();fs.writeFileSync(path.join(dir,variant.name+'.apk'),apk);record.apk={file:variant.name+'.apk',bytes:apk.length,seconds:(Date.now()-started)/1000};
    await page.getByText('放弃',{exact:true}).last().click();await page.waitForTimeout(1000);await page.keyboard.press('Escape');await page.waitForTimeout(500);
   }
  }
  report.passed=true;
 }catch(e){report.failure=e.stack;throw e;}
 finally{report.finished=new Date().toISOString();fs.writeFileSync(path.join(reportDir,'native.json'),JSON.stringify(report,null,2));await page.screenshot({path:path.join(reportDir,'last.png')}).catch(()=>{});await browser.close();}
 console.log(JSON.stringify({lesson,passed:report.passed,variants:report.projects.map(x=>({name:x.name,blocks:x.blocks,bad:x.bad.length,apk:x.apk}))}));
})().catch(e=>{console.error(e);process.exitCode=1});

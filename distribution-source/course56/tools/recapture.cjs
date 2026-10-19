const fs=require('fs'),path=require('path'),assert=require('assert'),crypto=require('crypto');
const {chromium}=require('playwright');const capture=require('./capture-block.cjs');
const HERE=path.resolve(__dirname,'..'),base=JSON.parse(fs.readFileSync(path.join(HERE,'services.json'))).url;
const sha=f=>crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 const p=await browser.newPage({viewport:{width:1800,height:1200},deviceScaleFactor:2});p.on('dialog',d=>d.accept());
 try{
  for(let i=0;i<3;i++){
   await p.goto(base+'login');if(await p.locator('#username').count()){await p.locator('#username').fill('Course56');await Promise.all([p.waitForNavigation(),p.getByRole('button',{name:'进入工作区'}).click()]);}
   if(!(await p.locator('body').innerText()).includes('Error 403'))break;
  }
  await p.getByText('项目 ▾',{exact:true}).waitFor();await p.waitForTimeout(2000);
  for(const n of process.argv.slice(2).map(Number)){
   const key='lesson'+String(n).padStart(2,'0'),folder=path.join(HERE,'screenshots',key);
   const proof=JSON.parse(fs.readFileSync(path.join(HERE,'validation',key,'native.json')));assert(proof.passed);
   const answer=proof.projects.find(x=>x.kind==='answer');
   await p.getByText('我的项目',{exact:true}).first().click();
   const row=p.locator('.ode-ProjectRow[data-exporturl$="/'+answer.projectId+'"] .ode-ProjectNameLabel');
   await row.waitFor({state:'visible'});await row.click();
   await p.getByText(new RegExp('^'+answer.name+'(?:V[0-9]+)?$')).filter({visible:true}).first().waitFor({timeout:45000});
   await p.waitForTimeout(1500);
   await p.getByText('逻辑设计',{exact:true}).filter({visible:true}).first().waitFor();
   await p.getByText('逻辑设计',{exact:true}).filter({visible:true}).first().click();
   await p.waitForTimeout(1200);
   try { await p.waitForFunction(count=>window.Blockly?.getMainWorkspace()?.getAllBlocks(false).length===count,answer.blocks,{timeout:45000}); }
   catch(e){console.log(JSON.stringify(await p.evaluate(()=>({url:location.href,workspaces:Object.values(Blockly.Workspace.WorkspaceDB_||{}).map(w=>({id:w.id,blocks:w.getAllBlocks(false).length,svg:w.getParentSvg?.()?.getBoundingClientRect().toJSON()})),main:Blockly.getMainWorkspace()?.getAllBlocks(false).length,body:document.body.innerText.slice(-2500)}))));await p.screenshot({path:path.join(HERE,'ui/recapture-error.png')});throw e;}
   await p.waitForFunction(()=>{const s=window.Blockly?.getMainWorkspace()?.getParentSvg()?.getBoundingClientRect();return s&&s.width>300&&s.height>300;});
   const groups=JSON.parse(fs.readFileSync(path.join(folder,'blocks.json'))),files=[];
   for(const g of groups){
    const f=path.join(folder,'block-'+String(g.index).padStart(2,'0')+'.png'),old=sha(f);
    const rect=await capture(p,g.id,f);files.push({file:path.basename(f),changed:old!==sha(f),rect});
   }
   fs.writeFileSync(path.join(folder,'full-capture.json'),JSON.stringify({passed:true,projectId:answer.projectId,files},null,2));
   console.log('L'+n+' full block images captured; changed '+files.filter(x=>x.changed).length);
  }
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});

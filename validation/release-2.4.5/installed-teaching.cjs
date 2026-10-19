const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert');
const {chromium}=require('C:/Users/Yuxuan/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const [root,base,out]=process.argv.slice(2);const catalog=JSON.parse(fs.readFileSync(path.join(root,'server/war/static/teaching/catalog.json')));
(async()=>{const b=await chromium.launch({channel:'chrome',headless:true});const p=await b.newPage({viewport:{width:1440,height:950}});const report={ok:false,errors:[]};p.on('dialog',d=>d.accept());p.on('pageerror',e=>report.errors.push(e.message));
try{
 for(let i=0;i<3;i++){await p.goto(base+'login');if(await p.locator('#username').count()){await p.locator('#username').fill('Installed245');await Promise.all([p.waitForNavigation(),p.getByRole('button',{name:'进入工作区'}).click()]);}if(!(await p.locator('body').innerText()).includes('Error 403'))break;}
 await p.getByText('我的项目',{exact:true}).first().waitFor();await p.waitForTimeout(1800);await p.getByText('我的项目',{exact:true}).first().click();
 await p.getByRole('button',{name:'切换到教学项目',exact:true}).click();assert.equal(await p.locator('[data-stage-folder]').count(),8);await p.screenshot({path:path.join(out,'installed-teaching.png')});
 assert.equal(catalog.stages.flatMap(s=>s.lessons).length,56);assert.equal(catalog.stages.flatMap(s=>s.lessons.flatMap(l=>l.projects)).length,168);
 const last=catalog.stages.at(-1).lessons.at(-1);for(const m of last.materials){const r=await p.request.get(base+m.url);assert.equal(r.status(),200);assert.equal(crypto.createHash('sha256').update(await r.body()).digest('hex'),m.sha256);}
 await p.locator('[data-stage-folder="01"]').click();await p.locator('[data-lesson-folder="1"]').click();await p.locator('[data-teaching-project="starter"] button').click();await p.getByText('逻辑设计',{exact:true}).first().waitFor();await p.getByText('逻辑设计',{exact:true}).first().click();
 await p.waitForFunction(()=>window.Blockly?.getMainWorkspace());assert.equal(await p.evaluate(()=>Blockly.getMainWorkspace().getAllBlocks(false).length),0);assert(!await p.locator('.yx-curriculum-pane').isVisible());assert.deepEqual(report.errors,[]);
 report.ok=true;report.catalog={lessons:56,projects:168};report.starterImport=true;report.lastLessonDownloads=true;
}catch(e){report.failure=e.stack;throw e;}finally{fs.writeFileSync(path.join(out,'installed-teaching.json'),JSON.stringify(report,null,2));await b.close();}console.log('PASS installed 56-course library, material hashes, starter import and editor visibility');})().catch(e=>{console.error(e);process.exitCode=1});

const fs=require('fs'),path=require('path'),assert=require('assert'),crypto=require('crypto');
const {chromium}=require('playwright');
const HERE=path.resolve(__dirname,'..'),base=JSON.parse(fs.readFileSync(path.join(HERE,'services.json'))).url;
const expected=JSON.parse(fs.readFileSync(path.resolve(HERE,'../teaching-projects/catalog.json')));
const folder=path.join(HERE,'ui');fs.mkdirSync(folder,{recursive:true});
const report={layouts:[],courses:[],imports:[],errors:[]};
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});const p=await browser.newPage({viewport:{width:1600,height:1000}});
 p.on('dialog',d=>d.accept());p.on('pageerror',e=>report.errors.push(e.message));
 async function library(stage,lesson){
  await p.getByText('我的项目',{exact:true}).first().click();
  await p.getByRole('button',{name:'切换到教学项目',exact:true}).click();
  await p.locator('.yx-teaching-breadcrumb .yx-crumb').first().click();
  if(stage)await p.locator(`[data-stage-folder="${stage}"]`).click();
  if(lesson)await p.locator(`[data-lesson-folder="${lesson}"]`).click();
 }
 try{
  for(let i=0;i<3;i++){
   await p.goto(base+'login');if(await p.locator('#username').count()){await p.locator('#username').fill('CourseUI56');await Promise.all([p.waitForNavigation(),p.getByRole('button',{name:'进入工作区'}).click()]);}
   if(!(await p.locator('body').innerText()).includes('Error 403'))break;
  }
  await p.getByText('我的项目',{exact:true}).first().waitFor();await p.waitForTimeout(2500);
  await library();assert.equal(await p.locator('[data-stage-folder]').count(),8);
  for(const stage of expected.stages){
   await p.locator(`[data-route-stage="${stage.id}"]`).click();
   assert.deepEqual(await p.locator('[data-lesson-folder] .yx-folder-name').allTextContents(),stage.lessons.map(l=>l.name));
   for(const lesson of stage.lessons){
    await p.locator(`[data-lesson-folder="${lesson.id}"]`).click();assert.equal(await p.locator('[data-teaching-project]').count(),3);
    assert.equal(await p.locator('.yx-material-link').count(),lesson.materials.length);
    report.courses.push({id:lesson.id,projects:3,materials:lesson.materials.length});
    await p.locator('.yx-back-link').click();
   }
  }
  for(const width of [1600,1440,1100,960,720]){
   await p.setViewportSize({width,height:900});await library();await p.waitForTimeout(150);
   for(const view of ['root','lesson']){
    if(view==='lesson'){await p.locator('[data-stage-folder="01"]').click();await p.locator('[data-lesson-folder="1"]').click();}
    const layout=await p.locator('.yx-teaching-browser').evaluate(el=>{
     const rect=s=>el.querySelector(s).getBoundingClientRect().toJSON();
     return {panel:el.getBoundingClientRect().toJSON(),left:rect('.yx-library-pane'),right:rect('.yx-curriculum-pane'),cut:[...el.querySelectorAll('.yx-folder-name,.yx-route-title,.yx-template h2,.yx-view-tab,.yx-material-link')].filter(e=>e.clientWidth+2<e.scrollWidth).map(e=>e.textContent)};
    });
    assert.deepEqual(layout.cut,[]);assert(layout.panel.right<=width+1);
    if(width>760){const ratio=layout.left.width/layout.panel.width;assert(Math.abs(ratio-(view==='lesson'&&width>=1200?.575:.5))<.01);}
    report.layouts.push({width,view,...layout});await p.screenshot({path:path.join(folder,`teaching-${view}-${width}.png`)});
   }
  }
  await p.setViewportSize({width:1600,height:1000});
  for(const [stage,n,kind] of [['01',1,'starter'],['07',46,'answer'],['08',56,'class']]){
   await library(stage,n);const spec=JSON.parse(fs.readFileSync(path.join(HERE,`aia/lesson${String(n).padStart(2,'0')}/artifact-spec.json`)));
   const v=spec.versions.find(v=>v.kind===kind);
   await p.locator(`[data-teaching-project="${kind}"] button`).click();
   await p.getByText('逻辑设计',{exact:true}).first().waitFor();await p.waitForTimeout(1500);
   assert(!await p.locator('.yx-curriculum-pane').isVisible());
   await p.getByText('逻辑设计',{exact:true}).first().click();
   await p.waitForFunction(c=>window.Blockly?.getMainWorkspace()?.getAllBlocks(false).length===c,v.blockCount,{timeout:45000});
   const bad=await p.evaluate(()=>Blockly.getMainWorkspace().getAllBlocks(false).filter(b=>b.isBadBlock?.()).map(b=>b.id));assert.deepEqual(bad,[]);
   const id=new URL(p.url()).hash.slice(1);assert(id);report.imports.push({lesson:n,kind,id,blocks:v.blockCount});
   await library(stage,n);await p.locator(`[data-teaching-project="${kind}"] button`).click();
   await p.waitForFunction(id=>location.hash==='#'+id,id);report.imports.at(-1).sameCopyReopened=true;
  }
  await p.getByText('我的项目',{exact:true}).first().click();await p.getByRole('button',{name:'切换到我的项目',exact:true}).click();
  assert(!await p.locator('.yx-curriculum-pane').isVisible());
  const newFolder=p.getByText('新建文件夹',{exact:true}).first();assert(await newFolder.isVisible());
  fs.writeFileSync(path.join(folder,'project-toolbar.html'),await newFolder.evaluate(e=>e.parentElement.parentElement.outerHTML));
  await p.screenshot({path:path.join(folder,'projects-after.png')});
  const size=await p.getByRole('button',{name:'切换到教学项目',exact:true}).boundingBox();assert(size.width>=86&&size.width<=160&&size.height>=34&&size.height<=44);report.tabSize=size;
  await p.getByText('查看回收站',{exact:true}).first().click();await p.locator('[data-yuxuan-project-box="trash"]').waitFor();assert(!await p.locator('.yx-curriculum-pane').isVisible());report.hiddenInTrash=true;
  assert.deepEqual(report.errors,[]);report.passed=true;
 }catch(e){report.failure=e.stack;await p.screenshot({path:path.join(folder,'teaching-error.png')});throw e;}
 finally{fs.writeFileSync(path.join(folder,'teaching-ui.json'),JSON.stringify(report,null,2));await browser.close();}
 console.log(JSON.stringify({passed:report.passed,courses:report.courses.length,layouts:report.layouts.length,imports:report.imports}));
})().catch(e=>{console.error(e);process.exitCode=1});

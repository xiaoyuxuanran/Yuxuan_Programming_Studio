const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert');
const {chromium}=require('playwright');
const HERE=path.resolve(__dirname,'..'),base=JSON.parse(fs.readFileSync(path.join(HERE,'services.json'))).url;
(async()=>{const b=await chromium.launch({channel:'chrome',headless:true});const p=await b.newPage({viewport:{width:1440,height:950}});const out={downloads:[],folders:[]};
try{
 for(let i=0;i<3;i++){await p.goto(base+'login');if(await p.locator('#username').count()){await p.locator('#username').fill('CourseUI56');await Promise.all([p.waitForNavigation(),p.getByRole('button',{name:'进入工作区'}).click()]);}if(!(await p.locator('body').innerText()).includes('Error 403'))break;}
 await p.getByText('我的项目',{exact:true}).first().waitFor();await p.waitForTimeout(1800);
 const previous=JSON.parse(fs.readFileSync(path.join(HERE,'ui/final-ui.json')));
 const catalog=JSON.parse(fs.readFileSync(path.resolve(HERE,'../teaching-projects/catalog.json')));
 for(const lesson of catalog.stages.flatMap(s=>s.lessons))for(const m of [...lesson.projects,...lesson.materials]){
  const prior=previous.downloads.find(d=>d.lesson===lesson.id&&d.file===m.file);if(prior){out.downloads.push(prior);continue;}
  const r=await p.request.get(base+m.url);assert.equal(r.status(),200);const bytes=await r.body();assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),m.sha256,m.file);out.downloads.push({lesson:lesson.id,file:m.file,bytes:bytes.length});
 }
 await p.getByText('我的项目',{exact:true}).first().click();
 const personal=p.getByRole('button',{name:'切换到我的项目',exact:true});if(await personal.getAttribute('aria-pressed')!=='true')await personal.click();
 const title=p.locator('[data-yuxuan-project-toolbar] .ya-ProjectName:visible');assert.equal(await title.evaluate(e=>getComputedStyle(e).color),'rgb(33, 83, 115)');out.toolbarLabelVisible=true;
 const name='课程验收文件夹'+Date.now();await p.getByText('新建文件夹',{exact:true}).first().click();await p.getByRole('button',{name:'确定',exact:true}).waitFor();
 const input=p.getByRole('textbox').first();fs.writeFileSync(path.join(HERE,'ui/folder-dialog.html'),await input.evaluate(e=>e.parentElement.parentElement.parentElement.outerHTML));
 await input.fill(name);await p.getByRole('button',{name:'确定',exact:true}).click();
 await p.getByText(name,{exact:true}).first().waitFor();out.folders.push({name,created:true});
 const toggle=p.getByText(name,{exact:true}).locator('xpath=ancestor::div[contains(@class,"ode-ExpandButtonFocusPanel")]');
 const children=toggle.locator('xpath=../following-sibling::div[contains(@class,"ode-ProjectFolderList")]');
 assert.equal(await children.evaluate(e=>getComputedStyle(e).display),'none');await toggle.click();assert.notEqual(await children.evaluate(e=>getComputedStyle(e).display),'none');await toggle.click();assert.equal(await children.evaluate(e=>getComputedStyle(e).display),'none');out.folderCollapse=true;
 const sort=p.getByRole('button',{name:'Sort by project name',exact:true});await sort.click();assert.equal(await sort.getAttribute('aria-sort'),'ascending');await sort.click();assert.equal(await sort.getAttribute('aria-sort'),'descending');out.nativeSorting=true;
 fs.writeFileSync(path.join(HERE,'ui/folders-dom.html'),await p.locator('.ode-ProjectTable').evaluate(e=>e.outerHTML));
 for(const width of [1440,960,720]){await p.setViewportSize({width,height:950});await p.screenshot({path:path.join(HERE,`ui/personal-final-${width}.png`)});}
 out.passed=true;
}catch(e){out.failure=e.stack;await p.screenshot({path:path.join(HERE,'ui/final-error.png')});throw e;}finally{fs.writeFileSync(path.join(HERE,'ui/final-ui.json'),JSON.stringify(out,null,2));await b.close();}console.log(JSON.stringify({passed:out.passed,downloads:out.downloads.length,folders:out.folders}));})().catch(e=>{console.error(e);process.exitCode=1});

const fs=require('fs'),path=require('path');
const {chromium}=require('C:/Users/Yuxuan/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true});const page=await browser.newPage();const report={layouts:[]};
try{
 await page.goto('http://127.0.0.1:8768/#'+'1'.repeat(64));await page.getByText('服务已就绪',{exact:false}).waitFor();
 for(const width of [1440,1024,768,550]){await page.setViewportSize({width,height:900});report.layouts.push(await page.evaluate(()=>({width:innerWidth,overflow:document.documentElement.scrollWidth>innerWidth,cards:[...document.querySelectorAll('.board-card h3')].map(e=>({text:e.textContent,clipped:e.scrollWidth>e.clientWidth||e.scrollHeight>e.clientHeight}))})));}
 await page.setViewportSize({width:1440,height:1000});await page.locator('[data-board="arduino_avr"]').click();await page.waitForTimeout(4000);
 const frame=page.frames().find(f=>f.url().includes('/boards/index.html'));await frame.locator('body').click({position:{x:700,y:300}});await page.keyboard.press('Control+m');await frame.getByText('PS2 Controller',{exact:true}).waitFor({timeout:30000});
 report.cloudDialog={ok:true,text:(await frame.locator('body').innerText()).slice(-1400)};await page.screenshot({path:path.join(__dirname,'web-cloud-libraries.png'),fullPage:true});
 report.ok=report.layouts.every(l=>!l.overflow&&l.cards.every(c=>!c.clipped));
}finally{fs.writeFileSync(path.join(__dirname,'layout-verification.json'),JSON.stringify(report,null,2));await browser.close();}console.log(JSON.stringify(report));})().catch(e=>{console.error(e);process.exitCode=1});

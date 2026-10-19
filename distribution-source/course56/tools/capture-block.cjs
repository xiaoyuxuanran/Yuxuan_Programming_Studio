const assert=require('assert');
module.exports=async function captureBlock(page,id,file){
 await page.evaluate(id=>{
  const w=Blockly.getMainWorkspace();window.coursePositions={};w.setScale(1);
  for(const b of w.getTopBlocks(false)){
   const q=b.getRelativeToSurfaceXY();window.coursePositions[b.id]={x:q.x,y:q.y};
   b.getSvgRoot().style.display=b.id===id?'':'none';
  }
  const b=w.getBlockById(id),bbox=b.getSvgRoot().getBBox(),q=b.getRelativeToSurfaceXY();
  const parent=w.getParentSvg().getBoundingClientRect();
  const scale=Math.min(1,(Math.min(parent.right,innerWidth)-parent.left-110)/bbox.width,(Math.min(parent.bottom,innerHeight)-parent.top-100)/bbox.height);
  w.setScale(scale);b.moveBy(30-q.x,30-q.y);w.scroll(0,0);
  b.getSvgRoot().setAttribute('data-course-target','true');
  document.querySelectorAll('.blocklyBackpack,.blocklybackpackImage,.blocklyTrash,.blocklyZoom').forEach(x=>{x.dataset.courseVisibility=x.style.visibility;x.style.visibility='hidden';});
 },id);
 try{
  for(let i=0;i<3;i++){
   await page.waitForTimeout(70);
   const fits=await page.evaluate(()=>{
    const e=document.querySelector('[data-course-target]'),r=e.getBoundingClientRect(),w=Blockly.getMainWorkspace(),p=w.getParentSvg().getBoundingClientRect();
    const right=Math.min(p.right,innerWidth)-30,bottom=Math.min(p.bottom,innerHeight)-30;
    const ratio=Math.min(1,(right-r.left)/r.width,(bottom-r.top)/r.height);
    if(ratio<1){w.setScale(w.scale*ratio*.96);w.scroll(0,0);return false;}return true;
   });
   if(fits)break;
  }
  const rect=await page.locator('[data-course-target]').boundingBox(),v=page.viewportSize();
  assert(rect&&rect.width>0&&rect.x>=6&&rect.y>=6&&rect.x+rect.width+6<=v.width&&rect.y+rect.height+6<=v.height,'Full block must fit without clipping: '+JSON.stringify(rect));
  await page.screenshot({path:file,clip:{x:rect.x-6,y:rect.y-6,width:rect.width+12,height:rect.height+12}});
  return rect;
 }finally{
  await page.evaluate(()=>{
   const w=Blockly.getMainWorkspace();
   for(const b of w.getTopBlocks(false)){b.getSvgRoot().style.display='';const o=window.coursePositions[b.id],q=b.getRelativeToSurfaceXY();b.moveBy(o.x-q.x,o.y-q.y);b.getSvgRoot().removeAttribute('data-course-target');}
   document.querySelectorAll('[data-course-visibility]').forEach(x=>{x.style.visibility=x.dataset.courseVisibility;delete x.dataset.courseVisibility;});
  });
 }
};

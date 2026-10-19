import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {Presentation,PresentationFile,FileBlob} from '@oai/artifact-tool';
const HERE=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'), ROOT=path.resolve(HERE,'../..');
const lesson=Number(process.argv[2]),key='lesson'+String(lesson).padStart(2,'0');
const jsonPath=process.argv[3]||path.join(HERE,'content',key,'lesson.json');
const content=JSON.parse(await fs.readFile(jsonPath,'utf8'));
const OUT=path.join(ROOT,'outputs/课程案例/56课课程','No.'+String(lesson).padStart(2,'0')+content.title.replace(/[<>:"/\\|?*]/g,'：'));
const BUILD=path.join(HERE,'decks',key),IMAGES=path.join(HERE,'screenshots',key);
const SKILL='C:/Users/Yuxuan/.codex/plugins/cache/openai-primary-runtime/presentations/26.1013.11914/skills/presentations';
const PY='C:/Users/Yuxuan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe';
process.env.RUNTIME_NODE_MODULES='C:/Users/Yuxuan/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
await fs.mkdir(BUILD,{recursive:true});await fs.mkdir(OUT,{recursive:true});
const FONT='Microsoft YaHei',C={ink:'#123E62',blue:'#1388CC',muted:'#56758B',pale:'#F1F9FF',line:'#CDE6F5'};
const p=Presentation.create({slideSize:{width:1280,height:720}}),tables=[];let num=0;
function txt(s,text,x,y,w,h,size=28,color=C.ink,bold=false){
 const a=s.shapes.add({name:'text-'+s.shapes.items.length,geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 a.text=String(text);a.text.style={fontFamily:FONT,typeface:FONT,fontSize:size,color,bold,wrap:'square',autoFit:'none',insets:0,verticalAlignment:'top'};return a;
}
async function image(s,file,x,y,w,h,alt){const b=await fs.readFile(file);s.images.add({blob:b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),contentType:'image/png',alt,fit:'contain',position:{left:x,top:y,width:w,height:h}});}
function table(s,values,columnWidths){
 const cols=Math.max(...values.map(r=>r.length));values=values.map(r=>Array.from({length:cols},(_,c)=>String(r[c]??'')));
 const widths=columnWidths||(cols===2?[385,767]:cols===3?[230,380,542]:Array(cols).fill(1152/cols));
 const h=Math.min(450,Math.max(300,values.length*64));
 const t=s.tables.add({rows:values.length,columns:cols,left:64,top:174,width:1152,height:h,columnWidths:widths,values});
 t.borders.assign({fill:C.line,width:1,style:'solid'});
 for(let r=0;r<values.length;r++)for(let c=0;c<cols;c++){
  const cell=t.getCell(r,c);cell.fill=r===0?C.blue:r%2?'#FFFFFF':'#EEF7FD';
  cell.text.style={fontFamily:FONT,typeface:FONT,fontSize:values.length>7?23:25,bold:r===0,color:r===0?'#FFFFFF':C.ink,verticalAlignment:'middle',insets:12};
 }
 tables.push(num);
}
const sources=(content.sources||[]).map(s=>typeof s==='string'?s:(s.url||s.href||'')).filter(Boolean);
const cleanBody=b=>(b||[]).map(x=>typeof x==='string'?x:[x.heading||x.title,x.text||x.description].filter(Boolean).join('：'));
const authored=content.slides;
if(!Array.isArray(authored)||authored.length<20)throw new Error('Each lesson needs a substantial authored slide sequence');
const layoutLog=[];
for(const [index,slide] of authored.entries()){
 const s=p.slides.add();num++;
 s.background.fill=num%2?'#F1F9FF':'#FFFFFF';
 const body=cleanBody(slide.body),layout=slide.layout||'text';
 let title=slide.title;
 if(index===0){
  txt(s,'羽轩编程工作台 · App Inventor 课程',66,55,1100,44,25,C.blue,true);
  txt(s,'第'+lesson+'课',66,158,1070,70,48,C.blue,true);
  const coverTitle=content.coverTitle||(content.title.length>13?content.title.slice(0,12)+'\n'+content.title.slice(12):content.title);
  txt(s,coverTitle,64,252,1128,190,64,C.ink,true);
  const subtitle=content.exampleTitle||body.filter(x=>!x.startsWith('第'+lesson+'课')&&!x.startsWith('90分钟')).slice(0,2).join('\n');
  txt(s,subtitle,68,482,1110,108,30,C.ink);
  txt(s,'90分钟 · App Inventor 创意编程',68,629,1100,36,24,C.muted);
 }else{
  if(title.length>26)throw new Error('Overlong slide title '+index+': '+title);
  txt(s,title,64,46,1152,108,43,C.ink,true);
  if(layout==='table'&&slide.table){
   table(s,slide.table,slide.columnWidths);
   if(body.length)txt(s,body.slice(0,2).join('\n'),68,636,1090,62,23,C.muted);
  }else if(layout==='blocksTall'){
   const blockIndex=slide.blockIndex||1;
   await image(s,path.join(IMAGES,'block-'+String(blockIndex).padStart(2,'0')+'.png'),64,174,740,466,slide.alt||title+'的实际积木');
   txt(s,body.join('\n\n'),846,195,362,430,27,C.ink);
  }else if(layout==='blocks'){
   const blockIndex=slide.blockIndex||1;
   await image(s,path.join(IMAGES,'block-'+String(blockIndex).padStart(2,'0')+'.png'),64,179,1152,286,slide.alt||title+'的实际积木');
   txt(s,body.join('\n'),68,492,1120,156,28,C.ink);
  }else if(layout==='designer'){
   await image(s,path.join(IMAGES,'designer.png'),64,177,755,446,'实际App Inventor项目设计器');
   txt(s,body.join('\n\n'),851,187,355,430,25,C.ink);
  }else if(layout==='image'&&slide.file){
   await image(s,path.resolve(path.dirname(jsonPath),slide.file),64,174,760,450,slide.alt||title);
   txt(s,body.join('\n\n'),854,192,350,421,27,C.ink);
  }else{
   const items=body.length?body:[''];
   const available=450,gap=Math.min(140,available/items.length),size=items.length>4?27:31;
   if(items.length>6)throw new Error('Too many body rows: '+title);
   items.forEach((v,i)=>txt(s,v,68,187+i*gap,1120,gap-9,size,i===0&&layout==='question'?C.blue:C.ink,layout==='question'&&i===0));
  }
  txt(s,String(num).padStart(2,'0'),1170,672,50,25,17,C.muted);
 }
 s.speakerNotes.text=String(slide.notes||'')+(sources.length?'\n技术参考：\n'+sources.join('\n'):'');
 layoutLog.push({slide:num,title,layout,body});
}
await fs.writeFile(path.join(BUILD,'layout-content.json'),JSON.stringify(layoutLog,null,2));
const candidate=path.join(BUILD,'candidate.pptx');await(await PresentationFile.exportPptx(p)).save(candidate);
let revision=1,finalPath=path.join(OUT,'第'+String(lesson).padStart(2,'0')+'课-'+content.title.replace(/[<>:"/\\|?*]/g,'：')+'.pptx');
try{await fs.access(finalPath);finalPath=finalPath.replace('.pptx','-修订'+Date.now()+'.pptx');}catch{}
const {finalizePresentation}=await import(pathToFileURL(path.join(SKILL,'container_tools/artifact_tool_utils.mjs')).href);
const receipt=path.join(BUILD,'validation-'+Date.now()+'.json');
await finalizePresentation({workspaceDir:ROOT,candidatePath:candidate,finalPath,pythonExecutable:PY,integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...tables.flatMap(n=>['--require-native-table-slide',String(n)])],requiredNativeTableOwnerSlides:tables,fontPolicy:{basis:'design',families:[FONT]},verifyArtifactToolImport:true,receiptPath:receipt});
const final=await PresentationFile.importPptx(await FileBlob.load(finalPath));
await fs.mkdir(path.join(BUILD,'renders'),{recursive:true});
for(let i=0;i<final.slides.items.length;i++){
 const png=await final.export({slide:final.slides.items[i],format:'png',scale:1});
 await fs.writeFile(path.join(BUILD,'renders','slide-'+String(i+1).padStart(2,'0')+'.png'),new Uint8Array(await png.arrayBuffer()));
}
await fs.writeFile(path.join(BUILD,'result.json'),JSON.stringify({lesson,slides:num,path:finalPath,tables,receipt},null,2));
console.log(JSON.stringify({lesson,slides:num,path:finalPath}));
process.exitCode=0;

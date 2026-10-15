// Keep a per-environment recovery copy; explicit Save still writes the user's project.
window.addEventListener('DOMContentLoaded',()=>{
  const timer=setInterval(()=>{
    if(!window.Mixly?.Editor?.blockEditor||!Mixly.MFile||!Mixly.Electron?.File)return;
    clearInterval(timer);
    const {fs,path}=Mixly.Modules;
    const folder=path.join(Mixly.Env.clientPath,'drafts');fs.mkdirSync(folder,{recursive:true});
    const file=path.join(folder,path.basename(Mixly.Env.indexDirPath)+'.json');
    let ready=false,last='';
    try{
      if(fs.existsSync(file)){
        const draft=JSON.parse(fs.readFileSync(file,'utf8'));
        if(draft.mix){Mixly.MFile.parseMix($(draft.mix),draft.selected==='CODE',true);}
        if(draft.openedFilePath&&fs.existsSync(draft.openedFilePath)){
          Mixly.Electron.File.openedFilePath=draft.openedFilePath;
          Mixly.Electron.File.workingPath=path.dirname(draft.openedFilePath);
          Mixly.Title.updeteFilePath(draft.openedFilePath);
        }
      }
      ready=true;
    }catch(error){console.error('Mixly recovery failed',error);ready=false;}
    function save(){
      if(!ready)return;
      try{
        const value=JSON.stringify({mix:Mixly.MFile.getMix(),selected:Mixly.Editor.mainEditor.selected,openedFilePath:Mixly.Electron.File.openedFilePath});
        if(value===last)return;
        fs.writeFileSync(file+'.tmp',value);fs.renameSync(file+'.tmp',file);last=value;
      }catch(error){console.error('Mixly recovery write failed',error);}
    }
    setInterval(save,1500);
    window.addEventListener('beforeunload',save);
    Mixly.YuxuanRecovery={save,file};
  },150);
});

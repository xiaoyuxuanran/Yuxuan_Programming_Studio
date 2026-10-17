// One owner restores the workspace. The upstream 200 ms restore used to append
// its localStorage copy after this draft was loaded, doubling blocks each time.
window.YuxuanDesktopRecovery = true;
window.addEventListener('DOMContentLoaded',()=>{
  const timer=setInterval(()=>{
    if(!window.Mixly?.Editor?.blockEditor||!Mixly.MFile||!Mixly.Electron?.File)return;
    clearInterval(timer);
    const {fs,path}=Mixly.Modules;
    const folder=path.join(Mixly.Env.clientPath,'drafts');fs.mkdirSync(folder,{recursive:true});
    const file=path.join(folder,path.basename(Mixly.Env.indexDirPath)+'.json');
    let ready=false,last='';
    function finish(){ready=true;document.querySelectorAll('.loading').forEach(el=>el.remove());}
    try{
      if(fs.existsSync(file)){
        const draft=JSON.parse(fs.readFileSync(file,'utf8'));
        if(typeof draft.mix!=='string'||!$(draft.mix).filter('xml').length)throw Error('Invalid recovery draft');
        Mixly.MFile.parseMix($(draft.mix),false,true,()=>{
          if(draft.selected==='CODE'){
            const saved=$(draft.mix).filter('code').html();
            const code=typeof draft.code==='string'?draft.code:(saved?Base64.decode(saved):'');
            Mixly.Editor.mainEditor.drag.full('NEGATIVE');
            Mixly.Editor.codeEditor.setValue(code,-1);
          }
          if(draft.openedFilePath&&fs.existsSync(draft.openedFilePath)){
            Mixly.Electron.File.openedFilePath=draft.openedFilePath;
            Mixly.Electron.File.workingPath=path.dirname(draft.openedFilePath);
            Mixly.Title.updeteFilePath(draft.openedFilePath);
          }
          finish();
        });
      }else{
        // Import the legacy cache once when upgrading a desktop installation.
        Mixly.Editor.blockEditor.clear();
        restore_blocks();
        finish();
      }
    }catch(error){console.error('Mixly recovery failed',error);ready=false;document.querySelectorAll('.loading').forEach(el=>el.remove());}
    function save(){
      if(!ready)return;
      try{
        const value=JSON.stringify({mix:Mixly.MFile.getMix(),code:Mixly.Editor.codeEditor.getValue(),selected:Mixly.Editor.mainEditor.selected,openedFilePath:Mixly.Electron.File.openedFilePath});
        if(value===last)return;
        fs.writeFileSync(file+'.tmp',value);fs.renameSync(file+'.tmp',file);last=value;
        backup_blocks();
      }catch(error){console.error('Mixly recovery write failed',error);}
    }
    setInterval(save,1500);
    window.addEventListener('beforeunload',save);
    Mixly.YuxuanRecovery={save,file,get ready(){return ready;}};
  },150);
});

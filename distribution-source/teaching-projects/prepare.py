"""Preserve existing overlays; add the curriculum browser and Unicode folder validation."""
from pathlib import Path
import shutil, difflib, subprocess, json, re, sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
REPO=Path('/home/yuxuan/appinventor-dev/appinventor-sources')
APP=REPO/'appinventor/appengine';CLIENT=APP/'src/com/google/appinventor/client'
NATIVE=ROOT/'work/native'
def edit(rel,fn):
 p=CLIENT/rel;before=p.read_text(encoding='utf8');after=fn(before)
 if before!=after:p.write_text(after,encoding='utf8')
 target=HERE/'source'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
 base=subprocess.check_output(['git','show','HEAD:appinventor/appengine/src/com/google/appinventor/client/'+rel],cwd=REPO).decode('utf8')
 patch=HERE/'patches'/(Path(rel).name+'.patch');patch.parent.mkdir(exist_ok=True)
 patch.write_text(''.join(difflib.unified_diff(base.splitlines(True),after.splitlines(True),fromfile=rel,tofile=rel)),encoding='utf8')

edit('TopToolbar.java',lambda s:s if 'TeachingProjectsAction.register' in s else s.replace('com.google.appinventor.client.actions.OfflineUsbAction.register();','com.google.appinventor.client.actions.OfflineUsbAction.register();\n    com.google.appinventor.client.actions.TeachingProjectsAction.register();'))
def box(s):
 if 'data-yuxuan-teaching-host' in s:return s
 s=s.replace('import com.google.appinventor.client.widgets.boxes.Box;','import com.google.appinventor.client.widgets.boxes.Box;\nimport com.google.gwt.user.client.ui.FlowPanel;')
 s=s.replace('    setContent(plist);','''    FlowPanel teachingHost = new FlowPanel();
    teachingHost.getElement().setAttribute("data-yuxuan-teaching-host", "true");
    plist.getElement().setAttribute("data-yuxuan-personal-projects", "true");
    teachingHost.add(plist);
    setContent(teachingHost);
    getElement().setAttribute("data-yuxuan-project-box", "projects");''')
 s=s.replace('  public void loadProjectList() {','  public void loadProjectList() {\n    getElement().setAttribute("data-yuxuan-project-box", "projects");')
 s=s.replace('  public void loadTrashList() {','  public void loadTrashList() {\n    getElement().setAttribute("data-yuxuan-project-box", "trash");')
 return s
edit('boxes/ProjectListBox.java',box)

def validators(s):
 if 'isValidFolderName(String' in s:return s
 # Only folder validation changes. Project/component/asset compiler names retain their rules.
 start=s.index('  public static ProjectNameStatus checkNewFolderName(');end=s.index('\n  /**',start)
 chunk=s[start:end].replace('!isValidIdentifier(folderName)','!isValidFolderName(folderName)').replace('Window.alert(MESSAGES.malformedProjectNameError());','Window.alert("文件夹名称不能为空、不能超过100个字符，也不能包含路径或文件保留字符。");')
 s=s[:start]+chunk+s[end:]
 start=s.index('  public static String getFolderErrorMessage(');end=s.index('\n  public static String getWarningMessages(',start)
 s=s[:start]+'''  /** Folder labels are JSON UI data, not Java/YAIL identifiers or asset paths. */
  public static boolean isValidFolderName(String name) {
    if (name == null) return false;
    String trimmed = name.trim();
    if (trimmed.isEmpty() || trimmed.length() > 100 || ".".equals(trimmed) || "..".equals(trimmed)) return false;
    String forbidden = "/\\\\:*?\\\"<>|";
    for (int i = 0; i < trimmed.length(); i++) {
      char c = trimmed.charAt(i);
      if (c < 32 || c == 127 || forbidden.indexOf(c) >= 0) return false;
    }
    return true;
  }

  public static String getFolderErrorMessage(String folderName) {
    return isValidFolderName(folderName) ? "" :
        "请输入1～100个字符的文件夹名称；可用中文，不能包含 / \\\\ : * ? \\\" < > | 等保留字符。";
  }
''' +s[end:]
 start=s.index('  public static String getFolderWarningMessages(')
 s=s[:start]+'''  public static String getFolderWarningMessages(String folderName) {
    return "";
  }
}
'''
 return s
edit('youngandroid/TextValidators.java',validators)
edit('wizards/NewFolderWizard.java',lambda s:s.replace('input.getText().trim().replaceAll("( )+", " ").replace(" ", "_")','input.getText().trim()'))
shutil.copy2(HERE/'TeachingProjectsAction.java',CLIENT/'actions/TeachingProjectsAction.java')
print('Prepared teaching-project bridge, native project host and Chinese folder names.',flush=True)

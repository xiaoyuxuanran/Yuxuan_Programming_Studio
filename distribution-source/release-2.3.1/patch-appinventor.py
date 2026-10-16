"""Run inside the existing WSL checkout; retains earlier App Inventor overlays."""
from pathlib import Path
import shutil

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
repo=Path('/home/yuxuan/appinventor-dev/appinventor-sources')
app=repo/'appinventor/appengine'
client=app/'src/com/google/appinventor/client'
def edit(path,transform):
    before=path.read_text(encoding='utf-8');after=transform(before)
    (HERE/'appinventor-source').mkdir(exist_ok=True)
    path.write_text(after,encoding='utf-8');shutil.copy2(path,HERE/'appinventor-source'/path.name)

def palette(s):
    if 'qualityPaletteCategory' in s:return s
    s=s.replace('addPaletteItem(item, category);','addPaletteItem(item, qualityPaletteCategory(componentTypeName, category));')
    s=s.replace('removePaletteItem(simplePaletteItems.get(componentTypeName), category);','removePaletteItem(simplePaletteItems.get(componentTypeName), qualityPaletteCategory(componentTypeName, category));')
    s=s.replace('if (ComponentCategory.EXTENSION.equals(category)) {','if (category == null) {\n      title = "优质扩展";\n    } else if (ComponentCategory.EXTENSION.equals(category)) {')
    marker='  private void addPaletteItem(SimplePaletteItem component, ComponentCategory category) {'
    helper='''  // A null key is reserved in CollapsablePanel for the local curated category.
  private ComponentCategory qualityPaletteCategory(String name, ComponentCategory original) {
    String type = componentDatabase.getComponentType(name);
    if ("co.com.dendritas.MqttTCP.MqttTCP".equals(type)
        || "edu.mit.appinventor.ble.BluetoothLE".equals(type)
        || "com.gmail.at.moicjarod.ClientSocketAI2Ext".equals(type)) return null;
    return original;
  }

'''
    return s.replace(marker,helper+marker)
edit(client/'editor/simple/palette/AbstractPalettePanel.java',palette)

def icons(s):
    marker='  private Image getImageFromPath(String iconPath, String packageName) {'
    if 'quality/MqttTCP.png' in s:return s
    return s.replace(marker,marker+'''
    // Local icons also cover older imported copies whose remote icons disappeared.
    if ("co.com.dendritas.MqttTCP".equals(packageName)) iconPath = "/static/images/quality/MqttTCP.png";
    else if ("edu.mit.appinventor.ble".equals(packageName)) iconPath = "/static/images/quality/BluetoothLE.png";
    else if ("com.gmail.at.moicjarod".equals(packageName)) iconPath = "/static/images/quality/ClientSocketAI2Ext.png";
''')
edit(client/'editor/simple/palette/BaseComponentFactory.java',icons)
edit(client/'boxes/BlockSelectorBox.java',lambda s:s.replace('getElement().setId("yuxuan-block-selector");','getElement().setAttribute("data-yuxuan-block-selector", "true");') if 'yuxuan-block-selector' in s else s.replace('    sourceStructureExplorer = new SourceStructureExplorer();','    getElement().setAttribute("data-yuxuan-block-selector", "true");\n    sourceStructureExplorer = new SourceStructureExplorer();'))

server=app/'src/com/google/appinventor/server'
service=server/'project/youngandroid/YoungAndroidProjectService.java'
edit(service,lambda s:s if 'BundledExtensions.ensure' in s else s.replace('    // Retrieve project information\n    List<String> sourceFiles', '    com.google.appinventor.server.BundledExtensions.ensure(storageIo, userId, projectId);\n    // Retrieve project information\n    List<String> sourceFiles'))
shutil.copy2(HERE/'BundledExtensions.java',server/'BundledExtensions.java')

workspace=repo/'appinventor/blocklyeditor/src/workspace_svg.js'
def deletion(s):
    start=s.index('Blockly.WorkspaceSvg.prototype.recordDeleteAreas = function() {')
    end=s.index('Blockly.WorkspaceSvg.prototype.getBackpack',start)
    old=s[start:end]
    if 'yuxuan-block-selector' in old:
        return s.replace("var selector = window.parent.document.getElementById('yuxuan-block-selector');", "var selector = Array.prototype.filter.call(window.parent.document.querySelectorAll('[data-yuxuan-block-selector]'), function(e) { return e.offsetParent !== null && e.getAttribute('aria-hidden') !== 'true'; })[0];")
    needle='''  } else {
    this.deleteAreaToolbox_ = null;
  }
};'''
    replacement='''  } else {
    this.deleteAreaToolbox_ = null;
    // The main AI2 category panel is a GWT widget outside the Blockly iframe.
    // Reuse Blockly's delete-area handling so normal delete events and Undo apply.
    try {
      var selector = Array.prototype.filter.call(window.parent.document.querySelectorAll('[data-yuxuan-block-selector]'), function(e) { return e.offsetParent !== null && e.getAttribute('aria-hidden') !== 'true'; })[0];
      if (selector && selector.getBoundingClientRect().width > 0) {
        var r = selector.getBoundingClientRect();
        var frame = window.frameElement;
        var offset = frame ? frame.getBoundingClientRect() : {left: 0, top: 0};
        this.deleteAreaToolbox_ = new Blockly.utils.Rect(
          r.top - offset.top, r.bottom - offset.top, r.left - offset.left, r.right - offset.left);
      }
    } catch (ignored) {}
  }
};'''
    assert needle in old
    return s[:start]+old.replace(needle,replacement)+s[end:]
edit(workspace,deletion)
modern='''
// Current Blockly uses registered delete targets instead of the older rectangle cache.
Blockly.WorkspaceSvg.prototype.getDragTarget = (function(original) {
  return function(event) {
    if (!this.isMutator && !this.isFlyout && !this.yuxuanSidebarDeleteTarget_) {
      var target = new Blockly.DeleteArea();
      target.id = 'yuxuan-sidebar-delete-' + this.id;
      target.getClientRect = function() {
        try {
          var panel = Array.prototype.filter.call(window.parent.document.querySelectorAll('[data-yuxuan-block-selector]'), function(e) {
            return e.offsetParent !== null && e.getAttribute('aria-hidden') !== 'true';
          })[0];
          if (!panel) return null;
          var r = panel.getBoundingClientRect();
          if (!r.width || !r.height) return null;
          var offset = window.frameElement ? window.frameElement.getBoundingClientRect() : {left:0,top:0};
          return new Blockly.utils.Rect(r.top-offset.top,r.bottom-offset.top,r.left-offset.left,r.right-offset.left);
        } catch (ignored) { return null; }
      };
      this.getComponentManager().addComponent({component:target,weight:0,
        capabilities:[Blockly.ComponentManager.Capability.DRAG_TARGET,Blockly.ComponentManager.Capability.DELETE_AREA]});
      this.yuxuanSidebarDeleteTarget_ = target;
    }
    var area = this.yuxuanSidebarDeleteTarget_;
    var rect = area && area.getClientRect();
    if (rect && rect.contains(event.clientX,event.clientY)) return area;
    return original.call(this,event);
  };
})(Blockly.WorkspaceSvg.prototype.getDragTarget);
'''
if 'yuxuanSidebarDeleteTarget_' not in workspace.read_text(encoding='utf-8'):
    edit(workspace,lambda s:s+modern)
elif 'rect.contains(event.clientX,event.clientY)' not in workspace.read_text(encoding='utf-8'):
    edit(workspace,lambda s:s.replace('    return original.call(this,event);','    var area = this.yuxuanSidebarDeleteTarget_;\n    var rect = area && area.getClientRect();\n    if (rect && rect.contains(event.clientX,event.clientY)) return area;\n    return original.call(this,event);'))
print('Prepared curated extensions, local icons and native Blockly drag-delete area.')

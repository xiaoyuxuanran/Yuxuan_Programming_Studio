"""Apply the 2.3.2 desktop fixes after the pinned 2.0-rc4 adaptation."""
from pathlib import Path
import json,shutil
HERE=Path(__file__).resolve().parent
SRC=HERE.parent/'native/mixly/src'
def replace(path,before,after):
    p=SRC/path;s=p.read_text(encoding='utf-8')
    if after in s:return
    assert before in s,(path,before[:70])
    p.write_text(s.replace(before,after),encoding='utf-8')

replace('common/js/blockly_helper.js','function auto_save_and_restore_blocks() {','function auto_save_and_restore_blocks() {\n    if (window.YuxuanDesktopRecovery) return;')
replace('common/template/serial-tool.html','<div id="{{ d.moveId }}" style="height: 10px;width: 100%;"></div>',
'''<div id="{{ d.moveId }}" class="yuxuan-serial-header">
    <span>串口调试</span>
    <button type="button" class="yuxuan-serial-close" aria-label="关闭串口调试">关闭 ×</button>
</div>''')
replace('common/template/serial-tool.html','style="width: 100%;height: 100%;margin-top:', 'style="width: 100%;height: calc(100% - 40px);margin-top:')
replace('common/modules/mixly-modules/common/dom-operator.js','''                    const { classList } = layero[0].childNodes[1].childNodes[0];
                    classList.remove('layui-layer-close2');
                    classList.add('layui-layer-close1');''','''                    layero.addClass('yuxuan-serial-dialog');
                    layero.find('.yuxuan-serial-close').off('click.yuxuan').on('click.yuxuan', (event) => {
                        event.preventDefault();
                        event.stopPropagation();
                        serialDom.close();
                    });''')

p=SRC/'common/modules/mixly-modules/electron/cloud-download.js';s=p.read_text(encoding='utf-8')
if 'yuxuanOfficialMirror' not in s:
    end=s.rindex('});')
    p.write_text(s[:end]+(HERE/'cloud-fallback.js').read_text(encoding='utf-8')+'\n'+s[end:],encoding='utf-8')

board=SRC/'boards/default/arduino_esp32'
for name,relative in [('blocks.js','blocks/communicate.js'),('generators.js','generators/communicate.js')]:
    shutil.copy2(HERE/'bluetooth'/name,board/relative)
p=board/'xml/esp32.xml';s=p.read_text(encoding='utf-8')
if 'data-yuxuan-bluetooth' not in s:
    begin=s.index('<block type="serialBT_Init">');end=s.index('<block type="i2c_master_writer"',begin)
    s=s[:begin]+(HERE/'bluetooth/toolbox.xml').read_text(encoding='utf-8')+s[end:]
    p.write_text(s,encoding='utf-8')

meta=HERE.parent/'native/mixly/UPSTREAM.json'
data=json.loads(meta.read_text(encoding='utf-8'));data.update(suiteVersion='2.3.2',interface='desktop',fixes=['single-owner draft restore','visible accessible serial close button'])
meta.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print('Applied Mixly desktop restore and serial dialog fixes')

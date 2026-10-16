"""Restore classic ESP32 SPP blocks and correct the inherited block contracts."""
from pathlib import Path
import re

board=Path(__file__).resolve().parent/'upstream/boards/default_src/arduino_esp32'
p=board/'blocks/communicate.js'
s=p.read_text(encoding='utf-8')
s=s.replace('this.setOutput(true, "Boolean");','this.setOutput(true, Boolean);')
s=s.replace('this.setOutput(true, "Number");','this.setOutput(true, Number);')
s=s.replace('this.setOutput(true, Boolean);\n        this.setTooltip(Blockly.Msg.MIXLY_TOOLTIP_BLOCKGROUP_SERIAL_AVAILABLE);\n\n', 'this.setOutput(true, Number);\n        this.setTooltip("读取一个蓝牙字节，未收到数据时返回 -1。仅经典 ESP32 支持 SPP。");\n\n')
s=s.replace('this.appendValueInput("CONTENT", String)', 'this.appendValueInput("CONTENT")')
s=s.replace('.setCheck("String");', '.setCheck(String);')
s=s.replace('.setCheck("Number");', '.setCheck(Number);')
s=s.replace('.appendField(Blockly.Msg.MIXLY_SERIALBT_WRITE);', '.appendField("蓝牙串口 发送字节")\n            .setCheck(Number);')
if 'export const serialBT_print' not in s:
    s+='''
export const serialBT_print = {
    init: function () {
        this.setColour(COMMUNICATE_HUE);
        this.appendValueInput("CONTENT").appendField("蓝牙串口 发送文本");
        this.appendDummyInput().appendField(new Blockly.FieldDropdown([["不换行", "print"], ["换行", "println"]]), "MODE");
        this.setPreviousStatement(true); this.setNextStatement(true);
        this.setInputsInline(true);
        this.setTooltip("向蓝牙串口发送文本或数字。仅经典 ESP32 支持 SPP，不支持 ESP32-C3 / S3。");
    }
};
'''
p.write_text(s,encoding='utf-8')
p=board/'generators/communicate.js';s=p.read_text(encoding='utf-8')
s=s.replace("import { Profile } from 'mixly';", '''function ensureBluetooth(generator) {
    generator.definitions_['include_BluetoothSerial'] = '#include <BluetoothSerial.h>\\n#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED) || !defined(CONFIG_BT_SPP_ENABLED)\\n#error "Bluetooth SPP requires an original ESP32 (not ESP32-C3/S3)."\\n#endif';
    generator.definitions_['var_declare_BluetoothSerial'] = 'BluetoothSerial SerialBT;';
}''')
a=s.index('export const serialBT_Init')
s=s[:a]+'''export const serialBT_Init = function (block, generator) {
    ensureBluetooth(generator);
    const name = generator.valueToCode(block, 'CONTENT', generator.ORDER_NONE) || '"ESP32BT"';
    generator.setups_['setup_serial_BT'] = 'SerialBT.begin(' + name + ');';
    return '';
};
export const serialBT_available = function (block, generator) {
    ensureBluetooth(generator);
    return ['SerialBT.available() > 0', generator.ORDER_RELATIONAL];
};
export const serialBT_read = function (block, generator) {
    ensureBluetooth(generator);
    return ['SerialBT.read()', generator.ORDER_ATOMIC];
};
export const serialBT_write = function (block, generator) {
    ensureBluetooth(generator);
    const value = generator.valueToCode(block, 'CONTENT', generator.ORDER_NONE) || '0';
    return 'SerialBT.write((uint8_t)(' + value + '));\\n';
};
export const serialBT_print = function (block, generator) {
    ensureBluetooth(generator);
    const value = generator.valueToCode(block, 'CONTENT', generator.ORDER_NONE) || '""';
    const method = block.getFieldValue('MODE') === 'println' ? 'println' : 'print';
    return 'SerialBT.' + method + '(' + value + ');\\n';
};
'''
p.write_text(s,encoding='utf-8')
for name in ('esp32.xml',):
    p=board/'origin/xml'/name;s=p.read_text(encoding='utf-8')
    s=re.sub(r'<!--\s*<block type="serialBT_Init"[\s\S]*?</block>\s*-->', '', s, count=1)
    # Use individual toolbox blocks rather than a deeply nested old demonstration stack.
    # This gives each operation its own visible entry and keeps legacy block type IDs.
    if 'data-yuxuan-bluetooth' not in s:
        i=s.index('<block type="i2c_master_writer"')
        s=s[:i]+'''<!-- data-yuxuan-bluetooth: classic ESP32 SPP -->
  <label text="蓝牙串口 · 仅经典 ESP32（不含 C3 / S3）"></label>
  <block type="serialBT_Init"><value name="CONTENT"><shadow type="text"><field name="TEXT">ESP32BT</field></shadow></value></block>
  <block type="serialBT_available"></block>
  <block type="serialBT_read"></block>
  <block type="serialBT_write"><value name="CONTENT"><shadow type="math_number"><field name="NUM">65</field></shadow></value></block>
  <block type="serialBT_print"><value name="CONTENT"><shadow type="text"><field name="TEXT">Hello ESP32</field></shadow></value></block>
  '''+s[i:]
    p.write_text(s,encoding='utf-8')
print('Restored classic ESP32 Bluetooth toolbox; corrected read type, defaults and send operations.')

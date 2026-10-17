'use strict';
goog.provide('Blockly.Arduino.communicate');
goog.require('Blockly.Arduino');
function ensureBluetooth(generator) {
    generator.definitions_['include_BluetoothSerial'] = '#include <BluetoothSerial.h>\n#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED) || !defined(CONFIG_BT_SPP_ENABLED)\n#error "Bluetooth SPP requires an original ESP32 (not ESP32-C3/S3)."\n#endif';
    generator.definitions_['var_declare_BluetoothSerial'] = 'BluetoothSerial SerialBT;';
}

Blockly.Arduino.forBlock['spi_transfer'] = function () {
    const block=this,generator=Blockly.Arduino;
    generator.definitions_['include_SPI'] = '#include <SPI.h>';
    generator.setups_['setup_spi'] = 'SPI.begin();';
    var pin = generator.valueToCode(this, 'pin', generator.ORDER_ATOMIC);
    var value = generator.valueToCode(this, 'value', generator.ORDER_ATOMIC);
    generator.setups_['setup_output_' + pin] = 'pinMode(' + pin + ', OUTPUT);';
    var code = "digitalWrite(" + pin + ", LOW);\n";
    code += "SPI.transfer(" + value + ");\n";
    code += "digitalWrite(" + pin + ", HIGH);\n";
    return code;
}

Blockly.Arduino.forBlock['serialBT_Init'] = function () {
    const block=this,generator=Blockly.Arduino;
    ensureBluetooth(generator);
    const name = generator.valueToCode(block, 'CONTENT', generator.ORDER_NONE) || '"ESP32BT"';
    generator.setups_['setup_serial_BT'] = 'SerialBT.begin(' + name + ');';
    return '';
};
Blockly.Arduino.forBlock['serialBT_available'] = function () {
    const block=this,generator=Blockly.Arduino;
    ensureBluetooth(generator);
    return ['SerialBT.available() > 0', generator.ORDER_RELATIONAL];
};
Blockly.Arduino.forBlock['serialBT_read'] = function () {
    const block=this,generator=Blockly.Arduino;
    ensureBluetooth(generator);
    return ['SerialBT.read()', generator.ORDER_ATOMIC];
};
Blockly.Arduino.forBlock['serialBT_write'] = function () {
    const block=this,generator=Blockly.Arduino;
    ensureBluetooth(generator);
    const value = generator.valueToCode(block, 'CONTENT', generator.ORDER_NONE) || '0';
    return 'SerialBT.write((uint8_t)(' + value + '));\n';
};
Blockly.Arduino.forBlock['serialBT_print'] = function () {
    const block=this,generator=Blockly.Arduino;
    ensureBluetooth(generator);
    const value = generator.valueToCode(block, 'CONTENT', generator.ORDER_NONE) || '""';
    const method = block.getFieldValue('MODE') === 'println' ? 'println' : 'print';
    return 'SerialBT.' + method + '(' + value + ');\n';
};

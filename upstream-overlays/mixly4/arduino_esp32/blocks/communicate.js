import * as Blockly from 'blockly/core';

const COMMUNICATE_HUE = 140;

export const serialBT_Init = {
    init: function () {
        this.setColour(COMMUNICATE_HUE);
        this.appendValueInput("CONTENT")
            .appendField(Blockly.Msg.MIXLY_SERIALBT_INIT)
            .setCheck(String);
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setInputsInline(true);
        this.setTooltip(Blockly.Msg.MIXLY_TOOLTIP_SERIAL_BEGIN);
    }
};

export const serialBT_available = {
    init: function () {
        this.setColour(COMMUNICATE_HUE);
        this.appendDummyInput()
            .appendField(Blockly.Msg.MIXLY_SERIALBT_AVAILABLE);
        this.setOutput(true, Boolean);
        this.setTooltip(Blockly.Msg.MIXLY_TOOLTIP_BLOCKGROUP_SERIAL_AVAILABLE);
    }
};

export const serialBT_read = {
    init: function () {
        this.setColour(COMMUNICATE_HUE);
        this.appendDummyInput()
            .appendField(Blockly.Msg.MIXLY_SERIALBT_READ);
        this.setOutput(true, Number);
        this.setTooltip("读取一个蓝牙字节，未收到数据时返回 -1。仅经典 ESP32 支持 SPP。");

    }
};

export const serialBT_write = {
    init: function () {
        this.setColour(COMMUNICATE_HUE);
        this.appendValueInput("CONTENT")
            .appendField("蓝牙串口 发送字节")
            .setCheck(Number);
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setTooltip(Blockly.Msg.TEXT_WRITE_TOOLTIP);
    }
};
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

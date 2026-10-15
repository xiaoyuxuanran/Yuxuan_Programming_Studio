// Yuxuan local browser bridge. Mixly authors and upstream license are retained.
import * as Blockly from 'blockly/core';
import { Msg } from '../common/msg.js';
import { Boards } from '../common/boards.js';
import { LayerProgress } from '../common/layer-progress.js';
import { PluginManager } from '../common/plugin-manager.js';

export const ArduShell = {context: null, job: null};
ArduShell.setContext = context => { ArduShell.context = context; };
ArduShell.getContext = () => ArduShell.context;
ArduShell.progressLayer = new LayerProgress({width: 240, cancelValue: '停止', cancel: () => { ArduShell.kill(); return false; }});

async function api(route, data) {
    const response = await fetch('/api/' + route, {
        method: data === undefined ? 'GET' : 'POST',
        headers: {'Content-Type': 'application/json', 'X-Yuxuan-Mixly': '1'},
        body: data === undefined ? undefined : JSON.stringify(data)
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || `HTTP ${response.status}`);
    return result;
}

async function execute(upload) {
    if (ArduShell.job) return;
    const context = ArduShell.getContext();
    const manager = context.getService('StatusBarsManager');
    const terminal = manager.getStatusBarById('output');
    const editor = context.getService('EditorsManager').getActive();
    manager.show(); manager.changeTo('output');
    terminal.setValue(upload ? '正在编译并上传…\n' : '正在本机编译…\n');
    ArduShell.progressLayer.title(upload ? '编译并上传' : '本机编译');
    ArduShell.progressLayer.show();
    try {
        const files = {};
        for (const [name, content] of Object.entries(Blockly.generator.libs_ || {})) files[name] = content;
        let port = '';
        if (upload) {
            try { port = window.top.YuxuanMixly?.selectedPort() || ''; } catch (_) { /* standalone board */ }
            if (!port) throw new Error('请先在工作台上方选择 USB 串口；也可在串口面板刷新设备。');
        }
        const started = await api('arduino', {
            fqbn: Boards.getSelectedBoardCommandParam() || Boards.getSelectedBoardKey(), options: {},
            code: editor.getCode(), files, upload, port, plugins: [...PluginManager.runtimePlugins.keys()]
        });
        ArduShell.job = started.id;
        let offset = 0;
        while (ArduShell.job) {
            const result = await api('jobs/' + started.id);
            if (result.outputEnd > offset) { terminal.addValue(result.output.slice(Math.max(0, offset - (result.outputEnd - result.output.length)))); offset = result.outputEnd; }
            if (result.state !== 'running') {
                if (result.exitCode !== 0) throw new Error(result.cancelled ? '任务已停止' : `任务失败，退出码 ${result.exitCode}`);
                terminal.appendLine(upload ? '==上传成功==' : '==编译成功==');
                break;
            }
            await new Promise(resolve => setTimeout(resolve, 300));
        }
    } catch (error) {
        terminal.appendLine('\n' + String(error.message || error));
    } finally {
        ArduShell.job = null;
        ArduShell.progressLayer.hide();
    }
}
ArduShell.compile = () => execute(false);
ArduShell.upload = () => execute(true);
ArduShell.kill = async () => { if (ArduShell.job) await api('jobs/' + ArduShell.job + '/stop', {}); };

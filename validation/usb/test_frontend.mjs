// Executes the production USB panel in a small DOM fixture. No production hooks.
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import vm from 'node:vm';

const here = dirname(fileURLToPath(import.meta.url));
const sourcePath = resolve(here, '../appinventor-ui/offline-usb.js');
const source = readFileSync(sourcePath, 'utf8');
const flush = () => new Promise(resolve => setImmediate(resolve));
const readyDevice = {serial:'USB012', state:'device', model:'Test phone', label:'Test phone · USB012'};

function fixture(options = {}) {
  const nodes = new Map(), requests = [], builds = [], timeouts = new Map(), intervals = new Map();
  let counter = 0, timerId = 0, acceptBuild = true;
  class Element {
    constructor(tag = 'div') {
      this.tag = tag; this.children = []; this.handlers = new Map();
      this.disabled = false; this.hidden = false; this.value = '';
      this.textContent = ''; this.attributes = new Map(); this.classes = new Set();
      this.scrollTop = 0; this.scrollHeight = 100;
      this.classList = {toggle:(key, value) => value ? this.classes.add(key) : this.classes.delete(key)};
    }
    set id(value) { this.identity = value; nodes.set(value, this); }
    get id() { return this.identity; }
    set innerHTML(html) {
      this.html = html;
      for (const match of html.matchAll(/<(\w+)[^>]*\bid="([^"]+)"[^>]*>/g)) {
        const child = new Element(match[1]); child.id = match[2];
        child.disabled = /\bdisabled(?:\s|>)/.test(match[0]);
        this.children.push(child);
      }
    }
    querySelector(selector) { return selector.startsWith('#') ? nodes.get(selector.slice(1)) : null; }
    appendChild(child) { this.children.push(child); }
    replaceChildren(...children) { this.children = children; this.value = ''; }
    add(option) { assert.equal(option.tag, 'option', 'select.add must receive an HTML option element'); this.children.push(option); if (this.children.length === 1) this.value = option.value; }
    setAttribute(key, value) { this.attributes.set(key, value); }
    addEventListener(type, handler) { this.handlers.set(type, [...(this.handlers.get(type) || []), handler]); }
    click() { if (!this.disabled) for (const handler of this.handlers.get('click') || []) handler({target:this}); }
    change(value) { if (!this.disabled) { this.value = value; for (const handler of this.handlers.get('change') || []) handler({target:this}); } }
    focus() {}
  }
  class Option extends Element {
    constructor(text, value) { super('option'); this.textContent = text; this.value = value; }
  }
  const header = new Element(), body = new Element();
  const document = {
    readyState:'complete', body, documentElement:new Element(),
    querySelector:selector => selector === '.ode-TopPanel' ? header : null,
    createElement:tag => new Element(tag), addEventListener() {}
  };
  const window = {OfflineAppInventor:{buildForUsb:ticket => {builds.push(ticket); return acceptBuild;}}, addEventListener() {}};
  const context = vm.createContext({document, window, Option:options.globalOption || Option, URL,
    location:{href:'http://127.0.0.1:8888/?locale=en', origin:'http://127.0.0.1:8888'},
    crypto:{randomUUID:() => 'ticket-' + ++counter},
    MutationObserver:class {observe() {} disconnect() {}},
    setTimeout:(handler, delay) => {const id = ++timerId; timeouts.set(id, handler); return id;},
    clearTimeout:id => timeouts.delete(id),
    setInterval:handler => {const id = ++timerId; intervals.set(id, handler); return id;},
    fetch:(url, options) => new Promise((resolve, reject) => {
      requests.push({url, options, settled:false,
        reply(body, status=200) {this.settled = true; resolve({ok:status < 400, status, json:async () => body});},
        reject(error) {this.settled = true; reject(error);}});
    })
  });
  vm.runInContext(source, context, {filename:sourcePath});
  return {
    nodes, requests, builds, timeouts, intervals, window,
    get:(id) => nodes.get('yx-usb-' + id),
    pending:(path) => requests.find(request => !request.settled && request.url === '/ode/usb/' + path),
    set acceptBuild(value) {acceptBuild = value;}
  };
}

async function initial(f = fixture()) {
  assert.equal(f.get('run').disabled, true);
  f.pending('devices').reply({devices:[readyDevice], hint:''});
  await flush();
  assert.equal(f.get('run').disabled, false);
  return f;
}

async function installSuccess(f, ticket) {
  const callback = f.window.offlineUsbBuildReady(ticket,
    'http://127.0.0.1:8888/ode/download/project-output/123/Android');
  await flush();
  const request = f.pending('install');
  assert.ok(request);
  assert.equal(request.options.headers['X-Offline-Usb'], '1');
  assert.equal(request.options.credentials, 'same-origin');
  assert.deepEqual(JSON.parse(request.options.body), {serial:'USB012', downloadPath:'/ode/download/project-output/123/Android'});
  request.reply({job:'abc'});
  await flush();
  f.pending('job?id=abc').reply({state:'done', stage:'安装完成', output:'Success', package:'appinventor.ai_test.UsbTest'});
  await callback;
  return f;
}

const results = [];
async function test(name, action) {
  await action(); results.push({name, passed:true}); console.log('PASS ' + name);
}

await test('successful build installs chosen device and enables app logs', async () => {
  const f = await initial();
  f.get('run').click();
  assert.equal(f.get('run').disabled, true);
  assert.equal(f.get('devices').disabled, true);
  assert.equal(f.get('refresh').disabled, true);
  await installSuccess(f, f.builds[0]);
  assert.equal(f.get('run').disabled, false);
  assert.equal(f.get('logs').disabled, false);
  assert.equal(f.get('output').textContent, 'Success');
  assert.match(f.get('status').textContent, /已安装并启动/);
});

await test('build failure and refusal restore controls without installing', async () => {
  const f = await initial();
  f.get('run').click();
  f.window.offlineUsbBuildFailed(f.builds[0], 'YAIL 构建失败');
  assert.equal(f.get('run').disabled, false);
  assert.equal(f.get('devices').disabled, false);
  assert.equal(f.get('logs').disabled, true);
  assert.equal(f.get('status').textContent, 'YAIL 构建失败');
  assert.equal(f.pending('install'), undefined);
  f.acceptBuild = false;
  f.get('run').click();
  assert.equal(f.get('run').disabled, false);
  assert.match(f.get('status').textContent, /可编辑的项目/);
});

await test('failed device installation preserves error output and permits retry', async () => {
  const f = await initial();
  f.get('run').click();
  const callback = f.window.offlineUsbBuildReady(f.builds[0], '/ode/download/project-output/123/Android');
  await flush();
  f.pending('install').reply({job:'bad'});
  await flush();
  f.pending('job?id=bad').reply({state:'failed', output:'INSTALL_FAILED_USER_RESTRICTED', stage:'安装失败'});
  await callback;
  assert.equal(f.get('run').disabled, false);
  assert.equal(f.get('logs').disabled, true);
  assert.equal(f.get('output').textContent, 'INSTALL_FAILED_USER_RESTRICTED');
  f.get('run').click();
  assert.equal(f.builds.length, 2);
});

await test('pending device response cannot reenable controls during build', async () => {
  const f = await initial();
  f.get('refresh').click();
  const oldRefresh = f.pending('devices');
  f.get('run').click();
  const status = f.get('status').textContent;
  oldRefresh.reply({devices:[], hint:'No device'});
  await flush();
  assert.equal(f.get('run').disabled, true);
  assert.equal(f.get('devices').disabled, true);
  assert.equal(f.get('devices').value, 'USB012');
  assert.equal(f.get('status').textContent, status);
  await installSuccess(f, f.builds[0]);
});

await test('pending device error cannot overwrite current build state', async () => {
  const f = await initial();
  f.get('refresh').click();
  const oldRefresh = f.pending('devices');
  f.get('run').click();
  const status = f.get('status').textContent;
  oldRefresh.reject(new Error('old device refresh failed'));
  await flush();
  assert.equal(f.get('run').disabled, true);
  assert.equal(f.get('status').textContent, status);
});

await test('out-of-order device refresh cannot replace a newer selected device', async () => {
  const f = await initial();
  f.get('refresh').click();
  const first = f.pending('devices');
  f.get('refresh').click();
  const second = f.requests.find(request => !request.settled && request !== first);
  second.reply({devices:[{...readyDevice, serial:'USB999', label:'New phone'}]});
  await flush();
  first.reply({devices:[]});
  await flush();
  assert.equal(f.get('devices').value, 'USB999');
  assert.equal(f.get('run').disabled, false);
});

await test('stale log response cannot replace new run output or enable log button', async () => {
  const f = await initial();
  f.get('run').click();
  await installSuccess(f, f.builds[0]);
  f.get('logs').click();
  const oldLog = f.pending('logcat?serial=USB012&package=appinventor.ai_test.UsbTest');
  assert.ok(oldLog);
  f.get('run').click();
  const output = f.get('output').textContent, status = f.get('status').textContent;
  oldLog.reply({output:'STALE LOG DATA'});
  await flush();
  assert.equal(f.get('output').textContent, output);
  assert.equal(f.get('status').textContent, status);
  assert.equal(f.get('logs').disabled, true);
  assert.equal(f.get('run').disabled, true);
});

await test('stale log failure cannot overwrite current run', async () => {
  const f = await initial();
  f.get('run').click();
  await installSuccess(f, f.builds[0]);
  f.get('logs').click();
  const oldLog = f.pending('logcat?serial=USB012&package=appinventor.ai_test.UsbTest');
  f.get('run').click();
  const status = f.get('status').textContent;
  oldLog.reject(new Error('STALE LOG ERROR'));
  await flush();
  assert.equal(f.get('status').textContent, status);
  assert.equal(f.get('logs').disabled, true);
});

await test('old ticket callbacks leave a subsequent run intact', async () => {
  const f = await initial();
  f.get('run').click();
  const old = f.builds[0];
  f.window.offlineUsbBuildFailed(old, 'first build failed');
  f.get('run').click();
  const current = f.builds[1], status = f.get('status').textContent;
  f.window.offlineUsbBuildFailed(old, 'STALE BUILD ERROR');
  await f.window.offlineUsbBuildReady(old, '/ode/download/project-output/123/Android');
  assert.equal(f.get('status').textContent, status);
  assert.equal(f.get('run').disabled, true);
  assert.equal(f.pending('install'), undefined);
  await installSuccess(f, current);
});

await test('untrusted download URL never triggers installation', async () => {
  const f = await initial();
  f.get('run').click();
  await f.window.offlineUsbBuildReady(f.builds[0], 'http://evil.test/ode/download/project-output/123/Android');
  assert.equal(f.pending('install'), undefined);
  assert.equal(f.get('run').disabled, false);
  assert.match(f.get('status').textContent, /下载地址无效/);
});

await test('no device or only unauthorized device keeps Run disabled', async () => {
  const f = fixture();
  f.pending('devices').reply({devices:[], hint:'Connect a phone'});
  await flush();
  assert.equal(f.get('run').disabled, true);
  f.get('refresh').click();
  f.pending('devices').reply({devices:[{...readyDevice, state:'unauthorized'}]});
  await flush();
  assert.equal(f.get('run').disabled, true);
  assert.equal(f.get('devices').children[0].disabled, true);
  f.get('run').click();
  assert.equal(f.builds.length, 0);
});

await test('GWT or Blockly shadowing global Option cannot break device choices', async () => {
  for (const globalOption of [function() {throw new Error('GWT Option collision');}, function() {return {};}]) {
    const f = await initial(fixture({globalOption}));
    assert.equal(f.get('devices').children[0].tag, 'option');
    assert.equal(f.get('devices').value, 'USB012');
    f.get('run').click();
    await installSuccess(f, f.builds[0]);
    assert.equal(f.get('logs').disabled, false);
  }
});

writeFileSync(resolve(here, 'frontend-acceptance.json'), JSON.stringify({
  productionSource:'work/appinventor-ui/offline-usb.js', tests:results.length, passed:true,
  scope:'Production JavaScript executed with DOM and network fixtures; no physical phone or browser visual assertions.',
  results
}, null, 2) + '\n', 'utf8');
console.log('All ' + results.length + ' production UI state tests passed.');

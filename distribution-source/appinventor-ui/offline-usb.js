/* Desktop USB testing panel. All operations go through the authenticated local servlet. */
(() => {
  'use strict';
  let panel, entry, devices, run, refresh, status, output, logs, ticket, activeSerial;
  let busy = false, timer, appPackage = '', devicePoll;
  let deviceRequest = 0;
  const labels = {queued:'等待安装', downloading:'读取 APK', installing:'安装 APK',
    launching:'启动应用', done:'已安装并启动', failed:'运行失败'};
  async function api(path, body) {
    const response = await fetch('/ode/usb/' + path, {
      method: body ? 'POST' : 'GET', credentials:'same-origin', cache:'no-store',
      headers: {'X-Offline-Usb':'1', ...(body ? {'Content-Type':'application/json'} : {})},
      ...(body ? {body:JSON.stringify(body)} : {})
    });
    let data;
    try { data = await response.json(); } catch (_) {
      throw new Error(response.status === 412 ? '工作区会话已失效，请刷新页面。' : 'USB 服务响应异常，请重新启动 App Inventor。');
    }
    if (!response.ok) throw new Error(data.error || 'USB 操作失败（' + response.status + '）');
    return data;
  }
  function show(message, failure = false) {
    status.textContent = message;
    status.classList.toggle('yx-usb-error', failure);
    entry.classList.toggle('yx-usb-busy', busy);
  }
  function setBusy(value) {
    busy = value;
    run.disabled = value || !devices.value || !window.OfflineAppInventor;
    devices.disabled = value;
    refresh.disabled = value;
    entry.classList.toggle('yx-usb-busy', value);
  }
  async function updateDevices(manual = false) {
    if (busy) return;
    const request = ++deviceRequest;
    try {
      const selected = devices.value;
      const result = await api('devices');
      if (busy || request !== deviceRequest) return;
      const choices = result.devices || [];
      devices.replaceChildren();
      for (const device of choices) {
        const option = document.createElement('option');
        option.textContent = device.label || device.model || device.serial;
        option.value = device.serial;
        option.disabled = device.state !== 'device';
        if (option.disabled) option.textContent += device.state === 'unauthorized' ? ' · 待手机授权' : ' · 离线';
        devices.add(option);
      }
      if (!choices.length) {
        const option = document.createElement('option');
        option.textContent = '未发现 USB 设备'; option.value = '';
        devices.add(option);
      }
      if (choices.some(d => d.serial === selected && d.state === 'device')) devices.value = selected;
      else {
        const ready = choices.find(d => d.state === 'device');
        devices.value = ready ? ready.serial : '';
      }
      setBusy(false);
      if (manual || !ticket) show(result.hint || (devices.value ? '设备已就绪，点击运行会保存并构建当前项目。' : '请连接手机，开启 USB 调试，并在手机上允许此电脑。'));
    } catch (e) {
      if (busy || request !== deviceRequest) return;
      show(e.message, true); run.disabled = true;
    }
  }
  function openPanel() {
    panel.hidden = !panel.hidden;
    entry.setAttribute('aria-expanded', String(!panel.hidden));
    if (!panel.hidden) { updateDevices(true); devices.focus(); }
  }
  function finish(message, failure) {
    clearTimeout(timer);
    setBusy(false);
    show(message, failure);
  }
  async function pollJob(id) {
    try {
      const job = await api('job?id=' + encodeURIComponent(id));
      output.textContent = job.output || '';
      output.scrollTop = output.scrollHeight;
      show(labels[job.stage] || job.stage || labels[job.state] || '正在运行…');
      if (job.state === 'done' || job.state === 'succeeded') {
        appPackage = job.package || '';
        logs.disabled = !appPackage;
        finish('已安装并启动。可点击“读取应用日志”查看测试结果。', false);
      } else if (job.state === 'failed' || job.state === 'error') {
        finish(job.error || '运行失败，请查看下方输出。', true);
      } else timer = setTimeout(() => pollJob(id), 700);
    } catch (e) { finish(e.message, true); }
  }
  window.offlineUsbBuildReady = async (id, downloadUrl) => {
    if (!busy || id !== ticket) return;
    try {
      const url = new URL(downloadUrl, location.href);
      if (url.origin !== location.origin || !/^\/ode\/download\/project-output\/\d+\/Android$/.test(url.pathname))
        throw new Error('构建返回的 APK 下载地址无效。');
      show('APK 已构建，正在安装到所选设备…');
      const result = await api('install', {serial:activeSerial, downloadPath:url.pathname});
      await pollJob(result.job);
    } catch (e) { finish(e.message, true); }
  };
  window.offlineUsbBuildFailed = (id, message) => {
    if (id === ticket) finish(message, true);
  };
  function startRun() {
    if (busy || !devices.value || !window.OfflineAppInventor) return;
    activeSerial = devices.value;
    ticket = crypto.randomUUID ? crypto.randomUUID() : String(Date.now());
    appPackage = ''; logs.disabled = true;
    output.textContent = '保存项目 → 构建 APK → USB 安装 → 启动应用\n';
    setBusy(true);
    show('正在保存并构建当前项目，首次构建可能需要较长时间…');
    try {
      if (!window.OfflineAppInventor.buildForUsb(ticket))
        finish('请先打开一个可编辑的项目，并等待其他构建完成。', true);
    } catch (e) { finish('无法开始构建，请刷新页面后重试。', true); }
  }
  async function readLogs() {
    if (busy || !activeSerial || !appPackage) return;
    const context = ticket, serial = activeSerial, packageName = appPackage;
    logs.disabled = true;
    try {
      const result = await api('logcat?serial=' + encodeURIComponent(serial) + '&package=' + encodeURIComponent(packageName));
      if (busy || ticket !== context || activeSerial !== serial || appPackage !== packageName) return;
      const text = result.output || result.logs || '';
      // Replace the bounded snapshot instead of duplicating log history on each click.
      output.textContent = (text ? '应用日志 · ' + appPackage + '\n' + text : '暂时没有应用日志。请先在手机上操作应用，再读取日志。');
      output.scrollTop = output.scrollHeight;
      show(result.hint || '已读取应用日志。');
    } catch (e) {
      if (!busy && ticket === context && activeSerial === serial && appPackage === packageName) show(e.message, true);
    }
    finally {
      if (!busy && ticket === context && activeSerial === serial && appPackage === packageName) logs.disabled = false;
    }
  }
  function mount() {
    if (entry || !window.OfflineAppInventor) return;
    const header = document.querySelector('.ode-TopPanel');
    if (!header) return;
    mountWatch.disconnect();
    entry = document.createElement('button');
    entry.id = 'yx-usb-entry'; entry.textContent = 'USB 调试'; entry.type = 'button';
    entry.setAttribute('aria-expanded','false'); entry.setAttribute('aria-controls','yx-usb-panel');
    entry.addEventListener('click',openPanel);
    header.appendChild(entry);
    panel = document.createElement('section');
    panel.id = 'yx-usb-panel'; panel.hidden = true;
    panel.setAttribute('aria-label','USB 设备运行与调试');
    panel.innerHTML = '<div class="yx-usb-title"><strong>USB 运行与调试</strong><button type="button" id="yx-usb-close" aria-label="关闭 USB 调试面板">×</button></div>' +
      '<p class="yx-usb-help">用数据线连接手机，打开手机的开发者选项与 USB 调试，并允许此电脑。未识别时，请安装手机厂商提供的 USB 驱动。</p>' +
      '<label for="yx-usb-devices">运行设备</label><div class="yx-usb-controls"><select id="yx-usb-devices" aria-label="选择 USB 运行设备"></select><button id="yx-usb-refresh" type="button">刷新</button><button id="yx-usb-run" type="button" disabled>▶ 运行</button></div>' +
      '<p id="yx-usb-status" role="status" aria-live="polite">正在读取设备…</p><pre id="yx-usb-output" tabindex="0" aria-label="安装和应用日志"></pre>' +
      '<div class="yx-usb-footer"><button id="yx-usb-logs" type="button" disabled>读取应用日志</button><span>运行会更新安装，并启动当前项目。</span></div>';
    document.body.appendChild(panel);
    devices = panel.querySelector('#yx-usb-devices'); run = panel.querySelector('#yx-usb-run');
    refresh = panel.querySelector('#yx-usb-refresh'); status = panel.querySelector('#yx-usb-status');
    output = panel.querySelector('#yx-usb-output'); logs = panel.querySelector('#yx-usb-logs');
    panel.querySelector('#yx-usb-close').addEventListener('click',openPanel);
    refresh.addEventListener('click',() => updateDevices(true));
    devices.addEventListener('change',() => setBusy(false));
    run.addEventListener('click',startRun); logs.addEventListener('click',readLogs);
    document.addEventListener('keydown',event => {
      if (event.key === 'Escape' && !panel.hidden) { openPanel(); entry.focus(); }
    });
    devicePoll = setInterval(() => { if (!panel.hidden) updateDevices(); },5000);
    updateDevices();
  }
  const mountWatch = new MutationObserver(mount);
  mountWatch.observe(document.documentElement,{subtree:true,childList:true});
  window.addEventListener('offline-appinventor-ready',mount);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded',mount,{once:true});
  else mount();
})();

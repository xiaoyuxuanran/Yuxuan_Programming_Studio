'use strict';
const $ = selector => document.querySelector(selector);
const environments = {arduino_avr:'Arduino AVR', arduino_esp32:'Arduino ESP32', micropython_esp32:'MicroPython ESP32', arduino_esp8266:'Arduino ESP8266'};
let currentView = 'home', serialTimer = null, serialOffset = 0, serialTail = '', toastTimer;
window.YuxuanMixly = {selectedPort: () => $('#native-port').value};
async function api(path, data) {
  const response = await fetch('/api/' + path, {method:data === undefined ? 'GET':'POST',headers:{'Content-Type':'application/json','X-Yuxuan-Mixly':'1'},body:data === undefined ? undefined:JSON.stringify(data)});
  const value = await response.json(); if (!response.ok) throw new Error(value.error || `HTTP ${response.status}`); return value;
}
function notice(text) { $('#toast').textContent=text; $('#toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').hidden=true,7000); }
function show(view) {
  document.querySelectorAll('main>.view').forEach(el=>el.hidden=el.id!==view+'-view');
  document.querySelectorAll('nav [data-view]').forEach(el=>el.classList.toggle('active',el.dataset.view===view));
  currentView=view;
  if (view==='simulation' && !$('#simulation-frame').dataset.loaded) {$('#simulation-frame').src='/editor/mixvm/index.html';$('#simulation-frame').dataset.loaded='1';}
  if(view==='serial')refreshPorts();
}
function board(ident) {
  if(!environments[ident])return;
  const frame=$('#editor-frame');
  if(frame.dataset.board!==ident) {
    if(frame.dataset.board && !confirm('切换环境前，请确认已保存当前工程。继续切换？'))return;
    frame.src='/editor/boards/index.html?boardIndex='+encodeURIComponent('./boards/default/'+ident+'/index.xml'); frame.dataset.board=ident;
  }
  $('#environment-name').textContent=environments[ident];show('editor');
}
async function refreshPorts(){
  try{const {ports}=await api('ports');const selected=$('#native-port').value;$('#native-port').replaceChildren();
    if(!ports.length)$('#native-port').add(new Option('未连接设备',''));
    for(const port of ports)$('#native-port').add(new Option(port.device+' · '+port.description,port.device));
    if(ports.some(p=>p.device===selected))$('#native-port').value=selected;
  }catch(error){notice(error.message);}
}
const samples=[];
function chart(){
  const canvas=$('#serial-chart'), ctx=canvas.getContext('2d'), w=canvas.width,h=canvas.height;
  ctx.clearRect(0,0,w,h);ctx.strokeStyle='#e9f1f7';ctx.lineWidth=1;
  for(let y=30;y<h;y+=30){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke();}
  if(samples.length<2)return;const low=Math.min(...samples),high=Math.max(...samples),range=high-low||1;
  ctx.strokeStyle='#188bd3';ctx.lineWidth=2;ctx.beginPath();samples.forEach((v,i)=>{const x=20+i*(w-40)/(samples.length-1),y=h-20-(v-low)*(h-40)/range;i?ctx.lineTo(x,y):ctx.moveTo(x,y);});ctx.stroke();
  ctx.fillStyle='#68859c';ctx.font='12px Segoe UI';ctx.fillText(high.toPrecision(5),8,16);ctx.fillText(low.toPrecision(5),8,h-5);
}
async function pollSerial(){
  try{const result=await api('serial');$('#serial-state').textContent=result.open?'串口已连接':'未连接';
    const output=result.output,end=result.outputEnd;if(end<serialOffset){serialOffset=0;serialTail='';}
    if(end>serialOffset){const next=output.slice(Math.max(0,serialOffset-(end-output.length)));$('#serial-output').textContent=($('#serial-output').textContent+next).slice(-200000);$('#serial-output').scrollTop=$('#serial-output').scrollHeight;
      const lines=(serialTail+next).split(/\r?\n/);serialTail=lines.pop().slice(-1000);
      for(const line of lines){const value=Number(line.trim());if(line.trim()&&Number.isFinite(value)){samples.push(value);if(samples.length>160)samples.shift();}}chart();serialOffset=end;
    }
    $('#serial-open').disabled=result.open;
  }catch(error){$('#serial-state').textContent=error.message;}
}
async function start(){
  const token=location.hash.slice(1);history.replaceState(null,'',location.pathname);
  try{if(token)await api('session',{token});await api('ports');document.querySelectorAll('img[data-src]').forEach(el=>el.src=el.dataset.src);$('#home-state').textContent='服务已就绪 · Mixly 4 / 羽轩 2.3.0';await refreshPorts();}
  catch(error){$('#home-state').textContent='请从启动器打开工作台';notice(error.message);document.querySelectorAll('[data-board],[data-view]').forEach(el=>el.disabled=true);return;}
  document.querySelectorAll('[data-view]').forEach(el=>el.addEventListener('click',()=>show(el.dataset.view)));
  document.querySelectorAll('[data-board]').forEach(el=>el.addEventListener('click',()=>board(el.dataset.board)));
  $('#home-brand').onclick=$('#back-home').onclick=()=>show('home');
  $('#refresh-ports').onclick=refreshPorts;
  $('#expand-editor').onclick=()=>$('#editor-frame').requestFullscreen?.().catch(error=>notice(error.message));
  $('#serial-open').onclick=async()=>{try{await api('serial/open',{port:$('#native-port').value,baud:Number($('#baud-rate').value)});serialOffset=0;$('#serial-output').textContent='';samples.length=0;chart();if(!serialTimer)serialTimer=setInterval(pollSerial,400);await pollSerial();}catch(error){notice(error.message);}};
  $('#serial-close').onclick=async()=>{try{await api('serial/close',{});await pollSerial();clearInterval(serialTimer);serialTimer=null;}catch(error){notice(error.message);}};
  $('#serial-clear').onclick=()=>{$('#serial-output').textContent='';samples.length=0;chart();};
  $('#serial-send').onsubmit=async event=>{event.preventDefault();try{await api('serial/send',{text:$('#serial-input').value+($('#serial-newline').checked?'\n':'')});$('#serial-input').value='';}catch(error){notice(error.message);}};
  chart();
  let missed=0;
  setInterval(async()=>{try{await api('ports');missed=0;}catch(error){if(++missed<3)return;document.querySelectorAll('iframe').forEach(frame=>frame.src='about:blank');document.querySelectorAll('[data-board],[data-view]').forEach(el=>el.disabled=true);$('#home-state').textContent='本机服务已结束，请从启动器重新打开';show('home');}},3000);
}
start();

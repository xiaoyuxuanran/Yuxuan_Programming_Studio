const {ipcRenderer}=require('electron');
const boards=JSON.parse(require('fs').readFileSync(require('path').join(__dirname,'boards.json'),'utf8'));
const description={'Arduino AVR':'Uno、Nano、Mega 等经典开发板','Arduino ESP8266':'Wi-Fi 物联网，从连接开始','Python ESP32':'MicroPython 积木与固件工具','Arduino ESP32':'双核 ESP32，连接更多创意'};
for(const board of boards){
  const link=document.createElement('a');link.className='board';
  const query=Object.entries({thirdPartyBoard:'false',boardIndex:board.boardIndex,boardType:board.boardType,language:board.language}).map(([key,value])=>encodeURIComponent(key)+'='+encodeURIComponent(value)).join('&');
  link.href=board.boardIndex+'?'+query;
  const image=document.createElement('img');image.src=board.boardImg;image.alt='';
  const title=document.createElement('h3');title.textContent=board.boardType;
  const text=document.createElement('p');text.textContent=description[board.boardType];
  const action=document.createElement('span');action.className='start';action.textContent='开始编程 →';
  link.append(image,title,text,action);document.querySelector('#boards').append(link);
}
const drivers=[
  ['CH340 / CH341','沁恒 WCH','常见于 Arduino 兼容板、ESP8266 与 ESP32 开发板','https://www.wch.cn/downloads/CH341SER_EXE.html'],
  ['CH343 / CH9102','沁恒 WCH','新款 ESP32、CH343 / CH910x USB 串口芯片','https://www.wch.cn/downloads/CH343SER_EXE.html'],
  ['CP210x','Silicon Labs','CP2102、CP2104 等 USB 转串口芯片','https://www.silabs.com/software-and-tools/usb-to-uart-bridge-vcp-drivers'],
  ['FT232 / FT231','FTDI','FTDI USB 串口模块与部分 Arduino 开发板','https://ftdichip.com/drivers/vcp-drivers/']
];
for(const [name,manufacturer,detail,url] of drivers){const card=document.createElement('article');card.className='driver';const title=document.createElement('h3');title.textContent=name;const maker=document.createElement('small');maker.textContent=manufacturer;const text=document.createElement('p');text.textContent=detail;const button=document.createElement('button');button.textContent='官网下载';button.dataset.url=url;card.append(title,maker,text,button);document.querySelector('#driver-list').append(card);}
document.addEventListener('click',async event=>{const button=event.target.closest('[data-url]');if(!button)return;try{await ipcRenderer.invoke('yuxuan-open-driver',button.dataset.url);}catch(error){alert('无法打开下载页：'+error.message);}});

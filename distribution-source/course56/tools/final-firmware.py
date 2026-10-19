from pathlib import Path
import subprocess,json,time
HERE=Path(__file__).resolve().parents[1]
cases=[('serial','43-serial-protocol'),('spp','44-45-classic-spp'),('ble','46-ble-led'),('ap','47-tcp-ap'),('sta','48-tcp-sta'),('reliable','49-50-tcp-reliable')]
report={'passed':False,'fqbn':'esp32:esp32:esp32','core':'2.0.17','realHardwareTested':False,'builds':[]}
try:
 for name,sketch in cases:
  cmd=['U:/arduino-cli.exe','--config-file','C:/yx56-firmware/build-short.yaml','compile','--fqbn',report['fqbn'],'--build-path','C:/yx56-firmware/build/'+name,'--build-cache-path','C:/yx56-firmware/build/cache']
  if name=='spp':cmd+=['--build-property','build.partitions=huge_app']
  cmd+=['C:/yx56-firmware/'+sketch]
  start=time.monotonic();r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',errors='replace',creationflags=subprocess.CREATE_NO_WINDOW)
  folder=HERE/'validation/firmware-build';folder.mkdir(exist_ok=True)
  (folder/(name+'.log')).write_text(r.stdout+'\n'+r.stderr,encoding='utf8')
  report['builds'].append({'sketch':sketch,'exitCode':r.returncode,'seconds':round(time.monotonic()-start,2),'summary':r.stdout[-1000:]})
  assert r.returncode==0,sketch
  print('PASS '+sketch,flush=True)
 report['passed']=True
finally:(HERE/'validation/firmware-final.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')

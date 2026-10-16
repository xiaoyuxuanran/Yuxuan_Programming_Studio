from pathlib import Path
from PIL import Image, ImageDraw
import zipfile,json,io,hashlib

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
out=HERE/'bundled-extensions';out.mkdir(exist_ok=True)
catalog=[]
for name,kind in [('MqttTCP','mqtt'),('BluetoothLE','ble'),('ClientSocketAI2Ext','socket')]:
    image=Image.new('RGBA',(64,64),(0,0,0,0));d=ImageDraw.Draw(image)
    d.rounded_rectangle((1,1,63,63),radius=15,fill='#e0f2fe',outline='#38bdf8',width=2)
    if kind=='ble':
        d.line([(29,10),(44,23),(21,43),(29,51),(29,10),(44,40),(21,21)],fill='#0284c7',width=5)
    elif kind=='mqtt':
        d.line([(17,46),(32,18),(48,46),(17,46)],fill='#0284c7',width=4)
        for x,y in [(17,46),(32,18),(48,46)]:d.ellipse((x-7,y-7,x+7,y+7),fill='#0284c7',outline='white',width=2)
    else:
        d.line([(9,32),(55,32)],fill='#0284c7',width=5)
        d.rounded_rectangle((14,23,29,42),radius=4,fill='#0284c7');d.rounded_rectangle((36,23,51,42),radius=4,fill='#0284c7')
        d.line([(28,27),(37,27)],fill='white',width=3);d.line([(28,37),(37,37)],fill='white',width=3)
    png=io.BytesIO();image.save(png,format='PNG')
    with zipfile.ZipFile(ROOT/'outputs/AIA外部扩展提取'/f'{name}.aix') as z:
        entries={f.filename:z.read(f) for f in z.infolist() if not f.is_dir()}
    descfile=next(k for k in entries if k.endswith('/components.json'));package=descfile.rsplit('/',1)[0]
    components=json.loads(entries[descfile])
    for component in components:component['iconName']='aiwebres/yuxuan-icon.png'
    entries[descfile]=json.dumps(components,ensure_ascii=False,indent=2).encode('utf-8')
    entries[package+'/aiwebres/yuxuan-icon.png']=png.getvalue()
    path=out/(name+'.aix')
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for member,raw in sorted(entries.items()):z.writestr(member,raw)
    with zipfile.ZipFile(path) as z:assert z.testzip() is None
    static=ROOT/'work/native/server/war/static/images/quality';static.mkdir(exist_ok=True)
    (static/(name+'.png')).write_bytes(png.getvalue())
    resource=ROOT/'work/native/server/war/WEB-INF/classes/bundled-extensions';resource.mkdir(exist_ok=True)
    (resource/path.name).write_bytes(path.read_bytes())
    catalog.append({'name':name,'type':components[0]['type'],'version':components[0]['version'],'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(out/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(catalog,ensure_ascii=False))

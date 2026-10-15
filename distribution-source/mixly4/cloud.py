"""Adapt the existing official Mixly library catalog to Mixly 4 plugins."""
from pathlib import Path, PurePosixPath
import hashlib
import io
import json
import re
import threading
import time
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import zipfile

BOARDS = frozenset(('arduino_avr', 'arduino_esp32', 'arduino_esp8266', 'micropython_esp32'))


class CloudLibraries:
    def __init__(self, data, context):
        self.root = Path(data) / 'cloud'
        self.root.mkdir(parents=True, exist_ok=True)
        self.context = context
        self.catalogs = {}
        self.lock = threading.RLock()

    def fetch(self, url, limit=64 * 1024 * 1024):
        parts = urlsplit(url)
        if parts.scheme not in ('https', 'http') or parts.hostname != 'download.mixlylibs.cloud' or parts.port not in (None, 80, 443) or parts.username or parts.password:
            raise ValueError('扩展库下载地址不在官方源中')
        url = 'https://' + parts.netloc.replace(':80', '') + parts.path + ('?' + parts.query if parts.query else '')
        with urlopen(Request(url, headers={'User-Agent': 'YuxuanMixlyWeb/2.3.0'}), timeout=40, context=self.context()) as response:
            if urlsplit(response.geturl()).scheme != 'https' or urlsplit(response.geturl()).hostname != 'download.mixlylibs.cloud':
                raise ValueError('扩展库下载发生不允许的跳转')
            data = response.read(limit + 1)
        if len(data) > limit:
            raise ValueError('扩展库文件过大')
        return data

    def catalog(self, board):
        if board not in BOARDS:
            raise ValueError('扩展库环境无效')
        with self.lock:
            cached = self.catalogs.get(board)
            if cached and time.monotonic() - cached[0] < 120:
                return cached[1]
            saved = self.root / (board + '.json')
            try:
                raw = self.fetch(f'https://download.mixlylibs.cloud/mixly-packages/cloud-libs/{board}/libs.json', 2 * 1024 * 1024)
                # The official legacy catalog is JSON with block comments.
                text = raw.decode('utf-8-sig')
                text = re.sub(r'"(?:\\.|[^"\\])*"|/\*[\s\S]*?\*/|//[^\r\n]*',
                              lambda m: m[0] if m[0].startswith('"') else '', text)
                values = json.loads(text)
                if not isinstance(values, list):
                    raise ValueError('官方库目录格式无效')
                saved.write_text(json.dumps(values, ensure_ascii=False), encoding='utf-8')
            except Exception:
                if not saved.is_file():
                    raise
                values = json.loads(saved.read_bytes())
            output = []
            for value in values:
                if not isinstance(value, dict) or not value.get('url'):
                    continue
                ident = 'yx-' + board + '-' + hashlib.sha256(value['url'].encode()).hexdigest()[:16]
                version = str(value.get('version') or '1.0.0')
                output.append({'id': ident, 'dir': ident, 'name': str(value.get('name') or ident),
                               'description': str(value.get('desc') or ''), 'version': version,
                               'latestVersion': version, 'versions': [version],
                               'downloadUrl': f'/api/cloud/package?board={board}&id={ident}', '_url': value['url']})
            self.catalogs[board] = (time.monotonic(), output)
            return output

    def package(self, board, ident):
        item = next((item for item in self.catalog(board) if item['id'] == ident), None)
        if not item:
            raise ValueError('所选扩展库不在官方目录中')
        cache = self.root / 'packages' / ident
        cache.mkdir(parents=True, exist_ok=True)
        target = cache / ('converted-v2-' + hashlib.sha256(item['version'].encode()).hexdigest()[:12] + '.zip')
        with self.lock:
            if target.is_file():
                return target.read_bytes()
            raw = self.fetch(item['_url'])
            result = self.convert(raw, item, cache)
            temporary = target.with_suffix('.tmp')
            temporary.write_bytes(result)
            temporary.replace(target)
            return result

    @staticmethod
    def convert(raw, item, cache):
        with zipfile.ZipFile(io.BytesIO(raw)) as original:
            members = [m for m in original.infolist() if not m.is_dir()]
            if len(members) > 10000 or sum(m.file_size for m in members) > 256 * 1024 * 1024:
                raise ValueError('扩展库解压内容过大')
            files = {}
            for member in members:
                name = member.filename.replace('\\', '/')
                path = PurePosixPath(name)
                if path.is_absolute() or '..' in path.parts or ':' in name or (member.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError('扩展库含不安全路径')
                files[name] = original.read(member)
        xml_names = [name for name in files if name.lower().endswith('.xml')]
        xml_names.sort(key=lambda name: (name.count('/'), name))
        index_name = next((name for name in xml_names if b'<script' in files[name] or b'<category' in files[name]), None)
        if not index_name:
            raise ValueError('扩展库缺少积木入口 XML；请使用新版兼容库')
        parent = str(PurePosixPath(index_name).parent)
        prefix = '' if parent == '.' else parent + '/'
        stripped = {name[len(prefix):]: value for name, value in files.items() if name.startswith(prefix)}
        xml = files[index_name].decode('utf-8-sig', 'replace')
        script_names = [next(value for value in match if value) for match in
                        re.findall(r'<script\b[^>]*\bsrc\s*=\s*(?:"([^"]+)"|\'([^\']+)\'|([^\s>]+))', xml, re.I)]
        body = []
        for name in script_names:
            key = name.removeprefix('./')
            if key not in stripped:
                raise ValueError('扩展库缺少脚本：' + key)
            source = stripped[key].decode('utf-8-sig', 'replace')
            source = re.sub(r'goog\.(?:provide|require)\([^\n]*?\);?', '', source)
            language = re.search(r'(?:^|/)(zh-hans|zh-hant|en)\.js$', key)
            if language:
                source = 'if (__language === ' + json.dumps(language[1]) + ') {\n' + source + '\n}'
            source = re.sub(r"Blockly\.(Arduino|Python)(\[[\"'][^\"']+[\"']\])\s*=", r'Blockly.\1.forBlock\2 =', source)
            body.append(source)
        code = '''const Blockly = globalThis.Blockly;
const Mixly = globalThis.Mixly;
const goog = {provide(){}, require(){}};
const __language = Mixly.Config.USER.language || 'zh-hans';
const __beforeBlocks = {...Blockly.Blocks};
const __beforeGenerators = {...Blockly.generator.forBlock};
const __beforeMessages = {...Blockly.Msg};
'''
        code += '\n'.join(body)
        code += '''
export const blocks = Object.fromEntries(Object.entries(Blockly.Blocks).filter(([k,v]) => __beforeBlocks[k] !== v));
export const generators = Object.fromEntries(Object.entries(Blockly.generator.forBlock).filter(([k,v]) => __beforeGenerators[k] !== v));
export const languages = {[__language]: {Msg: Object.fromEntries(Object.entries(Blockly.Msg).filter(([k,v]) => __beforeMessages[k] !== v))}};
for (const key of Object.keys(blocks)) { if (key in __beforeBlocks) Blockly.Blocks[key] = __beforeBlocks[key]; else delete Blockly.Blocks[key]; }
for (const key of Object.keys(generators)) { if (key in __beforeGenerators) Blockly.generator.forBlock[key] = __beforeGenerators[key]; else delete Blockly.generator.forBlock[key]; }
'''
        xml = re.sub(r'<script\b[^>]*>[\s\S]*?</script>', '', xml, flags=re.I)
        xml = '<script src="index.js"></script>\n' + xml
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as converted:
            converted.writestr('index.xml', xml.encode('utf-8'))
            converted.writestr('index.js', code.encode('utf-8'))
            converted.writestr('package.json', json.dumps({'name': item['id'], 'version': item['version'], 'description': item['description']}).encode('utf-8'))
            for name, value in stripped.items():
                if name not in ('index.xml', 'index.js', 'package.json'):
                    converted.writestr(name, value)
                suffix = PurePosixPath(name).suffix.lower()
                if suffix in ('.h', '.hpp', '.c', '.cpp', '.cxx', '.s', '.a', '.properties'):
                    relative = PurePosixPath(name)
                    if len(relative.parts) == 1:
                        relative = PurePosixPath(item['id']) / relative
                    target = cache / 'libraries' / Path(relative)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(value)
                elif suffix == '.py':
                    converted.writestr('libraries/' + name, value)
        return output.getvalue()

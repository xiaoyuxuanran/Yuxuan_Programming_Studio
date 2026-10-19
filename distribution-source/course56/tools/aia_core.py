"""Small, side-effect-free App Inventor AIA construction helpers.

Component versions, method arguments and event names come from the exact native
distribution used by this project.  Importing this module never emits files.
"""
from __future__ import annotations

from pathlib import Path
import copy
import hashlib
import itertools
import json
import re
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[3]
METADATA_PATH = ROOT / 'work/native/server/war/WEB-INF/classes/com/google/appinventor/simple_components.json'
METADATA = {c['name']: c for c in json.loads(METADATA_PATH.read_text(encoding='utf8'))}


class AiaProject:
    def __init__(self, lesson: int, name: str, title: str):
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', name):
            raise ValueError('Internal project names must use ASCII identifiers')
        self.lesson, self.name, self.title = lesson, name, title
        self._ids = itertools.count(lesson * 100000 + 1)
        self._block_ids = itertools.count(1)
        self.types: dict[str, str] = {}
        self.components: dict[str, dict] = {}
        self.tops: list[ET.Element] = []
        self.class_tops: list[ET.Element] = []
        self.form: dict | None = None
        self.assets: dict[str, Path | bytes] = {}

    def comp(self, name, typ, children=None, **props):
        if name in self.types:
            raise ValueError(f'Duplicate component {name}')
        if typ not in METADATA:
            raise ValueError(f'Unknown component type {typ}')
        allowed = {p['name'] for p in METADATA[typ]['properties']} | {p['name'] for p in METADATA[typ]['blockProperties']}
        unknown = set(props) - allowed
        if unknown:
            raise ValueError(f'{typ} {name}: unknown properties {sorted(unknown)}')
        for key, value in props.items():
            if 'Color' in key and str(value).startswith('&') and not re.fullmatch(r'&H[0-9A-Fa-f]{8}', str(value)):
                raise ValueError(f'{typ} {name}: invalid ARGB color {key}={value}')
        c = {'$Name': name, '$Type': typ, '$Version': str(METADATA[typ]['version']), 'Uuid': str(next(self._ids))}
        c.update({k: str(v) for k, v in props.items()})
        if children is not None:
            c['$Components'] = children
        self.types[name] = typ
        self.components[name] = c
        return c

    def screen(self, children, **props):
        defaults = dict(Title=self.title, AppName=self.title, Sizing='Responsive', ScreenOrientation='portrait',
                        Scrollable='True', TitleVisible='False', ShowStatusBar='True', ActionBar='False',
                        Theme='AppTheme.Light', PrimaryColor='&HFF1388CC', PrimaryColorDark='&HFF123E62',
                        AccentColor='&HFF1388CC', BackgroundColor='&HFFF1F9FF', Icon='logo.png',
                        AboutScreen=f'羽轩编程工作台｜第 {self.lesson} 课：{self.title}\n课堂参考作品，支持在设计界面与逻辑设计中继续改编。')
        defaults.update(props)
        self.form = self.comp('Screen1', 'Form', children, **defaults)
        self.form['Uuid'] = '0'
        return self.form

    def label(self, name, text, **props):
        defaults = dict(Text=text, Width=-2, Height=-1, FontSize=17, TextColor='&HFF123E62', TextAlignment=0)
        defaults.update(props)
        return self.comp(name, 'Label', **defaults)

    def button(self, name, text, **props):
        defaults = dict(Text=text, Width=-2, Height=52, FontSize=17, TextColor='&HFFFFFFFF',
                        BackgroundColor='&HFF1388CC', Shape=1, ShowFeedback='True')
        defaults.update(props)
        return self.comp(name, 'Button', **defaults)

    def page(self, children, **props):
        defaults = dict(Width=-2, Height=-1, BackgroundColor='&HFFF1F9FF')
        defaults.update(props)
        return self.comp('Page', 'VerticalArrangement', children, **defaults)

    def b(self, typ, fields=None, values=None, statements=None, mutation=None, **attrs):
        b = ET.Element('block', {'type': typ, 'id': f'c{self.lesson:02d}-{next(self._block_ids):05d}',
                                 **{k: str(v) for k, v in attrs.items()}})
        if mutation is not None:
            m = ET.SubElement(b, 'mutation', {'xmlns': 'http://www.w3.org/1999/xhtml',
                    **{k: str(v) for k, v in mutation.items() if k not in ('args', 'eventparam')}})
            for arg in mutation.get('args', []):
                ET.SubElement(m, 'arg', {'name': arg})
            if 'eventparam' in mutation:
                ET.SubElement(m, 'eventparam', {'name': mutation['eventparam']})
        for k, v in (fields or {}).items():
            ET.SubElement(b, 'field', {'name': k}).text = str(v)
        for k, v in (values or {}).items():
            if v is None:
                raise ValueError(f'Empty value socket {typ}.{k}')
            ET.SubElement(b, 'value', {'name': k}).append(v)
        for k, v in (statements or {}).items():
            if v is not None:
                ET.SubElement(b, 'statement', {'name': k}).append(v)
        return b

    def text(self, value): return self.b('text', {'TEXT': value})
    def num(self, value): return self.b('math_number', {'NUM': value})
    def boolean(self, value): return self.b('logic_boolean', {'BOOL': 'TRUE' if value else 'FALSE'})
    def var(self, name): return self.b('lexical_variable_get', {'VAR': 'global ' + name})
    def param(self, name, event=False):
        return self.b('lexical_variable_get', {'VAR': name}, mutation={'eventparam': name} if event else None)
    def global_(self, name, value): return self.b('global_declaration', {'NAME': name}, {'VALUE': value})
    def setvar(self, name, value): return self.b('lexical_variable_set', {'VAR': 'global ' + name}, {'VALUE': value})
    def add(self, a, b): return self.b('math_add', values={'NUM0': a, 'NUM1': b}, mutation={'items': 2})
    def sub(self, a, b): return self.b('math_subtract', values={'A': a, 'B': b})
    def mul(self, a, b): return self.b('math_multiply', values={'NUM0': a, 'NUM1': b}, mutation={'items': 2})
    def div(self, a, b): return self.b('math_division', values={'A': a, 'B': b})
    def mm(self, op, a, b): return self.b('math_on_list', {'OP': op}, {'NUM0': a, 'NUM1': b}, mutation={'items': 2})
    def cmp(self, op, a, b): return self.b('math_compare', {'OP': op}, {'A': a, 'B': b})
    def eq(self, a, b): return self.b('logic_compare', {'OP': 'EQ'}, {'A': a, 'B': b})
    def both(self, a, b): return self.b('logic_operation', {'OP': 'AND'}, {'A': a, 'B': b}, mutation={'items': 2})
    def join(self, *items): return self.b('text_join', values={f'ADD{i}': v for i,v in enumerate(items)}, mutation={'items': len(items)})
    def trim(self, value): return self.b('text_trim', values={'TEXT': value})
    def isnum(self, value): return self.b('math_is_a_number', {'OP': 'NUMBER'}, {'NUM': value})
    def floor(self, value): return self.b('math_floor', values={'NUM': value})
    def random(self, start, end): return self.b('math_random_int', values={'FROM': start, 'TO': end})
    def iff(self, test, yes, no=None):
        return self.b('controls_if', values={'IF0': test}, statements={'DO0': yes, **({'ELSE': no} if no is not None else {})},
                      mutation={'elseif': 0, 'else': 1} if no is not None else None)
    def define(self, name, body, args=(), returns=False):
        return self.b('procedures_defreturn' if returns else 'procedures_defnoreturn', {'NAME': name},
                      values={'RETURN': body} if returns else None, statements=None if returns else {'STACK': body}, mutation={'args': args})
    def call(self, name, *args, names=(), returns=False):
        if len(args) != len(names):
            raise ValueError(f'Procedure call {name}: values and names differ')
        return self.b('procedures_callreturn' if returns else 'procedures_callnoreturn', {'PROCNAME': name},
                      values={f'ARG{i}': v for i,v in enumerate(args)}, mutation={'name': name, 'args': names})
    def forrange(self, name, start, end, step, body):
        return self.b('controls_forRange', {'VAR': name}, {'START': start, 'END': end, 'STEP': step}, {'DO': body})

    def event(self, component, name, body, comment=None):
        typ = self.types[component]
        if name not in {e['name'] for e in METADATA[typ]['events']}:
            raise ValueError(f'Unknown event {component}.{name}')
        b = self.b('component_event', {'COMPONENT_SELECTOR': component}, statements={'DO': body},
                    mutation=dict(component_type=typ, is_generic='false', instance_name=component, event_name=name))
        return self.note(b, comment) if comment else b

    def get(self, component, prop):
        self._check_property(component, prop, False)
        return self.b('component_set_get', {'COMPONENT_SELECTOR': component, 'PROP': prop},
                      mutation=dict(component_type=self.types[component], set_or_get='get', property_name=prop,
                                    is_generic='false', instance_name=component))

    def set(self, component, prop, value):
        self._check_property(component, prop, True)
        return self.b('component_set_get', {'COMPONENT_SELECTOR': component, 'PROP': prop}, {'VALUE': value},
                      mutation=dict(component_type=self.types[component], set_or_get='set', property_name=prop,
                                    is_generic='false', instance_name=component))

    def _check_property(self, component, prop, write):
        ps = {p['name']: p for p in METADATA[self.types[component]]['blockProperties']}
        if prop not in ps:
            raise ValueError(f'Unknown block property {component}.{prop}')
        if write and ps[prop]['rw'] == 'read-only':
            raise ValueError(f'Read-only block property {component}.{prop}')
        if not write and ps[prop]['rw'] == 'write-only':
            raise ValueError(f'Write-only block property {component}.{prop}')

    def method(self, component, name, *args):
        typ = self.types[component]
        method = next((m for m in METADATA[typ]['methods'] if m['name'] == name), None)
        if method is None or len(method['params']) != len(args):
            raise ValueError(f'Wrong method or arity: {component}.{name}({len(args)})')
        return self.b('component_method', {'COMPONENT_SELECTOR': component},
                      {f'ARG{i}': arg for i, arg in enumerate(args)},
                      mutation=dict(component_type=typ, is_generic='false', instance_name=component, method_name=name))

    def chain(self, *blocks):
        # A fragment can already contain a sequence, and can be reused by its
        # author. Work on fresh trees and append at the tail, never a second next.
        fragments=[]
        for block in blocks:
            if block is None: continue
            block=copy.deepcopy(block)
            for node in block.iter('block'):
                node.set('id', f'c{self.lesson:02d}-{next(self._block_ids):05d}')
            fragments.append(block)
        if not fragments: return None
        tail=fragments[0]
        for following in fragments[1:]:
            while tail.find('next') is not None:
                tail=tail.find('next/block')
                if tail is None: raise ValueError('Empty next in sequence fragment')
            ET.SubElement(tail,'next').append(following)
            tail=following
        return fragments[0]

    @staticmethod
    def note(block, text):
        ET.SubElement(block, 'comment', {'pinned': 'false', 'h': '100', 'w': '350'}).text = text
        return block

    def place(self, blocks):
        # Rows are generous enough for three-property beginner event chains.
        for i, b in enumerate(blocks):
            b.set('x', str(40 + (i % 2) * 1050))
            b.set('y', str(40 + (i // 2) * 550))
        return blocks

    def xml(self, kind):
        tops = self.tops if kind == 'answer' else self.class_tops if kind == 'class' else []
        root = ET.Element('xml', {'xmlns': 'https://developers.google.com/blockly/xml'})
        for b in self.place(copy.deepcopy(tops)):
            root.append(b)
        ET.SubElement(root, 'yacodeblocks', {'xmlns': 'https://appinventor.mit.edu/ns/project/',
                                           'ya-version': '237', 'language-version': '39'})
        return ET.tostring(root, encoding='utf-8', xml_declaration=False)

    def validate(self):
        if self.form is None:
            raise ValueError('No Screen1')
        result = {}
        for kind in ('answer', 'class', 'starter'):
            data = self.xml(kind)
            root = ET.fromstring(data)
            ids = [b.get('id') for b in root.iter() if b.tag.endswith('block') and b.tag.rsplit('}', 1)[-1] == 'block']
            if len(ids) != len(set(ids)):
                raise ValueError(f'Duplicate block ids in {kind}')
            for b in root.iter():
                if b.tag.rsplit('}', 1)[-1] != 'block':
                    continue
                if len(b.findall('next'))>1:
                    raise ValueError(f'Multiple next connections in {kind}: {b.get("id")}')
                for m in b:
                    if m.tag.rsplit('}', 1)[-1] == 'mutation' and m.get('instance_name'):
                        if m.get('instance_name') not in self.types:
                            raise ValueError(f'Dangling component in {kind}')
                        if self.types[m.get('instance_name')] != m.get('component_type'):
                            raise ValueError(f'Wrong component type in {kind}')
            result[kind] = {'blockCount': len(ids), 'topLevelCount': sum(1 for n in root if n.tag.rsplit('}', 1)[-1] == 'block')}
        # Every designer file path must name a bundled asset, never an external URL.
        for c in self.components.values():
            for k in ('Picture', 'Image', 'Icon', 'Source'):
                if c.get(k) and c[k] not in self.assets:
                    raise ValueError(f'Missing asset {c["$Name"]}.{k}={c[k]}')
        return result

    def write(self, folder):
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        counts = self.validate()
        versions = []
        for kind, suffix in [('answer', ''), ('class', 'Class'), ('starter', 'Starter')]:
            name = self.name + suffix
            path = folder / f'{name}.aia'
            source = f'src/appinventor/ai_yuxuan/{name}'
            props = (f'main=appinventor.ai_yuxuan.{name}.Screen1\nname={name}\naname={self.title}\n'
                     'source=../src\nassets=../assets\nbuild=../build\nversioncode=1\nversionname=1.0\n'
                     'androidminsdk=14\nactionbar=False\nshowlistsasjson=True\nsizing=Responsive\n'
                     'theme=AppTheme.Light\ncolor.primary=&HFF1388CC\ncolor.primary.dark=&HFF123E62\n'
                     'color.accent=&HFF1388CC\ndefaultfilescope=App\nlastopened=Screen1\nuseslocation=false\nprojectcolors={}\n')
            with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
                z.writestr('youngandroidproject/project.properties', props.encode('utf8'))
                z.writestr(source + '/Screen1.scm', '#|\n$JSON\n' + json.dumps(
                    {'authURL': ['127.0.0.1'], 'YaVersion': '237', 'Source': 'Form', 'Properties': self.form},
                    ensure_ascii=False, separators=(',', ':')) + '\n|#')
                z.writestr(source + '/Screen1.bky', self.xml(kind))
                for asset, value in self.assets.items():
                    z.writestr('assets/' + asset, value.read_bytes() if isinstance(value, Path) else value)
            versions.append(dict(name=name, file=str(path.resolve()), kind=kind, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), **counts[kind]))
        return versions

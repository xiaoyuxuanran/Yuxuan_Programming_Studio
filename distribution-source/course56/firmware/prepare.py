"""Copy shared headers so each sketch is independently distributable."""
from pathlib import Path
root=Path(__file__).resolve().parent
for folder in sorted(p.parent for p in root.glob('*/*.ino')):
    if folder.name=='46-ble-led':continue
    for name in ['course_protocol.h','course_board.h']+(['course_tcp.h'] if int(folder.name[:2])>=47 else []):
        (folder/name).write_bytes((root/'shared'/name).read_bytes())
print('Prepared six self-contained sketch directories.')

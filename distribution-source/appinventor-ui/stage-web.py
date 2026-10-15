from pathlib import Path
import shutil

here = Path(__file__).resolve().parent
native = here.parent / 'native'
war = native / 'server/war'
for name, folder in [('offline-usb.js','js'), ('offline-usb.css','css')]:
    shutil.copy2(here / name, war / 'static' / folder / name)
index = war / 'index.jsp'
text = index.read_text(encoding='utf-8')
text = text.replace('offline-usb.css?v=usb1', 'offline-usb.css?v=usb3').replace('offline-usb.js?v=usb1', 'offline-usb.js?v=usb3')
text = text.replace('offline-usb.css?v=usb2', 'offline-usb.css?v=usb3').replace('offline-usb.js?v=usb2', 'offline-usb.js?v=usb3')
if 'offline-usb.js' not in text:
    text = text.replace('</head>', '''<link rel="stylesheet" href="static/css/offline-usb.css?v=usb3">
<script src="static/js/offline-usb.js?v=usb3"></script>
</head>''')
index.write_text(text, encoding='utf-8')
xml = war / 'WEB-INF/web.xml'
text = xml.read_text(encoding='utf-8')
if 'OfflineUsbServlet' not in text:
    text = text.replace('  <!-- download -->', '''  <!-- Authenticated desktop USB device bridge -->
  <servlet>
    <servlet-name>offlineUsbServlet</servlet-name>
    <servlet-class>com.google.appinventor.server.OfflineUsbServlet</servlet-class>
  </servlet>
  <servlet-mapping>
    <servlet-name>offlineUsbServlet</servlet-name>
    <url-pattern>/ode/usb/*</url-pattern>
  </servlet-mapping>
  <filter-mapping>
    <filter-name>odeAuthFilter</filter-name>
    <servlet-name>offlineUsbServlet</servlet-name>
  </filter-mapping>

  <!-- download -->''')
xml.write_text(text, encoding='utf-8')
(native / 'resources/build-version.txt').write_text('2026.10.04-usb-fast-build-4\n', encoding='utf-8')
print('Staged USB web resources and authenticated servlet mapping.')

"""Проверка итогового layout-land браузера после сборки Verify MireaProject в IDE.

Проверяем реальные bounds, доступность кнопок и историю после пересоздания Fragment.
Импортируем только функции SDK из check_lesson3; основной прогон повторно не запускается.
"""
import re
import time
import check_lesson3 as m

def wait_ready():
    for _ in range(20):
        if m.text_id('status') == 'Страница загружена.':
            return
        time.sleep(1)
    raise AssertionError('Страница не завершила загрузку: '+m.text_id('status'))

def bounds(n):
    return list(map(int, re.findall(r'\d+', n.get('bounds'))))

# Сценарий выполняется после check_extra.py, оставившего браузер на странице МИРЭА.
m.rotate(True)
nodes = m.nodes()
controls = [next(n for n in nodes if n.get('resource-id','').endswith('/'+id))
            for id in ('url','go','home','backPage','reload')]
rows = [bounds(n) for n in controls]
m.check('Final landscape browser controls share one row',
        len({b[1] for b in rows}) == 1 and all(b[2]>b[0] and b[3]>b[1] for b in rows))
host = next(n for n in nodes if n.get('resource-id','').endswith('/nav_host_fragment_content_main'))
web = next(n for n in nodes if n.get('class') == 'android.webkit.WebView')
hb, wb = bounds(host), bounds(web)
m.check('Final landscape WebView has over half of content height',
        wb[3]-wb[1] > (hb[3]-hb[1])*.5, 'WebView='+str(wb)+'; host='+str(hb))
m.xml(); m.screenshot('22-web-landscape-final')
m.type_field('url','https://example.com')
m.shell('input','keyevent','KEYCODE_BACK'); m.click(id='go'); wait_ready()
m.check('Final landscape Go loads page','Example Domain' in m.alltext())
m.click(id='reload'); wait_ready()
m.check('Final landscape Reload preserves page','Example Domain' in m.alltext())
m.rotate(); wait_ready()
m.check('Final WebView page survives landscape to portrait','example.com' in m.text_id('url') and 'Example Domain' in m.alltext())
m.click(id='backPage'); wait_ready()
m.check('Final WebView history survives landscape to portrait','mirea.ru' in m.text_id('url'))
m.xml(); m.screenshot('31-web-history-after-final-rotation')
log = m.shell('logcat','-d','-b','crash')
(m.OUT/'crash-log.txt').write_text(log,encoding='utf-8')
m.check('Final no fatal exception','FATAL EXCEPTION' not in log)

"""Дополнительные сценарии после check_lesson3.py: фото, камера, HTTPS и drawer Back."""
import json,time
from pathlib import Path
import check_lesson3 as m

ROOT=Path(__file__).resolve().parent.parent
m.checks=json.loads((m.OUT/'checks.json').read_text(encoding='utf-8'))

def assert_result(name, condition, detail=''):
    # Повторный запуск обновляет конкретный результат, а не увеличивает счётчик копиями.
    m.checks[:]=[x for x in m.checks if x['name']!=name]
    m.check(name,condition,detail)

def wait_ready():
    for _ in range(15):
        if m.text_id('status')=='Страница загружена.': return
        time.sleep(1)

m.rotate()
m.adb('push',str(m.SHOTS/'15-fragments-landscape.png'),'/sdcard/Pictures/lesson3-test.png')
m.shell('am','broadcast','-a','android.intent.action.MEDIA_SCANNER_SCAN_FILE','-d','file:///sdcard/Pictures/lesson3-test.png')
m.start('ru.mirea.ZubarevVS.lesson3.sharer')
m.click(id='pick');m.click(text='Pictures');m.click(desc='Photo taken')
assert_result('Sharer image picker returns content URI','content://' in m.text_id('picked'))
m.xml();m.screenshot('25-picker-result')
m.click(id='camera');m.click(desc='Shutter');m.click(desc='Done')
assert_result('Sharer camera returns thumbnail','Получена миниатюра' in m.text_id('camera_status'))
m.xml();m.screenshot('27-camera-result')
m.rotate(True)
m.shell('input','swipe','1100','850','1100','200','300') # Статус в landscape ниже верхней части ScrollView.
assert_result('Sharer camera status survives rotation','Получена миниатюра' in m.text_id('camera_status'))
m.xml();m.screenshot('30-camera-landscape');m.rotate()

m.start('ru.mirea.ZubarevVS.lesson3.systemintentsapp');m.click(id='maps')
if 'SKIP' in m.alltext():m.click(text='SKIP')
assert_result('Google Maps opens geo URI','com.google.android.apps.maps' in m.shell('dumpsys','activity','activities'))
m.xml();m.screenshot('28-map-after-skip')

m.adb('install','-r',str(ROOT/'MireaProject/app/build/outputs/apk/debug/app-debug.apk'))
m.start('ru.mirea.ZubarevVS.mireaproject');m.click(desc='Open navigation drawer')
assert_result('Final drawer opens after inset fix','Браузер' in m.alltext())
m.xml();m.screenshot('19-mirea-drawer');m.click(text='Браузер');wait_ready()
assert_result('Final WebView MIREA renders',m.text_id('status')=='Страница загружена.' and 'mirea.ru' in m.text_id('url'))
m.xml();m.screenshot('20-web-default')
m.type_field('url','http://example.com');m.shell('input','keyevent','KEYCODE_BACK');m.click(id='go')
assert_result('WebView rejects cleartext URL','Введите адрес HTTPS' in m.alltext())
m.xml();m.screenshot('29-https-validation')
m.type_field('url','https://example.com');m.shell('input','keyevent','KEYCODE_BACK');m.click(id='go');wait_ready()
assert_result('Final WebView renders example.com','Example Domain' in m.alltext())
m.click(desc='Open navigation drawer');m.shell('input','keyevent','KEYCODE_BACK');time.sleep(.5)
assert_result('Drawer Back precedes WebView history','example.com' in m.text_id('url') and not any(n.attrib.get('resource-id','').endswith('/navView') for n in m.nodes()))
m.click(id='backPage')
for _ in range(15):
    if 'mirea.ru' in m.text_id('url'): break
    time.sleep(1)
assert_result('Final WebView history back','mirea.ru' in m.text_id('url'))
log=m.shell('logcat','-d','-b','crash')
(m.OUT/'crash-log.txt').write_text(log,encoding='utf-8')
assert_result('Final no fatal exception','FATAL EXCEPTION' not in log)

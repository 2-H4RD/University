"""Реальные APK: макеты, события, состояние и ориентация. Доказательства сохраняются в audit.
Запуск после Verify Lesson1 в Android Studio; ANDROID_SERIAL выбирает устройство SDK.
Общие функции ADB/UIAutomator находятся в соседней практике №2, зависимости только stdlib.
"""
import importlib.util
import json
import os
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('audit_support', ROOT.parent/'Lesson2/verification/check_apps.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m.OUT = Path(os.environ.get('LESSON_AUDIT_OUT', str(ROOT/'verification/audit-2026-10-09')))
m.OUT.mkdir(parents=True, exist_ok=True)
m.SHOTS = m.OUT/'screenshots'
m.SHOTS.mkdir(exist_ok=True)
m.RESULTS = json.loads((m.OUT/'checks.json').read_text(encoding='utf-8')) if (m.OUT/'checks.json').exists() else []
PKGS = {'app':'ru.mirea.ZubarevVS.lesson1', 'layouttype':'ru.mirea.ZubarevVS.layouttype',
        'control_lesson1':'ru.mirea.ZubarevVS.control_lesson1', 'buttonclicker':'ru.mirea.ZubarevVS.buttonclicker'}

def start(module):
    pkg = PKGS[module]
    m.shell('am','force-stop',pkg)
    output = m.shell('am','start','-W','-a','android.intent.action.MAIN','-c','android.intent.category.LAUNCHER',
                     '-f','0x10200000','-n',pkg+'/.MainActivity')
    m.record(module+' launches', 'Status: ok' in output, output)
    time.sleep(1)

def nodes(): return list(m.dump().iter('node'))
def text(id): return m.node(id).get('text','')
def visible(id):
    n=m.node(id)
    x1,y1,x2,y2=map(int,re.findall(r'\d+',n.get('bounds')))
    return x2>x1 and y2>y1

def buttons(count):
    found=[n for n in nodes() if n.get('text','').lower().startswith('кнопка ') and n.get('class','').endswith('Button')]
    return len(found)==count and all(len(set(re.findall(r'\d+',n.get('bounds'))))>1 for n in found)

def menu(label):
    more=next(n for n in nodes() if n.get('content-desc') in ('More options','Ещё','Дополнительные параметры'))
    x1,y1,x2,y2=map(int,re.findall(r'\d+',more.get('bounds')))
    m.shell('input','tap',(x1+x2)//2,(y1+y2)//2)
    time.sleep(.4)
    m.tap(text=label)
    time.sleep(.5)

def run():
    m.shell('input','keyevent','KEYCODE_WAKEUP');m.shell('wm','dismiss-keyguard')
    m.rotate(0);m.shell('cmd','uimode','night','no');m.shell('logcat','-c')
    for module in PKGS:
        apk=next((ROOT/module/'build/outputs/apk/debug').glob('*.apk'))
        m.record(module+' installs','Success' in m.adb('install','-r',apk))
    start('app');m.record('Hello World screen',m.has_text('Hello World!'));m.screenshot('01-hello')
    start('layouttype')
    m.record('Six buttons and EditText portrait',buttons(6) and 'New life for mirea activity!' in text('editTextNewLife'))
    m.screenshot('02-six-portrait');m.rotate(1)
    m.record('Six buttons and EditText landscape',buttons(6) and visible('editTextNewLife'))
    m.screenshot('03-six-landscape');m.rotate(0)
    menu('Макет: LinearLayout');m.record('LinearLayout six buttons',buttons(6));m.screenshot('04-linear')
    menu('Макет: TableLayout');m.record('TableLayout controls',buttons(5) and m.has_text('Флажок') and m.has_text('Текст'))
    m.screenshot('05-table');m.rotate(1)
    m.record('Selected table survives rotation',m.has_text('Флажок') and m.has_text('Текст'));m.screenshot('06-table-landscape');m.rotate(0)
    menu('Макет: ConstraintLayout');m.record('ConstraintLayout controls',visible('constraintTitle') and visible('constraintButtonLeft') and visible('constraintCheckBox'));m.screenshot('07-constraint')
    menu('Макет: TextView');m.record('Modified TextView',visible('textViewHello'));m.screenshot('08-textview')
    start('control_lesson1')
    ids=['contactImage','contactTitle','nameInput','favoriteCheckBox','saveButton','callImageButton']
    m.record('Six required control types portrait',all(visible(i) for i in ids));m.screenshot('09-controls-portrait')
    m.tap('nameInput');m.shell('input','text','Practice');m.shell('input','keyevent','KEYCODE_BACK');m.tap('favoriteCheckBox')
    m.rotate(1);m.record('Six control types landscape',all(visible(i) for i in ids))
    m.record('Control input and checkbox survive rotation',text('nameInput')=='Practice' and m.node('favoriteCheckBox').get('checked')=='true');m.screenshot('10-controls-landscape');m.rotate(0)
    start('buttonclicker')
    m.record('ButtonClicker initial unchecked',m.node('checkBox').get('checked')=='false')
    m.tap('btnWhoAmI');m.record('Java listener student number and toggle',text('tvOut')=='Мой номер по списку №5' and m.node('checkBox').get('checked')=='true');m.screenshot('11-java-listener')
    m.tap('btnItIsNotMe');m.record('XML handler text and toggle',text('tvOut')=='Это не я сделал' and m.node('checkBox').get('checked')=='false');m.screenshot('12-xml-handler')
    m.rotate(1);m.record('ButtonClicker output survives rotation',text('tvOut')=='Это не я сделал' and m.node('checkBox').get('checked')=='false');m.screenshot('13-clicker-landscape')
    m.tap('btnWhoAmI');m.rotate(0);m.record('Checked state survives rotation',m.node('checkBox').get('checked')=='true' and text('tvOut')=='Мой номер по списку №5')
    m.shell('cmd','uimode','night','yes');time.sleep(1);m.record('ButtonClicker dark theme retains output',text('tvOut')=='Мой номер по списку №5');m.screenshot('14-clicker-dark')
    m.shell('cmd','uimode','night','no');m.rotate(0)
    log=m.shell('logcat','-d','-b','crash');(m.OUT/'crash-log.txt').write_text(log,encoding='utf-8')
    m.record('No fatal exception','FATAL EXCEPTION' not in log,log)
    print('Completed',len(m.RESULTS),'checks',flush=True)

if __name__=='__main__':
    try: run()
    except Exception as error:
        (m.OUT/'failure.txt').write_text(str(error),encoding='utf-8')
        try:m.screenshot('failure')
        except Exception:pass
        raise

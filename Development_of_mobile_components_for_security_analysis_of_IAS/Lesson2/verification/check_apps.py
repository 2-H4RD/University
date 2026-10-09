"""Проверка реальных APK на учебном эмуляторе; XML и PNG сохраняются как доказательства."""
import argparse
import os
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADB = Path.home() / 'AppData/Local/Android/Sdk/platform-tools/adb.exe'
DEVICE = os.environ.get('ANDROID_SERIAL', 'emulator-5554')
# Новый запуск имеет отдельные доказательства и не подмешивает старые результаты.
OUT = Path(os.environ.get('LESSON_AUDIT_OUT', str(ROOT / 'verification' / 'audit-2026-10-09')))
OUT.mkdir(parents=True, exist_ok=True)
SHOTS = OUT / 'screenshots'
SHOTS.mkdir(exist_ok=True)
RESULTS = json.loads((OUT / 'checks.json').read_text(encoding='utf-8')) if (OUT / 'checks.json').exists() else []
MODULES = ['ActivityLifecycle', 'MultiActivity', 'IntentFilter', 'ToastApp', 'NotificationApp', 'Dialog']

def adb(*args, binary=False, check=True):
    result = subprocess.run([str(ADB), '-s', DEVICE, *map(str,args)], capture_output=True,
                            timeout=50, text=not binary, encoding=None if binary else 'utf-8',
                            errors=None if binary else 'replace')
    if check and result.returncode:
        raise RuntimeError(f'ADB {args}: {result.stderr}')
    return result.stdout

def shell(*args):
    return adb('shell', *args)

def package(module):
    return 'ru.mirea.ZubarevVS.lesson2.' + module.lower()

def record(name, condition, detail=''):
    RESULTS[:]=[item for item in RESULTS if item['check'] != name]
    RESULTS.append({'check': name, 'passed': bool(condition), 'detail': detail})
    (OUT / 'checks.json').write_text(json.dumps(RESULTS, ensure_ascii=False, indent=2),encoding='utf-8')
    print(('PASS ' if condition else 'FAIL ') + name, flush=True)
    if not condition:
        raise AssertionError(name + ': ' + detail)

def dump(name=None):
    shell('uiautomator','dump','/sdcard/lesson2-window.xml')
    data=shell('cat','/sdcard/lesson2-window.xml')
    if name:
        (OUT / (name+'.xml')).write_text(data,encoding='utf-8')
    return ET.fromstring(data)

def node(id=None, text=None):
    tree=dump()
    matches=[n for n in tree.iter('node') if (id is None or n.get('resource-id','').endswith('/'+id))
             and (text is None or n.get('text')==text)]
    if not matches:
        raise RuntimeError(f'Элемент не найден: id={id}, text={text}')
    return matches[0]

def tap(id=None,text=None):
    n=node(id,text)
    x1,y1,x2,y2=map(int,re.findall(r'\d+',n.get('bounds')))
    shell('input','tap',(x1+x2)//2,(y1+y2)//2)
    time.sleep(.5)

def screenshot(name):
    time.sleep(.8) # Ждём завершения системной анимации: иначе PNG может показать предыдущий кадр.
    (SHOTS / (name+'.png')).write_bytes(adb('exec-out','screencap','-p',binary=True))
    dump(name)

def launch(module, fresh=True):
    pkg=package(module)
    if fresh:
        shell('am','force-stop',pkg)
    # Имитируем launcher: обычный явный am start иначе меняет семантику Back у корневой Activity.
    output=shell('am','start','-W','-a','android.intent.action.MAIN','-c',
                 'android.intent.category.LAUNCHER','-f','0x10200000','-n',pkg+'/'+pkg+'.MainActivity')
    record(module+' launch', 'Status: ok' in output,output)
    time.sleep(.5)

def input_text(value, clear=False):
    tap('input')
    if clear:
        current=node('input').get('text','')
        shell('input','keyevent','123')
        if current:
            shell('input','keyevent',*(['67']*len(current)))
    shell('input','text',value.replace(' ','%s'))
    # Не посылаем Back после ввода: при аппаратной клавиатуре он может закрыть саму Activity.

def rotate(value):
    shell('settings','put','system','accelerometer_rotation','0')
    shell('settings','put','system','user_rotation',str(value))
    time.sleep(1.2)

def has_text(value):
    return any(value in n.get('text','') for n in dump().iter('node'))

def scroll_down():
    # Берём реальный размер текущей ориентации из UI XML; размеры wm size относятся к natural orientation.
    bounds=list(dump().iter('node'))[0].get('bounds')
    x1,y1,x2,y2=map(int,re.findall(r'\d+',bounds))
    shell('input','swipe',(x1+x2)//2,int(y2*.8),(x1+x2)//2,int(y2*.25),'450')
    time.sleep(.5)

def install():
    for m in MODULES:
        apks=list((ROOT/m/'build/outputs/apk/debug').glob('*.apk'))
        record(m+' APK exists',len(apks)==1)
        record(m+' install','Success' in adb('install','-r',apks[0]))

def visual():
    shell('input','keyevent','82')
    rotate(0)
    for m in MODULES:
        launch(m)
        screenshot(m+'-portrait')
        record(m+' student info',has_text('Зубарев Василий Сергеевич'))
        rotate(1)
        screenshot(m+'-landscape')
        record(m+' landscape title', any(n.get('resource-id','').endswith('/title') for n in dump().iter('node')))
        rotate(0)

def lifecycle():
    adb('logcat','-c')
    launch('ActivityLifecycle')
    input_text('Lifecycle42',clear=True)
    shell('input','keyevent','3')
    time.sleep(.5)
    launch('ActivityLifecycle',fresh=False)
    record('Lifecycle Home text retained',node('input').get('text')=='Lifecycle42')
    log=adb('logcat','-d','-s','LifecycleMain:I','*:S')
    record('Lifecycle Home no second onCreate',log.count('onCreate()')==1,log)
    shell('input','keyevent','4')
    launch('ActivityLifecycle',fresh=False)
    back_text=node('input').get('text')
    back_log=adb('logcat','-d','-s','LifecycleMain:I','*:S')
    retained=back_text=='Lifecycle42'
    # Методичка просит исследовать Back: фиксируем реальное поведение, не навязываем результат версии ОС.
    record('Lifecycle Back behavior recorded',
           back_log.count('onCreate()') == (1 if retained else 2),
           'text retained' if retained else 'Activity recreated; field reset')
    input_text('Lifecycle42',clear=True)
    rotate(1)
    record('Lifecycle rotation text retained',node('input').get('text')=='Lifecycle42')
    rotate(0)
    screenshot('Lifecycle-after-rotation')
    (OUT/'lifecycle-logcat.txt').write_text(adb('logcat','-d','-s','LifecycleMain:I','*:S'),encoding='utf-8')

def multi():
    adb('logcat','-c')
    launch('MultiActivity')
    tap('send')
    record('MultiActivity full FIO transferred',node('received').get('text')=='Зубарев Василий Сергеевич')
    screenshot('MultiActivity-second-fio')
    tap('back')
    input_text('Text42',clear=True)
    tap('send')
    record('MultiActivity arbitrary text transferred',node('received').get('text')=='Text42')
    shell('input','keyevent','4')
    record('MultiActivity Back restores first screen',node('input').get('text')=='Text42')
    (OUT/'multi-logcat.txt').write_text(adb('logcat','-d','-s','MultiMain:I','MultiSecond:I','*:S'),encoding='utf-8')

def toast():
    launch('ToastApp')
    tap('count')
    record('Toast empty count 0',has_text('Количество символов - 0'))
    screenshot('Toast-empty')
    input_text('MIREA',clear=True)
    tap('count')
    record('Toast MIREA count 5',has_text('Количество символов - 5'))
    screenshot('Toast-five')
    input_text('a b',clear=True)
    tap('count')
    record('Toast spaces count 3',has_text('Количество символов - 3'))
    rotate(1)
    record('Toast result retained on rotation',has_text('Количество символов - 3'))
    rotate(0)

def intents():
    launch('IntentFilter')
    tap('share')
    screenshot('Intent-share-chooser')
    activity=shell('dumpsys','activity','activities')
    record('Intent share chooser opens','ChooserActivity' in activity)
    shell('input','keyevent','4')
    tap('open')
    screenshot('Intent-browser')
    activity=shell('dumpsys','activity','activities')
    record('Intent browser opens','com.android.chrome' in activity)
    # Не выбираем получателя и не отправляем ФИО в стороннее приложение.
    shell('input','keyevent','4')

def notifications():
    launch('NotificationApp')
    tap('notify')
    screenshot('Notification-permission')
    tap('permission_deny_button')
    record('Notification denial handled',has_text('Разрешение не выдано'))
    screenshot('Notification-denied')
    tap('notify')
    tap('permission_allow_button')
    record('Notification allowed and sent',has_text('Уведомление отправлено'))
    tap('notify')
    data=shell('dumpsys','notification','--noredact')
    (OUT/'notification-dump.txt').write_text(data,encoding='utf-8')
    active=[line for line in data.splitlines() if 'NotificationRecord(' in line and 'pkg='+package('NotificationApp') in line and 'id=1' in line]
    record('Notification repeated ID leaves one record',len(active)==1,'\n'.join(active))
    shell('cmd','statusbar','expand-notifications')
    time.sleep(.6)
    screenshot('Notification-shade')
    record('Notification visible in shade',has_text('Mirea'))
    shell('cmd','statusbar','collapse')

def dialogs():
    rotate(0) # Каждый повтор сценария начинается в портретной ориентации, даже после прерванного теста.
    launch('Dialog')
    for text,result,button_id in [('Иду дальше','Иду дальше','button1'),('На паузе','На паузе','button3'),('Нет','Нет','button2')]:
        tap('alert')
        if text=='Иду дальше':
            screenshot('Dialog-alert')
        tap(button_id) # ID не зависит от регистра текста, заданного темой AlertDialog.
        record('Dialog action '+result,has_text('Вы выбрали кнопку «'+result+'»!'))
    tap('time')
    screenshot('Dialog-time')
    tap('button1')
    record('Dialog time selected',has_text('Выбрано время:'))
    screenshot('Dialog-time-result')
    tap('date')
    screenshot('Dialog-date')
    tap('button1')
    record('Dialog date selected',has_text('Выбрана дата:'))
    screenshot('Dialog-date-result')
    rotate(1)
    scroll_down() # Результат ниже четырёх кнопок: в landscape к нему нужно прокрутить экран.
    record('Dialog date result retained',has_text('Выбрана дата:'))
    screenshot('Dialog-landscape-scrolled')
    rotate(0)
    tap('progress')
    screenshot('Dialog-progress')
    record('ProgressDialog opens',has_text('Учебный ProgressDialog'))
    tap('button2')
    record('ProgressDialog closes',has_text('Диалоговые окна'))
    tap('alert')
    rotate(1)
    record('Dialog survives rotation',has_text('Здравствуй МИРЭА!'))
    screenshot('Dialog-alert-landscape')
    rotate(0)
    shell('input','keyevent','4')
    record('Dialog dismiss with Back',has_text('Диалоговые окна'))
    shell('cmd','uimode','night','yes')
    time.sleep(1)
    screenshot('Dialog-dark')
    record('Dialog dark mode usable',has_text('Диалоговые окна'))
    shell('cmd','uimode','night','no')
    time.sleep(1)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('phase',choices=['install','visual','lifecycle','multi','toast','intents','notifications','dialogs'])
    args=parser.parse_args()
    if (OUT/'checks.json').exists():
        RESULTS=json.loads((OUT/'checks.json').read_text(encoding='utf-8'))
    try:
        globals()[args.phase]()
    finally:
        (OUT/'checks.json').write_text(json.dumps(RESULTS,ensure_ascii=False,indent=2),encoding='utf-8')

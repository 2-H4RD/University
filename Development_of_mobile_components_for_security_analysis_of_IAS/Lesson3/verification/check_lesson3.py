from pathlib import Path
import subprocess, time, json, re, os, xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('LESSON_AUDIT_OUT', str(ROOT / 'verification' / 'audit-2026-10-09')))
SHOTS = OUT / 'screenshots'
SHOTS.mkdir(exist_ok=True, parents=True)
ADB = r'C:\Users\H4RD\AppData\Local\Android\Sdk\platform-tools\adb.exe'
DEVICE = os.environ.get('ANDROID_SERIAL', 'emulator-5554')
checks = json.loads((OUT/'checks.json').read_text(encoding='utf-8')) if (OUT/'checks.json').exists() else []

def adb(*args, binary=False):
    r = subprocess.run([ADB, '-s', DEVICE, *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    if r.returncode: raise RuntimeError(r.stderr.decode('utf-8',errors='replace') + r.stdout.decode('utf-8',errors='replace'))
    return r.stdout if binary else r.stdout.decode('utf-8',errors='replace')

def shell(*args): return adb('shell',*args)

def xml():
    for i in range(3):
        try:
            shell('uiautomator','dump','/sdcard/lesson3-ui.xml')
            data = shell('cat','/sdcard/lesson3-ui.xml')
            return ET.fromstring(data[data.index('<?xml'):])
        except Exception:
            if i == 2: raise
            time.sleep(1)

def nodes(): return list(xml().iter('node'))
def alltext(): return '\n'.join(n.attrib.get('text','') for n in nodes())

def tap_node(n):
    b = list(map(int,re.findall(r'\d+',n.attrib['bounds'])))
    shell('input','tap',str((b[0]+b[2])//2),str((b[1]+b[3])//2)); time.sleep(1)

def click(id=None, text=None, contains=None, desc=None):
    # Системная галерея/камера создаёт содержимое позже первого кадра Activity.
    # Ожидаем именно нужный узел, не принимая промежуточный пустой экран за сбой приложения.
    for attempt in range(6):
        for n in nodes():
            a = n.attrib
            if id and a.get('resource-id','').endswith('/'+id) or text and a.get('text')==text or contains and contains in a.get('text','') or desc and desc in a.get('content-desc',''):
                tap_node(n); return
        time.sleep(1)
    raise RuntimeError('Node absent '+str((id,text,contains,desc))+'\n'+alltext()[:1000])

def type_field(id,value):
    click(id=id)
    shell('input','keyevent','KEYCODE_MOVE_END')
    shell('input','keyevent','--longpress','KEYCODE_DEL')
    # Ctrl+A selects existing URL/text before deletion.
    shell('input','keycombination','113','29')
    shell('input','keyevent','KEYCODE_DEL')
    shell('input','text',value.replace(' ','%s'))
    time.sleep(.4)

def screenshot(name):
    (SHOTS/(name+'.png')).write_bytes(adb('exec-out','screencap','-p',binary=True))
    (OUT/(name+'.xml')).write_text(shell('cat','/sdcard/lesson3-ui.xml'),encoding='utf-8')

def check(name,condition,detail=''):
    checks[:]=[item for item in checks if item['name'] != name]
    checks.append({'name':name,'passed':bool(condition),'detail':detail})
    print(('PASS ' if condition else 'FAIL ')+name,flush=True)
    (OUT/'checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
    if not condition: raise AssertionError(name+' '+detail)

def start(pkg):
    shell('am','force-stop',pkg)
    # NEW_TASK | CLEAR_TASK даёт действительно чистый старт: в стеке не остаётся
    # внешняя галерея/камера с предыдущего оборванного теста Activity Result.
    shell('am','start','-W','-a','android.intent.action.MAIN','-c','android.intent.category.LAUNCHER',
          '-f','0x10008000','-n',pkg+'/.MainActivity'); time.sleep(2)

def rotate(land=False):
    shell('settings','put','system','accelerometer_rotation','0')
    shell('settings','put','system','user_rotation','1' if land else '0')
    time.sleep(2)

def text_id(id):
    return next((n.attrib.get('text','') for n in nodes() if n.attrib.get('resource-id','').endswith('/'+id)), '')

def run():
    shell('input','keyevent','KEYCODE_WAKEUP'); shell('wm','dismiss-keyguard')
    shell('settings','put','global','window_animation_scale','0')
    shell('settings','put','global','transition_animation_scale','0')
    shell('settings','put','global','animator_duration_scale','0')
    rotate()
    shell('cmd','uimode','night','no')
    shell('logcat','-c')
    for m in ['IntentApp','Sharer','FavoriteBook','SystemIntentsApp','SimpleFragmentApp']:
        apk = next((ROOT/m/'build/outputs/apk/debug').glob('*.apk'))
        check('Install '+m,'Success' in adb('install','-r',str(apk)))
    apk = ROOT/'MireaProject/app/build/outputs/apk/debug/app-debug.apk'
    check('Install MireaProject','Success' in adb('install','-r',str(apk)))
    prefix='ru.mirea.ZubarevVS.lesson3.'
    start(prefix+'intentapp')
    check('IntentApp initial','Время между экранами' in alltext())
    screenshot('01-intent-main')
    click(id='send')
    received=text_id('result')
    check('IntentApp square 25 and timestamp','СОСТАВЛЯЕТ 25' in received and bool(re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',received)),received)
    screenshot('02-intent-result')
    rotate(True)
    check('IntentApp result survives rotation',text_id('result')==received)
    screenshot('03-intent-landscape')
    rotate()
    click(id='back')
    check('IntentApp displays exact sent time',re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',received).group() in text_id('time'))

    start(prefix+'favoritebook')
    check('FavoriteBook initial','Тут появится' in text_id('textViewBook'))
    click(id='open')
    check('FavoriteBook developer fields',bool(text_id('developer_book')) and bool(text_id('developer_quote')))
    screenshot('04-book-input')
    click(id='send')
    check('FavoriteBook rejects empty fields',any(n.attrib.get('resource-id','').endswith('/book_name') for n in nodes()))
    type_field('book_name','Practice Book')
    type_field('quote','Test quote')
    shell('input','keyevent','KEYCODE_BACK');time.sleep(.4)
    click(id='send')
    result=text_id('textViewBook')
    check('FavoriteBook returns entered data','Practice Book' in result and 'Test quote' in result,result)
    screenshot('05-book-result')
    rotate(True)
    check('FavoriteBook result survives rotation',text_id('textViewBook')==result)
    rotate()
    click(id='open'); click(id='cancel')
    check('FavoriteBook cancellation preserves result',text_id('textViewBook')==result)

    start(prefix+'sharer')
    click(id='share')
    chooser=alltext()
    check('Sharer chooser opens','Mirea' in chooser or 'Sharing' in chooser or 'Nearby' in chooser or 'Выбор' in chooser,chooser[:300])
    screenshot('06-share-chooser')
    try:
        click(contains='Sharer')
        check('Sharer receives shared text',text_id('received')=='Mirea')
    except RuntimeError:
        shell('input','keyevent','KEYCODE_BACK')
        shell('am','start','-a','android.intent.action.SEND','-t','text/plain','--es','android.intent.extra.TEXT','Practice3Test','-n',prefix+'sharer/.ShareActivity')
        time.sleep(1)
        check('Sharer exported receiver reads text',text_id('received')=='Practice3Test')
    screenshot('07-share-received')
    start(prefix+'sharer');click(id='pick')
    check('Sharer opens image picker',not bool(text_id('picked')),alltext()[:200])
    screenshot('08-image-picker')
    shell('input','keyevent','KEYCODE_BACK'); time.sleep(1)
    check('Sharer picker cancellation','отменён' in text_id('picked'))
    screenshot('09-sharer-main')

    start(prefix+'systemintentsapp');click(id='call')
    check('ACTION_DIAL opens number','89811112233' in alltext().replace(' ','').replace('-',''),alltext()[:200])
    screenshot('10-system-dial')
    shell('input','keyevent','KEYCODE_BACK');time.sleep(1)
    start(prefix+'systemintentsapp');click(id='browser');time.sleep(2)
    check('ACTION_VIEW browser launches','chrome' in shell('dumpsys','activity','activities').lower())
    screenshot('11-system-browser')
    start(prefix+'systemintentsapp');click(id='maps');time.sleep(2)
    activities=shell('dumpsys','activity','activities')
    check('Geo URI launches installed Google Maps','com.google.android.apps.maps' in activities)
    screenshot('12-system-map')

    start(prefix+'simplefragmentapp')
    check('Fragment first portrait','Первый фрагмент' in alltext())
    screenshot('13-fragment-first')
    click(id='btnSecondFragment')
    check('Fragment replace second','Второй фрагмент' in alltext() and 'Первый фрагмент' not in alltext())
    type_field('note','Rotation note');shell('input','keyevent','KEYCODE_BACK')
    click(id='btnFirstFragment')
    type_field('note','First note');shell('input','keyevent','KEYCODE_BACK')
    click(id='btnSecondFragment')
    check('Second fragment retains text after switching',text_id('note')=='Rotation note')
    click(id='btnFirstFragment')
    check('First fragment retains independent text',text_id('note')=='First note')
    click(id='btnSecondFragment')
    screenshot('14-fragment-second')
    rotate(True)
    texts=alltext()
    check('Fragments both landscape','Первый фрагмент' in texts and 'Второй фрагмент' in texts)
    check('Fragment active text survives portrait to landscape','Rotation note' in texts,texts)
    check('Both independent fragment notes survive rotation','First note' in texts and 'Rotation note' in texts)
    screenshot('15-fragments-landscape')
    rotate()
    check('Selected second restored after landscape','Второй фрагмент' in alltext() and 'Первый фрагмент' not in alltext())
    check('Fragment text survives landscape to portrait','Rotation note' in alltext())
    shell('cmd','uimode','night','yes');time.sleep(1)
    check('Fragment night theme no crash','Второй фрагмент' in alltext())
    screenshot('16-fragment-dark')
    shell('cmd','uimode','night','no');time.sleep(1)

    pkg='ru.mirea.ZubarevVS.mireaproject'
    start(pkg)
    check('MireaProject data screen','Кибербезопасность' in alltext() and 'Безопасный код' in alltext())
    screenshot('17-mirea-data')
    shell('input','swipe','540','1800','540','500','400');time.sleep(.5)
    check('MireaProject data scrolls','Пример рабочего процесса' in alltext())
    screenshot('18-mirea-data-scroll')
    click(desc='Open navigation drawer')
    check('Drawer includes both destinations','Браузер' in alltext() and 'БИСО-02-22' in alltext())
    screenshot('19-mirea-drawer')
    shell('input','keyevent','KEYCODE_BACK');time.sleep(.5)
    check('Back closes drawer',not any(n.attrib.get('resource-id','').endswith('/navView') for n in nodes()))
    click(desc='Open navigation drawer');click(text='Браузер')
    check('WebView destination','Открыть' in alltext() and bool(text_id('url')))
    for i in range(10):
        if text_id('status') != 'Загрузка страницы…': break
        time.sleep(2)
    screenshot('20-web-default')
    check('WebView default URL is MIREA','mirea.ru' in text_id('url'),text_id('url'))
    type_field('url','https://example.com');shell('input','keyevent','KEYCODE_BACK');click(id='go')
    for i in range(10):
        if 'Example Domain' in alltext(): break
        time.sleep(2)
    check('WebView loads example.com','Example Domain' in alltext(),alltext()[:300])
    screenshot('21-web-example')
    rotate(True)
    check('WebView URL survives rotation','example.com' in text_id('url'))
    screenshot('22-web-landscape')
    rotate()
    click(id='backPage');time.sleep(2)
    check('WebView back history','mirea.ru' in text_id('url'),text_id('url'))
    click(desc='Open navigation drawer');click(text='Кибербезопасность')
    shell('cmd','uimode','night','yes');time.sleep(1)
    check('MireaProject dark theme','Кибербезопасность' in alltext())
    screenshot('23-mirea-dark')
    shell('cmd','uimode','night','no');rotate()
    log=shell('logcat','-d','-b','crash')
    (OUT/'crash-log.txt').write_text(log,encoding='utf-8')
    check('No app fatal exception','FATAL EXCEPTION' not in log,log[-600:])
    print('Completed',len(checks),'checks',flush=True)

if __name__=='__main__':
    try: run()
    except Exception as e:
        (OUT/'failure.txt').write_text(str(e),encoding='utf-8')
        try: xml();screenshot('failure')
        except Exception: pass
        raise

"""Подготавливает отчёты по фактическим JSON, lint и Gradle логам; применяются в IDE."""
from pathlib import Path
import json,re,datetime,xml.etree.ElementTree as ET
import prepare_audit as a

ROOT=Path.cwd()
DAY='audit-2026-10-09'
NOTES={
'Lesson1':'Добавлены меню выбора всех макетов, восстановление выбранного макета и результата ButtonClicker, учёт клавиатуры в Insets. Шаблон номера X заменён на5. Ландшафтные шесть кнопок, шесть типов контролов, обе обработки событий и состояние визуально проверены. Начальная ошибка тестового селектора из-за преобразования текста кнопок в верхний регистр исправлена в тесте; она не была ошибкой приложения. Один прогон lint завершился отказом доступа к промежуточному XML; последовательная чистая сборка в Studio прошла успешно. Полезные модульные сценарии проверены на эмуляторе, исходный JUnit тест подтверждает только 2+2.',
'Lesson2':'Проверены шесть модулей, Home/Back/поворот и реальные lifecycle журналы, передача ФИО/строки, пустой текст и пробелы в Toast, chooser и браузер, отказ/разрешение уведомлений и обновление одной записи Mirea, три ответа AlertDialog, дата/время/Snackbar, ProgressDialog, светлая/тёмная тема. Debug в Android Studio реально остановился в onClickCount: text=MIREA, count=5; F8 сформировал message, F9 продолжил выполнение. Точка останова удалена.',
'Lesson3':'В IntentApp квадрат5 вычисляется арифметически. SimpleFragmentApp теперь сохраняет ввод обоих фрагментов при переключении и повороте. Для MireaProject добавлена компактная панель управления WebView в layout-land. Проведены проверки действительных системных приложений, двух Activity, двух Fragment и Navigation Drawer/WebView. Личные значения FavoriteBook пока требуют ответа владельца: заглушка «ТРЕБУЕТСЯ ЗАПОЛНИТЬ» не считается выполненной персонализацией.'
}

def build_evidence():
 found=[]
 for logfile in (Path.home()/'.gradle/daemon/9.6.0').glob('daemon-*.out.log'):
  current=None;lines=[]
  for line in logfile.read_text(encoding='utf-8',errors='replace').splitlines():
   if 'Daemon is about to start building Build{' in line:
    match=re.search(r'currentDir=(.*?)\}',line)
    current=match.group(1).replace('\\','/') if match else None
    lines=[]
   if current and current.startswith(ROOT.as_posix()):
    if line.startswith(('BUILD ','FAILURE:','Execution failed for task','> java.io.FileNotFoundException','<ijLog>')):
     lines.append(line)
    if line.startswith('BUILD '):
     found.append((current,lines.copy()))
 return found

def run():
 builds=build_evidence()
 for project in ('Lesson1','Lesson2','Lesson3'):
  out=ROOT/project/'verification'/DAY
  results=json.loads((out/'checks.json').read_text(encoding='utf-8')) if (out/'checks.json').exists() else []
  passed=sum(bool(r['passed']) for r in results)
  lint=[]
  for f in (ROOT/project).rglob('lint-results-debug.xml'):
   if project=='Lesson3' and 'MireaProject' in f.parts:continue
   tree=ET.parse(f);issues=list(tree.getroot())
   errors=[n for n in issues if n.get('severity') in ('Error','Fatal')]
   warnings=[n for n in issues if n.get('severity')=='Warning']
   lint.append((f.relative_to(ROOT/project).as_posix(),len(errors),len(warnings),sorted({n.get('id','') for n in warnings})))
  if project=='Lesson3':
   f=ROOT/project/'MireaProject/app/build/reports/lint-results-debug.xml'
   if f.exists():
    issues=list(ET.parse(f).getroot())
    lint.append((f.relative_to(ROOT/project).as_posix(),sum(n.get('severity') in ('Error','Fatal') for n in issues),sum(n.get('severity')=='Warning' for n in issues),sorted({n.get('id','') for n in issues if n.get('severity')=='Warning'})))
  text=f'# Проверка {project} — 09.10.2026\n\nФактический статус сценариев: **{passed}/{len(results)} PASS**. Этот счётчик включает установку/запуск и отдельные проверки поведения; это не число выполненных пунктов PDF и не число Java unit tests.\n\n'
  text+='Проверка проведена в установленной Android Studio на Pixel_9, API35 Google Play x86_64, emulator-5554. Исходники исправлялись через редактор/MCP Android Studio. Gradle Sync, сборки, Run и Debug выполнялись в IDE. Для повторяемых действий устройства использован ADB/UIAutomator из установленного SDK. SDK, AVD, зависимости и APK остаются доступны. Недостающих системных приложений/SDK компонентов в выбранном образе не выявлено.\n\n'
  text+='## Изменения и проверенные сценарии\n\n'+NOTES[project]+'\n\n'
  if project=='Lesson3':
   text+='## Открытый личный пункт FavoriteBook\n\nМетодичка, стр.16, требует именно книгу и цитату разработчика. Запрошены название, автор и точная цитата владельца. До ответа `developer_book` и `developer_quote` остаются заглушками. Проверка «developer fields» подтверждает показ переданных полей и работу интерфейса, но **не подтверждает выполнение личного пункта**. Общий статус задания №3: технические сценарии проверены; персонализация FavoriteBook ожидает данных.\n\n'
  text+='## Результаты устройства\n\n| Проверка | Статус | Подробности |\n|---|---|---|\n'
  for r in results:
   name=r.get('check',r.get('name',''))
   text+='| '+a.md_escape(name)+' | '+('PASS' if r['passed'] else 'FAIL')+' | '+a.md_escape(r.get('detail',''))+' |\n'
  text+='\n## Статическая проверка\n\n| Lint отчёт | Ошибки | Предупреждения | Категории предупреждений |\n|---|---:|---:|---|\n'
  for path,e,w,ids in lint:text+=f'| [{path}](../../{path}) | {e} | {w} | '+', '.join(ids)+' |\n'
  text+='\nПредупреждения перечислены отдельно: рекомендации обновить SDK/версии, hardcoded текст примеров и устаревший учебный API не равны отказу сборки. В этой проверке не выполнялись публикация в Google Play, тестирование на всех версиях Android или физическом телефоне. ProgressDialog и некоторые Bundle API сохранены ради совместимости с учебным кодом и minSdk26.\n\n'
  relevant=[(p,l) for p,l in builds if p==str(ROOT/project).replace('\\','/') or project=='Lesson3' and p==str(ROOT/project/'MireaProject').replace('\\','/')]
  text+='## Доказательства сборок IDE\n\nНиже фактические результаты Gradle daemon для данного каталога, включая неуспешный первоначальный прогон, если он был. После правок исходники компилировались в Android Studio: сохранёнными Gradle конфигурациями Verify и build_project. Отдельный вложенный MireaProject проверялся собственной конфигурацией Verify MireaProject.\n\n```text\n'
  for path,lines in relevant:text+=path+'\n'+'\n'.join(lines)+'\n\n'
  text+='```\n\n## Скриншоты и журналы\n\n'
  for f in sorted((out/'screenshots').glob('*')):text+=f'- [{f.name}](screenshots/{f.name})\n'
  text+='\n[checks.json](checks.json) содержит машинный результат; XML рядом со скриншотами фиксирует реальные ID, тексты и bounds интерфейса. Журналы lifecycle/crash в этом каталоге относятся к текущему прогону. Скриншоты `failure`/начальная ошибка селектора — историческая диагностика; финальный статус берётся из checks.json.\n\n'
  text+='## Код и защита\n\n[Сценарий защиты](../../ИНСТРУКЦИЯ_ПО_ЗАЩИТЕ.md) • [Подробный разбор](../../РАЗБОР_КОДА.md).\n'
  f=out/'ОТЧЁТ.md';parts=[]
  a.add_patch(parts,f.relative_to(ROOT/project).as_posix(),f.read_text(encoding='utf-8') if f.exists() else None,text)
  (a.OUT/(project+'-report.patch')).write_text('*** Begin Patch\n'+''.join(parts)+'*** End Patch\n',encoding='utf-8')
  print(project,passed,len(results),'lint:',[(e,w) for _,e,w,_ in lint])

if __name__=='__main__':run()

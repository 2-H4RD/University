"""Read-only QA of current explanations and links; never edits Android sources."""
from pathlib import Path
from urllib.parse import unquote
import re,json

root=Path.cwd()
errors=[]
java_count=0
docs=[]
for lesson in ('Lesson1','Lesson2','Lesson3','Lesson3/MireaProject'):
    p=root/lesson
    doc=p/'РАЗБОР_КОДА.md'
    data=doc.read_text(encoding='utf-8')
    docs.extend([doc,p/'README.md'])
    if '/' not in lesson:
        docs.extend([p/'ИНСТРУКЦИЯ_ПО_ЗАЩИТЕ.md',p/'verification/audit-2026-10-09/ОТЧЁТ.md'])
    for module in p.iterdir():
        if not module.is_dir() or not (module/'src/main').exists():continue
        for source_root in ('src/main','src/test','src/androidTest'):
            for f in (module/source_root).rglob('*.java'):
                relative=f.relative_to(p).as_posix()
                marker='### '+relative+'\n'
                if marker not in data:
                    errors.append('Missing Java section: '+str(f));continue
                section=data.split(marker,1)[1].split('\n### ',1)[0]
                blocks=re.findall(r'```java\n(.*?)```',section,re.S)
                expected='\n'.join(f'{i:4} | {line}' for i,line in enumerate(f.read_text(encoding='utf-8').splitlines(),1))
                if not any(b.rstrip('\n')==expected for b in blocks):
                    errors.append('Numbered listing differs: '+str(f))
                java_count+=1
for doc in docs:
    data=re.sub(r'```.*?```','',doc.read_text(encoding='utf-8'),flags=re.S)
    for raw in re.findall(r'\]\(([^)]+)\)',data):
        url=raw.strip().strip('<>')
        if url.startswith(('http:','https:','#','codex:')):continue
        target=unquote(url.split('#',1)[0])
        if not (doc.parent/target).exists():errors.append('Broken link: '+str(doc)+' -> '+target)
for lesson in ('Lesson1','Lesson2','Lesson3'):
    results=json.loads((root/lesson/'verification/audit-2026-10-09/checks.json').read_text(encoding='utf-8'))
    assert all(r['passed'] for r in results), lesson
    print(lesson, len(results), 'PASS')
print('Java listings:',java_count,'Documents:',len(docs))
for error in errors:print(error)
if errors:raise SystemExit(1)
print('All numbered Java listings and local links match current files.')

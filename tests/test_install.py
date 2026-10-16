"""Exercise an independent consumer using the public install/render path."""
import json,subprocess,sys,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def test_consumer(tmp_path):
 n=json.loads((R/'src/theme.json').read_text())['name']
 subprocess.run([sys.executable,str(R/'scripts/build.py')],check=True)
 (tmp_path/'_smalldocs.yml').write_text('project:\n  type: website\ntheme: '+n+'\n')
 published=tmp_path/'published'; shutil.copytree(R/'_extensions',published/'_extensions')
 subprocess.run(['git','init','-q',str(published)],check=True)
 subprocess.run(['git','add','.'],cwd=published,check=True)
 subprocess.run(['git','-c','user.name=Theme test','-c','user.email=test@example.org','commit','-qm','Published extension'],cwd=published,check=True)
 subprocess.run([sys.executable,'-m','smalldocs.cli','add',str(published)],cwd=tmp_path,check=True)
 (tmp_path/'index.qmd').write_text('# A consumer\n\nA [real link](https://example.org) and `inline code`.\n\n```python\nprint("Hello")\n```\n')
 subprocess.run([sys.executable,'-m','smalldocs.cli','render',str(tmp_path),'--strict'],check=True)
 out=tmp_path/'_site'; html=(out/'index.html').read_text()
 assert n+'.css' in html
 css=out/'site_libs/themes'/n/(n+'.css')
 assert css.is_file()
 import re
 for ref in re.findall(r'url\(fonts/([^)]*)\)',css.read_text()):
  assert (css.parent/'fonts'/ref).is_file(),ref
 assert '@import' not in css.read_text()

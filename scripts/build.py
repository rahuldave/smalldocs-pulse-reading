"""Rebuild the complete installable theme from pinned, local source files."""
import json,re,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def build():
 t=json.loads((R/'src/theme.json').read_text()); n=t['name']; out=R/'_extensions'/n
 out.mkdir(parents=True,exist_ok=True)
 css=(R/'vendor/bootswatch/bootstrap.min.css').read_text()
 css=re.sub(r'@import\s+url\([^)]*\)\s*;','',css)
 css=re.sub(r'/\*# sourceMappingURL=.*?\*/','',css)
 palette=':root, [data-bs-theme] {\n'+''.join('--r-'+k+': '+v+';\n' for k,v in t['palette'].items())+'}\n'
 (out/(n+'.css')).write_text(css+'\n'+(R/'src/fonts.css').read_text()+'\n'+palette+(R/'src/reading.css').read_text()+(R/'src/design.css').read_text())
 shutil.copytree(R/'vendor/fonts',out/'fonts',dirs_exist_ok=True)
 shutil.copy2(R/'vendor/bootswatch/LICENSE',out/'BOOTSWATCH-LICENSE')
 shutil.copy2(R/'LICENSE',out/'READING-LICENSE')
 shutil.copy2(R/'src/smalldocs.yml',out/'smalldocs.yml')
 print('Built '+n)
if __name__=='__main__':build()

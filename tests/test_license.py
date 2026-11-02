"""Check that the licence names this theme, its upstream and the fonts it ships, as vendor/ holds them."""
import json,re,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def family(path):
 "The family of a TrueType font: name ID 16, else name ID 1, without a weight at the end."
 data=path.read_bytes(); names={}
 for i in range(struct.unpack('>H',data[4:6])[0]):
  tag,_,offset,_=struct.unpack('>4sIII',data[12+16*i:28+16*i])
  if tag!=b'name': continue
  _,count,strings=struct.unpack('>HHH',data[offset:offset+6])
  for j in range(count):
   plat,_,_,nid,length,off=struct.unpack('>6H',data[offset+6+12*j:offset+18+12*j])
   raw=data[offset+strings+off:offset+strings+off+length]
   names.setdefault(nid,raw.decode('utf-16-be' if plat in (0,3) else 'latin-1'))
 return re.sub(r'( (Thin|ExtraLight|Light|Medium|SemiBold|Bold|ExtraBold|Black|Italic))+$','',names.get(16,names[1]))
def families(): return {family(f) for f in (R/'vendor/fonts').glob('*.ttf')}
def header():
 "The versions, the theme and the copyright years in the header of the vendored Bootswatch CSS."
 css=(R/'vendor/bootswatch/bootstrap.min.css').read_text()[:2000]
 find=lambda p:re.search(p,css).group(1)
 return {'bootswatch':find(r'Bootswatch v(\S+)'),'theme':find(r'Theme: (\S+)'),'bootswatch_years':find(r'Copyright (\S+) Thomas Park'),
  'bootstrap':find(r'Bootstrap +v(\S+)'),'bootstrap_years':find(r'Copyright (\S+) The Bootstrap Authors')}
def squash(text): return re.sub(r'[^a-z]','',text.lower())
def text(): return ' '.join((R/'LICENSE').read_text().split())
def test_license_keeps_the_mit_terms():
 assert 'The above copyright notice and this permission notice shall be included in all copies' in text()
def test_license_names_the_upstream_as_vendored():
 t=text(); h=header(); theme=json.loads((R/'src/theme.json').read_text())
 for part in [theme['title'],theme['upstream'],f"Bootswatch theme {h['theme']} ",f"Copyright (c) {h['bootswatch_years']} Thomas Park",
  f"Bootswatch {h['bootswatch']} builds on Bootstrap {h['bootstrap']} ",f"Copyright (c) {h['bootstrap_years']} The Bootstrap Authors"]:
  assert part in t,part
 assert h['theme']==theme['name'].removesuffix('-reading')
def test_license_names_exactly_the_shipped_fonts():
 m=re.search(r'([A-Z][\w ,]*?) (?:is|are) licensed under the SIL Open Font License 1\.1',text())
 assert m,'no OFL sentence'
 assert set(re.split(r', | and ',m.group(1)))==families()
def test_each_font_family_has_its_ofl_file():
 ofl={squash(f.name.removesuffix('-OFL.txt')) for f in (R/'vendor/fonts').glob('*-OFL.txt')}
 assert {squash(f) for f in families()}==ofl
def test_license_paths_exist():
 for path in re.findall(r'vendor/[\w./*-]*[\w*]',text()):
  assert list(R.glob(path)),path
def test_font_sources_list_exactly_the_shipped_fonts():
 sources=json.loads((R/'vendor/font-sources.json').read_text())
 assert sorted(s['file'] for s in sources)==sorted(f.name for f in (R/'vendor/fonts').glob('*.ttf'))
 for s in sources:
  assert s['family']==family(R/'vendor/fonts'/s['file']),s['file']
  assert f"/s/{squash(s['family'])}/" in s['url'],s['url']

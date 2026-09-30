"""Shared checks for approved Japanese controls with unchanged Chinese display payloads."""
import re,json
OP=re.compile(r'\[(?:chara|live2dName|name|flashEffect|surround|se|bgEffect|wait|freeze|turnEffect):[^\[\]]*\]')
COLOR=re.compile(r'\[text(?:Red|Blue|Yellow|Black):[^\]]*\]')
TEXT={'textLeft','textRight','textCenter','textAvLeft','textAvRight','textAvCenter','narration','progressNarration','Fnarration','fnarration','progressFnarration'}
EXCEPTIONS={'511110-8_Qep4x.json','519020-13_QIB0F.json','520820-9_6HXJQ.json','101506-4_BdcGe.json','103205-5_7xz7k.json'}
SPEECH={'102704-1_yKMiv.json','519601-21_BPssF.json'}
def visible(s):return OP.sub('',s)
def validate_spec(spec,approved):
 name=spec['path'].rsplit('/',1)[-1]
 expected=approved.get(spec['path'])
 if not expected or expected['before']!=spec['before'] or expected['after']!=spec['after']:raise ValueError('File outside approved batch')
 for addr,old,new in spec['operations']:
  if not addr or addr[0]!='story':raise ValueError('Edit outside story')
  if addr[-1]=='id':
   if 'chara' not in addr or type(old) is not int or type(new) is not int:raise ValueError('Unexpected numeric edit')
  elif addr[-1] in TEXT:
   if not isinstance(old,str) or not isinstance(new,str):raise ValueError('Invalid text value')
   if name not in SPEECH|EXCEPTIONS:
    if visible(old)!=visible(new):raise ValueError('Unapproved Chinese change')
    if COLOR.findall(old)!=COLOR.findall(new):raise ValueError('Chinese highlight changed')
  else:raise ValueError('Unapproved field')

def no_added_undefined_references(before,after):
 def scan(d):
  ids=set();named=set();refs=set();nrefs=set()
  def walk(x):
   if isinstance(x,dict):
    for c in x.get('chara',[]):
     if c.get('id'):ids.add(c['id'])
     if c.get('live2dName'):named.add(c['live2dName'])
    for v in x.values():
     if isinstance(v,str):refs.update(map(int,re.findall(r'\[chara:(\d+):',v)));nrefs.update(re.findall(r'\[live2dName:([^:]+):',v))
     elif isinstance(v,(dict,list)):walk(v)
   elif isinstance(x,list):
    for v in x:walk(v)
  walk(d);return refs-ids,nrefs-named
 a,b=scan(json.loads(before)),scan(json.loads(after))
 if (b[0]-a[0]) or (b[1]-a[1]):raise ValueError('New undefined actor reference')

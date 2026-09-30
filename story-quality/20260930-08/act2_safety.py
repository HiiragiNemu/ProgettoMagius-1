"""Validate the two approved Act II text repairs without changing model structure."""
import json,re
TEXT={'textLeft','textRight','textCenter','narration','progressNarration','Fnarration','fnarration','progressFnarration','textAvLeft','textAvRight','textAvCenter'}
def tokens(s):return re.findall(r'\[(?!text(?:Red|Blue|Yellow|Black):)[^\[\]]*\]',s)
def fields(d):return [(('story',g,i,k),v) for g,a in d['story'].items() for i,t in enumerate(a) for k,v in t.items() if k in TEXT and isinstance(v,str)]
def validate_operations(spec,full,name_map):
 sid=spec['path'].rsplit('/',1)[-1].removesuffix('.json')
 assert sid in {'103105-11_32rIq','102502-1_lDVQb'} and sid in full
 expected=41 if sid.startswith('103105') else 52
 assert len(spec['operations'])==expected
 seen=set()
 for a,b,c in spec['operations']:
  assert tuple(a) not in seen and a[0]=='story' and a[-1] in TEXT
  assert isinstance(b,str) and isinstance(c,str) and b!=c
  seen.add(tuple(a))
  if sid.startswith('103105'):assert tokens(b)==tokens(c)
 return expected

def assert_only_recorded_changes(before,after,operations):
 a=json.loads(before);b=json.loads(after);restored=json.loads(after)
 for address,old,new in operations:
  x,y=a,restored
  for k in address[:-1]:x=x[k];y=y[k]
  assert x[address[-1]]==old and y[address[-1]]==new
  y[address[-1]]=old
 assert restored==a
 av,bv=fields(a),fields(b)
 assert [x for x,v in av]==[x for x,v in bv]
 if len(av)==58:
  old=[v for x,v in av];new=[v for x,v in bv]
  assert old[-1]==old[-2] and old[:5]==new[:5]
  assert new[5]=='哟，看来你们确实按昨天的约定@来了啊。'
  assert new[13]=='既然你们能找到结界，@联盟也可以参加战斗哦。'
  for i in range(6,58):
   if i!=13:assert new[i]==old[i-1]
  assert tokens(''.join(old))==tokens(''.join(new))
 else:
  assert len(av)==49
  assert [tokens(v) for x,v in av]==[tokens(v) for x,v in bv]

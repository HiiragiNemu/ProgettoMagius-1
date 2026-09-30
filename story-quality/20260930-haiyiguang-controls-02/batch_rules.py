"""Verify a maintainer name correction or a fully reviewed JP-layout localization."""
import json,re,hashlib
from exact_json import blob,apply
NAME_KEYS={'nameLeft','nameRight','nameCenter','nameNarration','nameFnarration'}
TEXT_KEYS={'textLeft','textRight','textCenter','textAvLeft','textAvRight','textAvCenter','narration','progressNarration','Fnarration','fnarration','progressFnarration'}
OP=re.compile(r'\[(?!text(?:Red|Blue|Yellow|Black):)[^\[\]]*\]')
OLD_NAMES={'アマビエ小阿鲁','阿玛比埃小阿鲁'}
NEW_NAME='海异光小阿鲁'

def core(x):
 if isinstance(x,dict):return {k:core(v) for k,v in x.items() if k not in NAME_KEYS|TEXT_KEYS}
 if isinstance(x,list):return [core(v) for v in x]
 return x

def text_values(x,p=()):
 if isinstance(x,dict):
  for k,v in x.items():
   if isinstance(v,(dict,list)):yield from text_values(v,p+(k,))
   elif isinstance(v,str) and k in TEXT_KEYS:yield p+(k,),v
 elif isinstance(x,list):
  for i,v in enumerate(x):yield from text_values(v,p+(i,))

def rebuild(spec,before,jp_raw=None):
 if blob(before)!=spec['before']:raise ValueError('Published/source baseline mismatch')
 if spec['mode']=='exact_name':
  for address,old,new in spec['operations']:
   if not address or address[0]!='story' or address[-1] not in NAME_KEYS or old not in OLD_NAMES or new!=NEW_NAME:raise ValueError('Outside exact maintainer name authorization')
  candidate=apply(before,spec['operations'])
  assert core(json.loads(before))==core(json.loads(candidate))
  assert list(text_values(json.loads(before)))==list(text_values(json.loads(candidate)))
 elif spec['mode']=='reviewed_jp_layout':
  if jp_raw is None or blob(jp_raw)!=spec['jp_sha']:raise ValueError('Fixed Japanese source mismatch')
  jp=json.loads(jp_raw);candidate=apply(jp_raw,spec['jp_operations']);result=json.loads(candidate)
  if core(jp)!=core(result):raise ValueError('Unauthorized change to Japanese execution layout')
  oldtexts=dict(text_values(jp));newtexts=dict(text_values(result))
  if oldtexts.keys()!=newtexts.keys():raise ValueError('Missing or extra source display slot')
  for path,jtext in oldtexts.items():
   if OP.findall(jtext)!=OP.findall(newtexts[path]):raise ValueError('Executable inline control mismatch')
   if re.search('[\u3041-\u3096\u30a1-\u30fa]',OP.sub('',newtexts[path])):raise ValueError('Unlocalized display payload')
  skeleton=hashlib.sha256(json.dumps(core(result),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  if skeleton!=spec['jp_skeleton_sha256']:raise ValueError('Skeleton fingerprint mismatch')
 else:raise ValueError('Unknown repair mode')
 if blob(candidate)!=spec['after']:raise ValueError('Candidate does not match committed source')
 return candidate

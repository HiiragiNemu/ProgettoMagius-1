"""Content-level invariants for reviewed repeated scenes; no original-language provenance guessing."""
import re,json
OPAQUE=re.compile(r'\[(?!text(?:Red|Blue|Yellow|Black):)[^\[\]]*\]')
TEXT={'textLeft','textCenter','textRight','textAvLeft','textAvCenter','textAvRight','narration','progressNarration','Fnarration','fnarration','progressFnarration'}
def transplant_reviewed_payload(reviewed,before):
 a,b=OPAQUE.findall(reviewed),OPAQUE.findall(before)
 normalize=lambda x:[s.replace('.exp3.json','.exp.json') for s in x]
 if normalize(a)!=normalize(b):raise ValueError('Execution signatures differ; semantic transplant requires review')
 replacements=iter(b);after=OPAQUE.sub(lambda _:next(replacements),reviewed)
 if OPAQUE.findall(after)!=b:raise ValueError('Target execution tokens changed')
 return after

def validate_operations(path,operations):
 for address,before,after in operations:
  if len(address)<4 or address[0]!='story' or address[-1] not in TEXT or not isinstance(before,str) or not isinstance(after,str):raise ValueError('Not a display string edit')
  if path.endswith('/102301-4_Z9WSZ.json'):
   if not before.startswith('chara:100501:effect_emotion_joy_0][se:7222_happy]') or after!='['+before:raise ValueError('Only verified opening bracket can change')
  elif OPAQUE.findall(before)!=OPAQUE.findall(after):raise ValueError('Existing runtime cue was altered')

def body_at(data,path):
 for key in path:data=data[key]
 return data

def verify_display_only(before,after,operations):
 a,b=json.loads(before),json.loads(after)
 for address,old,new in operations:
  node=b
  for k in address[:-1]:node=node[k]
  if node[address[-1]]!=new or body_at(a,address)!=old:raise ValueError('Recorded field mismatch')
  node[address[-1]]=old
 if a!=b:raise ValueError('Other scenario data changed')

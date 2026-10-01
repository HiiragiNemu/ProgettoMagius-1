"""Validation contract: translate display strings without silently changing execution."""
import json,re
TEXT_KEYS={'textSelect','textLeft','textRight','textCenter','textAvLeft','textAvRight','textAvCenter','narration','Fnarration','fnarration','progressNarration','progressFnarration'}
NAME_KEYS={'nameLeft','nameRight','nameCenter','nameNarration','nameFnarration'}
TAGS=re.compile(r'\[[^\[\]]*\]')
COLOR=re.compile(r'^\[text(?:Red|Blue|Yellow|Black):[^\]]*\]$')
def execution_tokens(text):return [t for t in TAGS.findall(text) if not COLOR.fullmatch(t)]
def color_types(text):return [t.split(':',1)[0] for t in TAGS.findall(text) if COLOR.fullmatch(t)]
def validate(original,revised,operations,allowed_name_operations=()):
 allowed_names={tuple(at):(before,after) for at,before,after in allowed_name_operations}
 a=json.loads(original);b=json.loads(revised);restored=json.loads(revised);seen=set()
 for address,before,after in operations:
  key=tuple(address)
  if key in seen or not address or address[0]!='story' or (address[-1] not in TEXT_KEYS and not (address[-1] in NAME_KEYS and allowed_names.get(key)==(before,after))):raise ValueError('Unapproved edit path')
  seen.add(key)
  if not isinstance(before,str) or not isinstance(after,str) or before==after:raise ValueError('Invalid display edit')
  if execution_tokens(before)!=execution_tokens(after):raise ValueError('Executable tag sequence changed')
  if color_types(before)!=color_types(after):raise ValueError('Highlight identity changed')
  x,y,z=a,b,restored
  for p in address[:-1]:x=x[p];y=y[p];z=z[p]
  if x[address[-1]]!=before or y[address[-1]]!=after:raise ValueError('Baseline/revised value mismatch')
  z[address[-1]]=before
 if restored!=a:raise ValueError('Unrecorded JSON change')
 return True

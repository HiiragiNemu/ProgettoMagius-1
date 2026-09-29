"""Validation shared by source staging tests and the public release builder."""
import json,re
NAME_FIELDS={'nameLeft','nameCenter','nameRight','nameNarration','nameFnarration'}
TEXT_FIELDS={'textLeft','textCenter','textRight','textAvLeft','textAvCenter','textAvRight','narration','progressNarration','Fnarration','fnarration','progressFnarration'}

def controls(value):
 return [re.sub(r'^(\[text(?:Red|Blue|Yellow|Black):).*\]$',r'\1<display>]',tag,flags=re.S) for tag in re.findall(r'\[[^\[\]]*\]',value)]

def validate_operations(spec,full_review_ids,name_map):
 seen=set()
 for address,before,after in spec['operations']:
  key=tuple(address)
  if key in seen or not isinstance(before,str) or not isinstance(after,str) or before==after:raise ValueError('Invalid duplicate or no-op edit')
  seen.add(key)
  if not address or address[0]!='story':raise ValueError('Outside scenario story')
  if address[-1] in NAME_FIELDS:
   if name_map.get(before)!=after:raise ValueError('Unreviewed exact name mapping')
  elif address[-1] in TEXT_FIELDS:
   sid=spec['path'].rsplit('/',1)[-1].removesuffix('.json')
   if sid not in full_review_ids:raise ValueError('Body edit outside reviewed complete story')
   if controls(before)!=controls(after):raise ValueError('Opaque runtime control modified')
  else:raise ValueError('Non-display scenario edit')
 return len(seen)

def assert_only_recorded_changes(before,after,operations):
 a=json.loads(before);b=json.loads(after)
 for address,old,new in operations:
  x,y=a,b
  for k in address[:-1]:x=x[k];y=y[k]
  if x[address[-1]]!=old or y[address[-1]]!=new:raise ValueError('Recorded value mismatch')
  y[address[-1]]=old
 if a!=b:raise ValueError('Unrecorded semantic change')

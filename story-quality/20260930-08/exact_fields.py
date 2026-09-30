"""Lossless, path-addressed replacement of JSON string values only."""
import json,hashlib

def blob(raw):
 return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()

def string_spans(raw):
 text=raw.decode('utf-8-sig');decoder=json.JSONDecoder();spans={};n=len(text)
 def ws(i):
  while i<n and text[i] in ' \t\r\n':i+=1
  return i
 def walk(i,path):
  i=ws(i);start=i
  if text[i]=='{':
   i=ws(i+1);seen=set()
   if text[i]=='}':return i+1
   while True:
    key,j=decoder.raw_decode(text,i)
    if not isinstance(key,str) or key in seen:raise ValueError('Invalid or duplicate JSON object key')
    seen.add(key);i=ws(j)
    if text[i]!=':':raise ValueError('Missing colon')
    i=ws(walk(i+1,path+(key,)))
    if text[i]=='}':return i+1
    if text[i]!=',':raise ValueError('Missing comma')
    i=ws(i+1)
  if text[i]=='[':
   i=ws(i+1);k=0
   if text[i]==']':return i+1
   while True:
    i=ws(walk(i,path+(k,)));k+=1
    if text[i]==']':return i+1
    if text[i]!=',':raise ValueError('Missing array comma')
    i=ws(i+1)
  value,j=decoder.raw_decode(text,i)
  if isinstance(value,str):spans[path]=(start,j,value)
  return j
 if ws(walk(0,()))!=n:raise ValueError('Trailing JSON data')
 return text,spans

def replace_strings(raw,operations):
 text,spans=string_spans(raw);edits=[];seen=set()
 for address,before,after in operations:
  address=tuple(address)
  if address in seen or address not in spans:raise ValueError('Ambiguous replacement address')
  seen.add(address);a,b,current=spans[address]
  if current!=before or not isinstance(after,str) or before==after:raise ValueError('Baseline/replacement mismatch')
  edits.append((a,b,json.dumps(after,ensure_ascii=False)))
 out=text
 for a,b,value in sorted(edits,reverse=True):out=out[:a]+value+out[b:]
 prefix=b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b''
 candidate=prefix+out.encode('utf-8')
 # Undo through the same exact paths and compare the complete object.
 revised=json.loads(candidate);original=json.loads(raw)
 for address,before,after in operations:
  node=revised
  for key in address[:-1]:node=node[key]
  if node[address[-1]]!=after:raise ValueError('Unexpected output at edited path')
  node[address[-1]]=before
 if revised!=original:raise ValueError('Unexpected JSON mutation')
 # Every byte outside selected string tokens is carried forward unchanged.
 return candidate

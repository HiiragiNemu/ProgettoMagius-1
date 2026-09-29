"""Conservative, reversible TXT edits matched to complete source sections."""
import json,re,hashlib
HEADER=re.compile(r'^\s*---\s*\[Section\s+\d+(?:\s*-\s*Branch\s+(\d+))?\]\s*\(Source:\s*([^/\\]+\.json)\)\s*---\s*$')
ROW=re.compile(r'^(\s*)([^:：\r\n]*?)([:：][ \t]?)(.*?)(\r?\n)?$')
KANA=re.compile('[\u3041-\u3096\u30a1-\u30fa]')

def clean(s):
 if not isinstance(s,str):raise ValueError('Non-string text')
 s=s.replace('@','\\n').replace('[br]','\\n').replace('「textBlack:','[textBlack:').replace('『textBlack:','[textBlack:')
 for c in ('Red','Blue','Yellow','Black'):
  s=re.sub(r'\[text'+c+r':(.*?)\]',lambda m:'<'+c.lower()+'>'+m[1]+'</'+c.lower()+'>',s,flags=re.S)
 return re.sub(r'\[.*?\]','',s).strip()

def rows(data,group,allow_interview=False):
 s=data['story'];s={'group_1':s} if isinstance(s,list) else s
 if group not in s or not isinstance(s[group],list):raise ValueError('Missing exact group')
 narr={'narration':None,'fnarration':None};speaker={p:None for p in ('Left','Right','Center')};positions={};output=[]
 for i,t in enumerate(s[group]):
  if not isinstance(t,dict):raise ValueError('Invalid turn')
  if t.get('select'):raise ValueError('Choice requires separate structural review')
  if not allow_interview and any(m in str(t.get('narration','')) for m in ('取材記録','采访记录','取材记录','取材録')):raise ValueError('Interview-format section held')
  for c in t.get('chara',[]):
   if 'pos' in c and c.get('id'):
    p={0:'Left',1:'Center',2:'Right'}.get(c['pos'])
    if p and positions.get(p)!=c['id']:speaker[p]=None;positions[p]=c['id']
  for p in speaker:
   if 'name'+p in t:
    v=t['name'+p]
    if not isinstance(v,str):raise ValueError('Non-string speaker name')
    speaker[p]=(v.strip() or '旁白',i)
  for kind,nk in (('narration','nameNarration'),('fnarration','nameFnarration')):
   if nk in t:
    v=t[nk]
    if not isinstance(v,str):raise ValueError('Non-string narrator name')
    narr[kind]=(v.strip() or '旁白',i)
  def emit(key,kind,identity):
   body=clean(t[key])
   if body:output.append({'index':i,'key':key,'kind':kind,'body':body,'name':identity[0] if identity else None,'name_index':identity[1] if identity else None})
  for kind,keys in (('narration',('narration','progressNarration')),('fnarration',('Fnarration','fnarration','progressFnarration'))):
   active=[k for k in keys if t.get(k)]
   if len(active)>1:raise ValueError('Ambiguous narration alias')
   if active:emit(active[0],kind,narr[kind])
  had=False
  for p in ('Left','Right','Center'):
   active=[k for k in ('text'+p,'textAv'+p) if t.get(k)]
   if len(active)>1:raise ValueError('Ambiguous dialogue alias')
   if active:had=True;emit(active[0],'dialogue',speaker[p])
  if t.get('text') and not had:emit('text','dialogue',(t.get('name') or '旁白',i))
 return output

def safe_name(name):
 return isinstance(name,str) and name and name!='旁白' and len(name)<80 and not KANA.search(name) and not re.search(r'[\[\]@:：\r\n]',name)

def plan(raw,source_reader,name_map,semantic_addresses):
 bom=b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b''
 lines=raw[len(bom):].decode('utf-8').splitlines(keepends=True);result=lines.copy();edits=[];held=[];inputs={}
 headers=[]
 for i,line in enumerate(lines):
  m=HEADER.match(line.rstrip('\r\n'))
  if m:headers.append((i,m[2],'group_'+(m[1] or '1')))
 if not headers:return raw,[],[{'reason':'No precise section headers'}],{}
 for n,(start,filename,group) in enumerate(headers):
  end=headers[n+1][0] if n+1<len(headers) else len(lines)
  try:
   old_bytes,new_bytes,source_path,source_sha=source_reader(filename)
   inputs[source_path]=source_sha
   before=rows(json.loads(old_bytes),group);after=rows(json.loads(new_bytes),group)
   if [(r['index'],r['key']) for r in before]!=[(r['index'],r['key']) for r in after]:raise ValueError('Source event structure changed')
   matches=[(i,ROW.match(lines[i])) for i in range(start+1,end) if lines[i].strip()]
   if any(m is None for _,m in matches) or [m[4] for _,m in matches]!=[r['body'] for r in before]:raise ValueError('Body sequence differs; existing wording preserved')
   for (i,m),a,b in zip(matches,before,after):
    old=m[2];new=old;body=m[4];kind=None
    if a['kind'] in ('narration','fnarration') and old=='旁白' and safe_name(b['name']):new=b['name'];kind='narrator'
    elif old in name_map and a['name']==old and b['name']==name_map[old] and safe_name(b['name']):new=b['name'];kind='localized_name'
    if body!=b['body']:
     if (filename,group,a['index'],a['key']) not in semantic_addresses:raise ValueError('Unapproved body change')
     body=b['body'];kind='semantic'
    if new==old and body==m[4]:continue
    updated=m[1]+new+m[3]+body+(m[5] or '')
    result[i]=updated;edits.append({'line':i+1,'source':filename,'source_path':source_path,'source_sha':source_sha,'group':group,'index':a['index'],'key':a['key'],'kind':kind,'before_name':old,'after_name':new,'body_sha256_before':hashlib.sha256(m[4].encode()).hexdigest(),'body_sha256_after':hashlib.sha256(body.encode()).hexdigest(),'before_line':lines[i],'after_line':updated})
  except (ValueError,KeyError,FileNotFoundError) as e:
   # Discard every edit from a held section, never publish half a matched block.
   result[start:end]=lines[start:end];edits=[e for e in edits if not(start<e['line']<=end)]
   held.append({'source':filename,'group':group,'reason':str(e)})
 undo=result.copy()
 for e in edits:
  assert undo[e['line']-1]==e['after_line'];undo[e['line']-1]=e['before_line']
 assert bom+''.join(undo).encode('utf-8')==raw,'Non-addressed byte modification'
 return bom+''.join(result).encode('utf-8'),edits,held,inputs

"""Exact complete-section matching for legacy expanded interview title cards."""
import json,re,hashlib
try:
 from .prefix_exact import rows,ROW,HEADER,clean,safe_name
 from .interview_layout import is_interview_marker,interview_names
except ImportError:
 from prefix_exact import rows,ROW,HEADER,clean,safe_name
 from interview_layout import is_interview_marker,interview_names

def get(d,a):
 for k in a:d=d[k]
 return d

def events(data,group):
 base=rows(data,group,allow_interview=True);result=[]
 source=data['story'];source={'group_1':source} if isinstance(source,list) else source
 for row in base:
  raw=source[group][row['index']][row['key']]
  if row['key']=='narration' and is_interview_marker(raw):
   result.append({'layout':True,'body':'―― 取材记录 ――','name':None,'index':row['index'],'key':row['key']})
   for name in interview_names(clean(raw)):result.append({'layout':True,'body':name,'name':'旁白','index':row['index'],'key':row['key']})
  else:result.append(row|{'layout':False})
 return result

def match_section(lines,start,end,records):
 cursor=start;matched=[]
 for row in records:
  while cursor<end and not lines[cursor].strip():cursor+=1
  if cursor>=end:raise ValueError('Missing source row')
  first=cursor;parts=row['body'].split('\n')
  if row['layout'] and row['name'] is None:
   if lines[cursor].rstrip('\r\n')!=parts[0]:raise ValueError('Interview header layout differs')
   m=None
  else:
   m=ROW.match(lines[cursor]);
   if m is None or m[4]!=parts[0]:raise ValueError('Whole-section body differs')
  cursor+=1
  for part in parts[1:]:
   if cursor>=end or lines[cursor].rstrip('\r\n')!=part:raise ValueError('Multi-line body differs')
   cursor+=1
  matched.append((row,first,cursor,m))
 if any(x.strip() for x in lines[cursor:end]):raise ValueError('Extra unaccounted text')
 return matched

def plan_frames(raw,read_source,name_map,allowed_semantics=set()):
 bom=b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b''
 lines=raw[len(bom):].decode('utf-8').splitlines(keepends=True);out=lines.copy();edits=[];held=[];inputs={}
 heads=[]
 for i,line in enumerate(lines):
  m=HEADER.match(line.rstrip('\r\n'))
  if m:heads.append((i,m[2],'group_'+(m[1] or '1')))
 for h,(start,filename,group) in enumerate(heads):
  end=heads[h+1][0] if h+1<len(heads) else len(lines)
  try:
   old,new,path,sha=read_source(filename);inputs[path]=sha
   a=events(json.loads(old),group);b=events(json.loads(new),group)
   if [(x['index'],x['key'],x['layout']) for x in a]!=[(x['index'],x['key'],x['layout']) for x in b]:raise ValueError('Layout or event shape changed')
   matched=match_section(lines,start+1,end,a);section_edits=[]
   for (before,i,j,m),after in zip(matched,b):
    if before['layout']:continue
    old_name=m[2];new_name=old_name;body=before['body'];newbody=after['body'];kind=None
    if old_name in name_map and after['name']==name_map[old_name] and safe_name(after['name']):new_name=after['name'];kind='localized_name'
    elif old_name=='旁白' and after['kind'] in ('narration','fnarration') and safe_name(after['name']):new_name=after['name'];kind='narrator'
    if body!=newbody:
     if (filename,group,before['index'],before['key']) not in allowed_semantics:raise ValueError('Body edit outside review')
     if '\n' in body or '\n' in newbody:raise ValueError('Physical multi-line body edit held')
     kind='semantic'
    if new_name==old_name and body==newbody:continue
    replacement=m[1]+new_name+m[3]+newbody.split('\n')[0]+(m[5] or '')
    section_edits.append({'line':i+1,'source':filename,'source_path':path,'source_sha':sha,'group':group,'index':before['index'],'key':before['key'],'kind':kind,'before_name':old_name,'after_name':new_name,'before_line':lines[i],'after_line':replacement,'body_sha256_before':hashlib.sha256(body.encode()).hexdigest(),'body_sha256_after':hashlib.sha256(newbody.encode()).hexdigest()})
   for e in section_edits:out[e['line']-1]=e['after_line']
   edits.extend(section_edits)
  except (ValueError,KeyError,FileNotFoundError) as ex:held.append({'source':filename,'group':group,'reason':str(ex)})
 undo=out.copy()
 for e in edits:undo[e['line']-1]=e['before_line']
 assert bom+''.join(undo).encode()==raw
 return bom+''.join(out).encode(),edits,held,inputs

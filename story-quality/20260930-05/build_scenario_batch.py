"""Build and independently validate one source-committed scenario batch."""
from pathlib import Path,PurePosixPath
import copy,json,hashlib,zipfile,zlib
from exact_fields import blob,replace_strings
NAMES=('cn_scenario_update.zip','cn_scenario_update_manifest.json','manifest.json','version_scenario.json')

def identity(path):
 h=hashlib.sha256();m=hashlib.md5();size=0
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b);m.update(b);size+=len(b)
 return {'size':size,'sha256':h.hexdigest(),'md5':m.hexdigest()}

def save(path,obj):
 Path(path).parent.mkdir(parents=True,exist_ok=True)
 Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')

def metadata(directory,version):
 directory=Path(directory);p=identity(directory/NAMES[0]);v=json.loads((directory/NAMES[3]).read_bytes())
 assert v=={'version':version,'size':p['size'],'md5':p['md5']},'Version gate mismatch'
 m=json.loads((directory/NAMES[1]).read_bytes())
 assert m['version']==version and m['zip_size']==p['size'] and m['zip_md5']==p['md5']
 with zipfile.ZipFile(directory/NAMES[0]) as z:
  assert len(z.namelist())==len(set(z.namelist()))==14251 and z.testzip() is None
  files={i.filename:{'size':i.file_size,'crc32':f'{i.CRC:08x}'} for i in z.infolist() if not i.is_dir()}
  assert len(files)==14233 and m['files']==files
  assert m['file_count']==len(files) and m['total_size']==sum(x['size'] for x in files.values())
 g=json.loads((directory/NAMES[2]).read_bytes())[NAMES[0]];cs=g['chunk_size'];assert 0<cs<=64*1024*1024
 with (directory/NAMES[0]).open('rb') as f:chunks=[hashlib.md5(b).hexdigest() for b in iter(lambda:f.read(cs),b'')]
 assert g['size']==p['size'] and g['chunks']==chunks
 return p

def build(base,out,plan,previous):
 base=Path(base);out=Path(out);out.mkdir(parents=True,exist_ok=True)
 p=metadata(base,plan['base_version']);assert p['sha256']==plan['base_package_sha256']
 specs={x['path']:x for x in plan['runtime_files']};assert len(specs)==plan['changed_runtime_scripts']
 preserved={x['path']:x['git_blob'] for r in previous for x in r['files']};assert len(preserved)==37
 files={};records=[];overlap=[]
 with zipfile.ZipFile(base/NAMES[0]) as old,zipfile.ZipFile(out/NAMES[0],'w',zipfile.ZIP_DEFLATED,compresslevel=9) as new:
  assert set(specs)<=set(old.namelist())
  for i in old.infolist():
   parts=PurePosixPath(i.filename);assert not parts.is_absolute() and '..' not in parts.parts
   raw=old.read(i.filename);updated=raw
   if i.filename in preserved:assert blob(raw)==preserved[i.filename]
   if i.filename in specs:
    s=specs[i.filename];assert blob(raw)==s['before']
    for address,before,after in s['operations']:
     if address[-1] not in ('nameLeft','nameCenter','nameRight','nameNarration','nameFnarration'):
      assert i.filename.endswith('/310371-3.json') and address==['story','group_1',33,'textRight']
      assert before=='既然这样……就别叫我里见小姐，@叫我小那由他吧。'
      assert after=='既然这样……就不叫你里见小姐，@改叫小那由他啦。'
    updated=replace_strings(raw,s['operations']);assert blob(updated)==s['after']
    if i.filename in preserved:
     assert all(op[0][-1].startswith('name') and any('\u3041'<=c<='\u3096' or '\u30a1'<=c<='\u30fa' for c in op[1]) for op in s['operations'])
     overlap.append({'path':i.filename,'additional_untranslated_names':len(s['operations'])})
    records.append({'path':i.filename,'before':s['before'],'git_blob':s['after'],'changed_fields':len(s['operations'])})
   if i.is_dir():assert raw==b'';new.writestr(copy.copy(i),updated)
   else:
    assert i.filename.startswith('madomagi/resource/scenario/json/')
    new.writestr(copy.copy(i),updated,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    files[i.filename]={'size':len(updated),'crc32':f'{zlib.crc32(updated)&0xffffffff:08x}'}
  new.comment=old.comment
 unchanged=0
 with zipfile.ZipFile(base/NAMES[0]) as old,zipfile.ZipFile(out/NAMES[0]) as new:
  assert old.namelist()==new.namelist() and new.testzip() is None
  for i in old.infolist():
   if i.filename in specs:assert blob(new.read(i.filename))==specs[i.filename]['after']
   else:
    assert old.read(i.filename)==new.read(i.filename)
    unchanged+=not i.is_dir()
 assert unchanged==14233-len(specs)
 p2=identity(out/NAMES[0]);save(out/NAMES[3],{'version':plan['target_version'],'size':p2['size'],'md5':p2['md5']})
 m=json.loads((base/NAMES[1]).read_bytes());m.update(version=plan['target_version'],zip_size=p2['size'],zip_md5=p2['md5'],files=files,file_count=len(files),total_size=sum(x['size'] for x in files.values()),generated=plan['generated_at']);save(out/NAMES[1],m)
 g=json.loads((base/NAMES[2]).read_bytes());cs=g[NAMES[0]]['chunk_size']
 with (out/NAMES[0]).open('rb') as f:chunks=[hashlib.md5(b).hexdigest() for b in iter(lambda:f.read(cs),b'')]
 g[NAMES[0]]={'size':p2['size'],'chunk_size':cs,'chunks':chunks};save(out/NAMES[2],g)
 assert metadata(out,plan['target_version'])==p2
 report={k:plan[k] for k in ('batch','base_version','target_version','reader_commit','cn_patch_commit','changed_name_fields','changed_dialogue_fields','changed_runtime_scripts','generated_at')}
 report.update(schema=1,version=plan['target_version'],status='built_and_validated',base_package=p,package=p2,files=records,unchanged_files=unchanged,prior_corrected_scripts=37,prior_scripts_byte_identical=37-len(overlap),prior_scripts_additional_name_repairs=overlap,prior_corrections_preserved=True,non_display_json_fields_unchanged=True,whole_corpus_review_complete=False,device_rendering_verified=False)
 save(out/'story-quality-report.json',report);return report

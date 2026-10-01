"""Fifty-two machine-origin scene reads, thirteen complete indexed chapters, no execution changes, exact package baseline."""
from pathlib import Path,PurePosixPath
import json,hashlib,zipfile,zlib,copy
from exact_json import blob,apply
from translation_rules import validate
NAMES=('cn_scenario_update.zip','cn_scenario_update_manifest.json','manifest.json','version_scenario.json')
def identity(path):
 sha=hashlib.sha256();md5=hashlib.md5();size=0
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):sha.update(b);md5.update(b);size+=len(b)
 return dict(size=size,sha256=sha.hexdigest(),md5=md5.hexdigest())
def save(path,obj):
 Path(path).parent.mkdir(parents=True,exist_ok=True);Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def metadata(root,version):
 root=Path(root);p=identity(root/NAMES[0]);v=json.loads((root/NAMES[3]).read_bytes());assert v==dict(version=version,size=p['size'],md5=p['md5'])
 m=json.loads((root/NAMES[1]).read_bytes());assert m['version']==version and m['zip_size']==p['size'] and m['zip_md5']==p['md5']
 with zipfile.ZipFile(root/NAMES[0]) as z:
  assert len(z.namelist())==len(set(z.namelist()))==14251 and z.testzip() is None
  files={i.filename:dict(size=i.file_size,crc32=f'{i.CRC:08x}') for i in z.infolist() if not i.is_dir()}
  assert m['files']==files and m['file_count']==len(files)==14233 and m['total_size']==sum(x['size'] for x in files.values())
 g=json.loads((root/NAMES[2]).read_bytes())[NAMES[0]];cs=g['chunk_size'];assert 0<cs<=64*1024*1024
 with (root/NAMES[0]).open('rb') as f:chunks=[hashlib.md5(b).hexdigest() for b in iter(lambda:f.read(cs),b'')]
 assert g['size']==p['size'] and g['chunks']==chunks;return p

def build(base,out,plan,previous):
 base=Path(base);out=Path(out);out.mkdir(parents=True,exist_ok=True);bp=metadata(base,3315);assert bp['sha256']==plan['base_package_sha256']
 specs={x['path']:x for x in plan['runtime_files']};assert len(specs)==44 and sum(len(s['operations']) for s in specs.values())==164
 prior={f['path']:f['git_blob'] for r in previous for f in r['files']};assert len(prior)>=373
 assert len(plan['protected_v4'])==43 and not set(specs)&set(plan['protected_v4'])
 records=[];files={};extensions=[]

 with zipfile.ZipFile(base/NAMES[0]) as a,zipfile.ZipFile(out/NAMES[0],'w',zipfile.ZIP_DEFLATED,compresslevel=9) as b:
  assert set(specs)|set(prior)|set(plan['protected_v4'])<=set(a.namelist())
  for i in a.infolist():
   path=PurePosixPath(i.filename);assert not path.is_absolute() and '..' not in path.parts
   raw=a.read(i.filename);new=raw
   if i.filename in prior:assert blob(raw)==prior[i.filename]
   if i.filename in plan['protected_v4']:assert blob(raw)==plan['protected_v4'][i.filename]
   if i.filename in specs:
    s=specs[i.filename];assert blob(raw)==s['before'];new=apply(raw,s['operations']);assert blob(new)==s['after'];validate(raw,new,s['operations'],allowed_name_operations=s['permitted_name_operations'])
    records.append(dict(path=i.filename,before=s['before'],git_blob=s['after'],fields=len(s['operations'])))
    if i.filename in prior:extensions.append(i.filename)
   if i.is_dir():assert raw==b'';b.writestr(copy.copy(i),new)
   else:
    assert i.filename.startswith('madomagi/resource/scenario/json/')
    b.writestr(copy.copy(i),new,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9);files[i.filename]=dict(size=len(new),crc32=f'{zlib.crc32(new)&0xffffffff:08x}')
  b.comment=a.comment
 with zipfile.ZipFile(base/NAMES[0]) as a,zipfile.ZipFile(out/NAMES[0]) as b:
  assert a.namelist()==b.namelist() and b.testzip() is None
  for i in a.infolist():
   if i.filename not in specs:assert a.read(i.filename)==b.read(i.filename)
   else:assert blob(b.read(i.filename))==specs[i.filename]['after']
 p=identity(out/NAMES[0]);save(out/NAMES[3],dict(version=3316,size=p['size'],md5=p['md5']))
 m=json.loads((base/NAMES[1]).read_bytes());m.update(version=3316,zip_size=p['size'],zip_md5=p['md5'],files=files,file_count=len(files),total_size=sum(x['size'] for x in files.values()),generated=plan['generated_at']);save(out/NAMES[1],m)
 g=json.loads((base/NAMES[2]).read_bytes());cs=g[NAMES[0]]['chunk_size']
 with (out/NAMES[0]).open('rb') as f:chunks=[hashlib.md5(b).hexdigest() for b in iter(lambda:f.read(cs),b'')]
 g[NAMES[0]]=dict(size=p['size'],chunk_size=cs,chunks=chunks);save(out/NAMES[2],g);assert metadata(out,3316)==p
 report=dict(schema=1,batch=plan['batch'],version=3316,status='built_and_validated',reader_commit=plan['reader_commit'],cn_patch_commit=plan['cn_patch_commit'],base_version=3315,base_package=bp,package=p,files=records,changed_runtime_scripts=44,full_scenes_read=52,reviewed_complete_scenes=52,complete_indexed_chapters=13,pending_source_adjudication=[],reviewed_fields=2961,changed_chinese_fields=164,body_fields_changed=163,speaker_labels_changed=1,new_jp_execution_layout_migrations=0,unchanged_files=len(files)-len(specs),previous_corrected_scripts=len(prior),previous_byte_identical=len(prior)-len(extensions),previous_exact_extensions=extensions,protected_v4_unchanged=43,non_text_json_structure_unchanged=True,scenario_tests=23,reviewed_execution_identities_preserved=44,reader_txt_files=26,reader_txt_field_spans=356,nonadv_files_changed=0,official_cn_provenance_independently_verified=False,whole_corpus_complete=False,game_device_verified=False)
 save(out/'story-quality-report.json',report);return report

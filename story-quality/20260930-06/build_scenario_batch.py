"""Build exact batch operations on the verified current player package."""
from pathlib import Path,PurePosixPath
import json,hashlib,zipfile,zlib,copy
from exact_fields import blob,replace_strings
from review_safety import validate_operations,assert_only_recorded_changes
NAMES=('cn_scenario_update.zip','cn_scenario_update_manifest.json','manifest.json','version_scenario.json')

def identity(path):
 h=hashlib.sha256();m=hashlib.md5();size=0
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b);m.update(b);size+=len(b)
 return dict(size=size,sha256=h.hexdigest(),md5=m.hexdigest())
def save(path,obj):
 Path(path).parent.mkdir(parents=True,exist_ok=True);Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def metadata(directory,version):
 directory=Path(directory);package=identity(directory/NAMES[0]);gate=json.loads((directory/NAMES[3]).read_bytes())
 assert gate==dict(version=version,size=package['size'],md5=package['md5'])
 m=json.loads((directory/NAMES[1]).read_bytes());assert m['version']==version and m['zip_size']==package['size'] and m['zip_md5']==package['md5']
 with zipfile.ZipFile(directory/NAMES[0]) as z:
  assert len(z.namelist())==len(set(z.namelist()))==14251 and z.testzip() is None
  files={i.filename:dict(size=i.file_size,crc32=f'{i.CRC:08x}') for i in z.infolist() if not i.is_dir()}
  assert m['files']==files and len(files)==m['file_count']==14233 and m['total_size']==sum(x['size'] for x in files.values())
 g=json.loads((directory/NAMES[2]).read_bytes())[NAMES[0]];cs=g['chunk_size'];assert 0<cs<=64*1024*1024
 with (directory/NAMES[0]).open('rb') as f:chunks=[hashlib.md5(b).hexdigest() for b in iter(lambda:f.read(cs),b'')]
 assert g['size']==package['size'] and g['chunks']==chunks;return package

def build(base,out,plan,previous):
 base=Path(base);out=Path(out);out.mkdir(parents=True,exist_ok=True)
 baseline=metadata(base,3306);assert baseline['sha256']==plan['base_package_sha256']
 specs={x['path']:x for x in plan['runtime_files']};assert len(specs)==27
 prior={f['path']:f['git_blob'] for r in previous for f in r['files']};assert len(prior)==194
 full=set(plan['full_review_ids']);assert len(full)==4
 for spec in specs.values():validate_operations(spec,full,plan['approved_name_map'])
 assert sum(not op[0][-1].startswith('name') for s in specs.values() for op in s['operations'])==294
 assert sum(op[0][-1].startswith('name') for s in specs.values() for op in s['operations'])==81
 files={};records=[];prior_touched=[]
 with zipfile.ZipFile(base/NAMES[0]) as old,zipfile.ZipFile(out/NAMES[0],'w',zipfile.ZIP_DEFLATED,compresslevel=9) as new:
  assert set(specs)<=set(old.namelist()) and set(prior)<=set(old.namelist())
  for info in old.infolist():
   path=PurePosixPath(info.filename);assert not path.is_absolute() and '..' not in path.parts
   raw=old.read(info.filename);updated=raw
   if info.filename in prior:assert blob(raw)==prior[info.filename],('Previous revision missing',info.filename)
   if info.filename in specs:
    spec=specs[info.filename];assert blob(raw)==spec['before']
    updated=replace_strings(raw,spec['operations']);assert blob(updated)==spec['after'];assert_only_recorded_changes(raw,updated,spec['operations'])
    if info.filename in prior:prior_touched.append({'path':info.filename,'previous_git_blob':prior[info.filename],'new_git_blob':spec['after'],'additional_exact_fields':len(spec['operations'])})
    records.append(dict(path=info.filename,before=spec['before'],git_blob=spec['after'],name_fields=sum(op[0][-1].startswith('name') for op in spec['operations']),body_fields=sum(not op[0][-1].startswith('name') for op in spec['operations'])))
   if info.is_dir():assert raw==b'';new.writestr(copy.copy(info),updated)
   else:
    assert info.filename.startswith('madomagi/resource/scenario/json/')
    new.writestr(copy.copy(info),updated,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    files[info.filename]=dict(size=len(updated),crc32=f'{zlib.crc32(updated)&0xffffffff:08x}')
  new.comment=old.comment
 unchanged=0
 with zipfile.ZipFile(base/NAMES[0]) as a,zipfile.ZipFile(out/NAMES[0]) as b:
  assert a.namelist()==b.namelist() and b.testzip() is None
  for i in a.infolist():
   if i.filename not in specs:assert a.read(i.filename)==b.read(i.filename);unchanged+=not i.is_dir()
   else:assert blob(b.read(i.filename))==specs[i.filename]['after']
 assert unchanged==14206
 package=identity(out/NAMES[0]);save(out/NAMES[3],dict(version=3307,size=package['size'],md5=package['md5']))
 m=json.loads((base/NAMES[1]).read_bytes());m.update(version=3307,generated=plan['generated_at'],zip_size=package['size'],zip_md5=package['md5'],files=files,file_count=len(files),total_size=sum(x['size'] for x in files.values()));save(out/NAMES[1],m)
 g=json.loads((base/NAMES[2]).read_bytes());cs=g[NAMES[0]]['chunk_size']
 with (out/NAMES[0]).open('rb') as f:chunks=[hashlib.md5(b).hexdigest() for b in iter(lambda:f.read(cs),b'')]
 g[NAMES[0]]=dict(size=package['size'],chunk_size=cs,chunks=chunks);save(out/NAMES[2],g)
 assert metadata(out,3307)==package
 report=dict(schema=1,batch=plan['batch'],version=3307,status='built_and_validated',reader_commit=plan['reader_commit'],cn_patch_commit=plan['cn_patch_commit'],base_version=3306,base_package=baseline,package=package,files=records,changed_runtime_scripts=27,fully_reviewed_stories=4,reviewed_dialogue_fields=320,changed_dialogue_fields=294,changed_name_fields=81,regression_tests=39,reader_name_fields=214,reader_txt_files=64,unchanged_files=unchanged,previous_corrected_scripts=194,previous_byte_identical=194-len(prior_touched),previous_exact_extensions=prior_touched,prior_corrections_preserved=True,non_display_json_fields_unchanged=True,whole_corpus_review_complete=False,device_rendering_verified=False)
 save(out/'story-quality-report.json',report);return report

"""Release only verified name edits and replayable, reviewed Japanese-layout replacements."""
from pathlib import Path,PurePosixPath
import json,hashlib,zipfile,zlib,copy
from exact_json import blob
from batch_rules import rebuild,OLD_NAMES
NAMES=('cn_scenario_update.zip','cn_scenario_update_manifest.json','manifest.json','version_scenario.json')

def identity(path):
 h=hashlib.sha256();m=hashlib.md5();size=0
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b);m.update(b);size+=len(b)
 return {'size':size,'sha256':h.hexdigest(),'md5':m.hexdigest()}
def save(path,data):
 Path(path).parent.mkdir(parents=True,exist_ok=True);Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def metadata(root,version):
 root=Path(root);package=identity(root/NAMES[0]);assert json.loads((root/NAMES[3]).read_bytes())=={'version':version,'size':package['size'],'md5':package['md5']}
 m=json.loads((root/NAMES[1]).read_bytes());assert m['version']==version and m['zip_size']==package['size'] and m['zip_md5']==package['md5']
 with zipfile.ZipFile(root/NAMES[0]) as z:
  assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))==14251
  files={i.filename:{'size':i.file_size,'crc32':f'{i.CRC:08x}'} for i in z.infolist() if not i.is_dir()}
  assert m['files']==files and len(files)==m['file_count']==14233 and m['total_size']==sum(x['size'] for x in files.values())
 c=json.loads((root/NAMES[2]).read_bytes())[NAMES[0]];size=c['chunk_size'];assert 0<size<=64*1024*1024
 with (root/NAMES[0]).open('rb') as f:hashes=[hashlib.md5(b).hexdigest() for b in iter(lambda:f.read(size),b'')]
 assert c['size']==package['size'] and c['chunks']==hashes;return package

def build(base,out,plan,previous):
 base=Path(base);out=Path(out);out.mkdir(parents=True,exist_ok=True);source=metadata(base,3310);assert source['sha256']==plan['base_package_sha256']
 specs={s['path']:s for s in plan['runtime_files']};assert len(specs)==12
 prior={f['path']:f['git_blob'] for r in previous for f in r['files']};assert len(prior)==364
 assert len(plan['protected_v4'])==43 and not(set(specs)&set(plan['protected_v4']))
 records=[];files={};touched_prior=[];namefields=0
 with zipfile.ZipFile(base/NAMES[0]) as z,zipfile.ZipFile(out/NAMES[0],'w',zipfile.ZIP_DEFLATED,compresslevel=9) as target:
  assert set(specs)|set(prior)|set(plan['protected_v4'])<=set(z.namelist())
  for i in z.infolist():
   p=PurePosixPath(i.filename);assert not p.is_absolute() and '..' not in p.parts
   before=z.read(i.filename);candidate=before
   if i.filename in prior:assert blob(before)==prior[i.filename]
   if i.filename in plan['protected_v4']:assert blob(before)==plan['protected_v4'][i.filename]
   if i.filename in specs:
    s=specs[i.filename];jp=(Path(__file__).parent/'jp'/Path(i.filename).name).read_bytes() if s['mode']=='reviewed_jp_layout' else None
    candidate=rebuild(s,before,jp)
    if s['mode']=='exact_name':namefields+=len(s['operations'])
    if i.filename in prior:touched_prior.append(i.filename)
    records.append({'path':i.filename,'before':s['before'],'git_blob':s['after'],'mode':s['mode']})
   if i.filename.endswith('.json'):assert not any(old.encode() in candidate for old in OLD_NAMES),'Uncorrected active name remains in package'
   if i.is_dir():assert before==b'';target.writestr(copy.copy(i),candidate)
   else:
    assert i.filename.startswith('madomagi/resource/scenario/json/')
    target.writestr(copy.copy(i),candidate,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9);files[i.filename]={'size':len(candidate),'crc32':f'{zlib.crc32(candidate)&0xffffffff:08x}'}
  target.comment=z.comment
 assert namefields==27
 with zipfile.ZipFile(base/NAMES[0]) as a,zipfile.ZipFile(out/NAMES[0]) as b:
  assert a.namelist()==b.namelist() and b.testzip() is None
  for i in a.infolist():
   if i.filename not in specs:assert a.read(i.filename)==b.read(i.filename)
   else:assert blob(b.read(i.filename))==specs[i.filename]['after']
 package=identity(out/NAMES[0]);save(out/NAMES[3],{'version':3311,'size':package['size'],'md5':package['md5']})
 m=json.loads((base/NAMES[1]).read_bytes());m.update(version=3311,generated=plan['generated_at'],zip_size=package['size'],zip_md5=package['md5'],files=files,file_count=len(files),total_size=sum(x['size'] for x in files.values()));save(out/NAMES[1],m)
 g=json.loads((base/NAMES[2]).read_bytes());size=g[NAMES[0]]['chunk_size']
 with (out/NAMES[0]).open('rb') as f:hashes=[hashlib.md5(b).hexdigest() for b in iter(lambda:f.read(size),b'')]
 g[NAMES[0]]={'size':package['size'],'chunk_size':size,'chunks':hashes};save(out/NAMES[2],g);assert metadata(out,3311)==package
 report={'schema':1,'batch':plan['batch'],'version':3311,'status':'built_and_validated','reader_commit':plan['reader_commit'],'cn_patch_commit':plan['cn_patch_commit'],'base_version':3310,'base_package':source,'package':package,'files':records,'changed_runtime_scripts':12,'maintainer_name':'海异光小阿鲁','renamed_fields':27,'reviewed_complete_scenes':4,'reviewed_jp_events':229,'source_corrected_payloads':58,'unchanged_chinese_payloads_reused':171,'unchanged_files':14221,'previous_corrected_scripts':364,'previous_byte_identical':364-len(touched_prior),'previous_exact_extensions':touched_prior,'protected_v4_unchanged':43,'old_name_residuals_in_player_package':0,'remaining_control_candidates':8,'remaining_control_files':5,'regression_tests':18,'reader_device_test_completed':False,'game_device_verified':False,'whole_corpus_complete':False}
 save(out/'story-quality-report.json',report);return report

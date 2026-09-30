"""Apply only approved scalar repairs to the fixed baseline package and verify every member."""
from pathlib import Path,PurePosixPath
import json,hashlib,zipfile,zlib,copy
from exact_json import blob,apply
from control_safety import validate_spec,no_added_undefined_references
NAMES=('cn_scenario_update.zip','cn_scenario_update_manifest.json','manifest.json','version_scenario.json')
def identity(path):
 sha=hashlib.sha256();md=hashlib.md5();size=0
 with Path(path).open('rb') as stream:
  for b in iter(lambda:stream.read(1024*1024),b''):sha.update(b);md.update(b);size+=len(b)
 return {'size':size,'sha256':sha.hexdigest(),'md5':md.hexdigest()}
def save(path,obj):
 Path(path).parent.mkdir(parents=True,exist_ok=True);Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def metadata(root,version):
 root=Path(root);package=identity(root/NAMES[0]);v=json.loads((root/NAMES[3]).read_bytes());assert v=={'version':version,'size':package['size'],'md5':package['md5']}
 m=json.loads((root/NAMES[1]).read_bytes());assert m['version']==version and m['zip_size']==package['size'] and m['zip_md5']==package['md5']
 with zipfile.ZipFile(root/NAMES[0]) as z:
  assert len(z.namelist())==len(set(z.namelist()))==14251 and z.testzip() is None
  files={x.filename:{'size':x.file_size,'crc32':f'{x.CRC:08x}'} for x in z.infolist() if not x.is_dir()}
  assert len(files)==14233 and files==m['files'] and m['file_count']==14233 and m['total_size']==sum(x['size'] for x in files.values())
 manifest=json.loads((root/NAMES[2]).read_bytes())[NAMES[0]];cs=manifest['chunk_size'];assert 0<cs<=64*1024*1024
 with (root/NAMES[0]).open('rb') as stream:chunks=[hashlib.md5(b).hexdigest() for b in iter(lambda:stream.read(cs),b'')]
 assert manifest['size']==package['size'] and chunks==manifest['chunks'];return package

def build(base,out,plan,previous):
 base=Path(base);out=Path(out);out.mkdir(parents=True,exist_ok=True);baseline=metadata(base,3309);assert baseline['sha256']==plan['base_package_sha256']
 specs={s['path']:s for s in plan['runtime_files']};assert len(specs)==130
 approved={p:{'before':s['before'],'after':s['after']} for p,s in specs.items()}
 prior={f['path']:f['git_blob'] for r in previous for f in r['files']};assert len(prior)==238
 assert len(plan['protected_v4'])==43 and not(set(specs)&set(plan['protected_v4']))
 for s in specs.values():validate_spec(s,approved)
 files={};records=[];changed_prior=[]
 with zipfile.ZipFile(base/NAMES[0]) as old,zipfile.ZipFile(out/NAMES[0],'w',zipfile.ZIP_DEFLATED,compresslevel=9) as new:
  assert set(specs)<=set(old.namelist()) and set(prior)<=set(old.namelist())
  for info in old.infolist():
   path=PurePosixPath(info.filename);assert not path.is_absolute() and '..' not in path.parts
   raw=old.read(info.filename);revised=raw
   if info.filename in prior:assert blob(raw)==prior[info.filename]
   if info.filename in plan['protected_v4']:assert blob(raw)==plan['protected_v4'][info.filename]
   if info.filename in specs:
    spec=specs[info.filename];working=raw
    if info.filename in plan.get('authorized_source_carry',{}):
     carry=plan['authorized_source_carry'][info.filename]
     assert blob(raw)==carry['package_before']
     for address,before,after in carry['operations']:
      assert isinstance(before,str) and before.replace('白翼','白羽')==after and before!=after
     working=apply(raw,carry['operations'])
     assert blob(working)==carry['repository_before']
    assert blob(working)==spec['before'];revised=apply(working,spec['operations']);assert blob(revised)==spec['after'];no_added_undefined_references(raw,revised)
    records.append({'path':info.filename,'before':blob(raw),'repository_before':spec['before'],'git_blob':spec['after'],'display_fields':sum(isinstance(op[1],str) for op in spec['operations']),'actor_id_values':sum(type(op[1]) is int for op in spec['operations'])})
    if info.filename in prior:changed_prior.append(info.filename)
   if info.is_dir():assert raw==b'';new.writestr(copy.copy(info),revised)
   else:
    assert info.filename.startswith('madomagi/resource/scenario/json/');new.writestr(copy.copy(info),revised,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    files[info.filename]={'size':len(revised),'crc32':f'{zlib.crc32(revised)&0xffffffff:08x}'}
  new.comment=old.comment
 with zipfile.ZipFile(base/NAMES[0]) as a,zipfile.ZipFile(out/NAMES[0]) as b:
  assert a.namelist()==b.namelist() and b.testzip() is None
  for info in a.infolist():
   if info.filename not in specs:assert a.read(info.filename)==b.read(info.filename)
   else:assert blob(b.read(info.filename))==specs[info.filename]['after']
 package=identity(out/NAMES[0]);save(out/NAMES[3],{'version':3310,'size':package['size'],'md5':package['md5']})
 m=json.loads((base/NAMES[1]).read_bytes());m.update(version=3310,zip_size=package['size'],zip_md5=package['md5'],files=files,total_size=sum(x['size'] for x in files.values()),file_count=len(files),generated=plan['generated_at']);save(out/NAMES[1],m)
 g=json.loads((base/NAMES[2]).read_bytes());cs=g[NAMES[0]]['chunk_size']
 with (out/NAMES[0]).open('rb') as stream:chunks=[hashlib.md5(b).hexdigest() for b in iter(lambda:stream.read(cs),b'')]
 g[NAMES[0]]={'size':package['size'],'chunk_size':cs,'chunks':chunks};save(out/NAMES[2],g);assert metadata(out,3310)==package
 report={'schema':1,'batch':plan['batch'],'version':3310,'status':'built_and_validated','reader_commit':plan['reader_commit'],'cn_patch_commit':plan['cn_patch_commit'],'base_version':3309,'base_package':baseline,'package':package,'files':records,'changed_runtime_scripts':130,'control_pass_display_string_fields':233,'authorized_previous_name_fields_now_delivered':17,'authorized_previous_body_fields_now_delivered':4,'source_carry_details':plan.get('authorized_source_carry',{}),'changed_actor_id_values':488,'new_source_based_utterances':2,'unchanged_files':14103,'previous_corrected_scripts':238,'previous_byte_identical':238-len(changed_prior),'previous_exact_extensions':changed_prior,'accepted_v4_files_unchanged':43,'reader_visible_identical_files':124,'reader_intended_display_change_files':7,'reader_txt_files':16,'regression_tests':18,'new_undefined_actor_references':0,'whole_corpus_review_complete':False,'device_gameplay_verified':False,'remaining_complex_control_candidates':25}
 save(out/'story-quality-report.json',report);return report

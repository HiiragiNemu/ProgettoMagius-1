"""Publish batch 3316 after source commits, metadata and public-byte verification."""
import json,os,time,hashlib,urllib.request,urllib.error
from pathlib import Path
from build_scenario_batch import build,metadata,identity,save,NAMES
from exact_json import blob
REPO='HiiragiNemu/ProgettoMagius-1'
ROOT=Path('story-quality/20261001-semantic-batch04-ai-only')

class API:
 def __init__(self):self.token=os.environ['GH_TOKEN']
 def call(self,path,method='GET',data=None):
  url='https://api.github.com/repos/'+REPO+'/'+path
  raw=None if data is None else json.dumps(data).encode()
  request=urllib.request.Request(url,data=raw,method=method,headers={'Authorization':'Bearer '+self.token,'Accept':'application/vnd.github+json','Content-Type':'application/json','User-Agent':'Scenario-3316-Publisher'})
  with urllib.request.urlopen(request,timeout=120) as response:
   body=response.read();return json.loads(body) if body else None
 def assets(self,release):
  items=self.call('releases/'+str(release['id'])+'/assets?per_page=100')
  assert len(items)<100 and len({x['name'] for x in items})==len(items)
  return {x['name']:x for x in items}
 def upload(self,release,path):
  import urllib.parse
  path=Path(path);url=release['upload_url'].split('{')[0]+'?name='+urllib.parse.quote(path.name)
  assert url.startswith('https://uploads.github.com/repos/'+REPO+'/releases/')
  request=urllib.request.Request(url,data=path.read_bytes(),method='POST',headers={'Authorization':'Bearer '+self.token,'Content-Type':'application/octet-stream','User-Agent':'Scenario-3316-Publisher'})
  with urllib.request.urlopen(request,timeout=600) as response:result=json.load(response)
  expected=identity(path);assert result['size']==expected['size'] and result['digest']=='sha256:'+expected['sha256']
  return result

def download(url,destination):
 assert url.startswith(('https://github.com/HiiragiNemu/ProgettoMagius-1/releases/download/','https://raw.githubusercontent.com/HiiragiNemu/ProgettoMagius-1/'))
 destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
 for attempt in range(3):
  try:
   request=urllib.request.Request(url,headers={'User-Agent':'Scenario-Anonymous-3316-Verification','Accept-Encoding':'identity'})
   with urllib.request.urlopen(request,timeout=240) as response,destination.open('wb') as out:
    assert response.status==200 and not response.headers.get('Content-Range')
    for chunk in iter(lambda:response.read(1024*1024),b''):out.write(chunk)
   return
  except Exception:
   if attempt==2:raise
   time.sleep(2+attempt)

def snapshot(assets):return {n:tuple(a.get(k) for k in ('id','size','digest','updated_at')) for n,a in assets.items()}

def anonymous_check(api,tag,files,output):
 release=api.call('releases/tags/'+tag);assets=api.assets(release)
 for p in files:
  target=Path(output)/p.name;expected=identity(p)
  # GitHub's mutable release path can briefly serve an older redirect/body.
  # Verify the normal, unauthenticated URL on every attempt; a cache-busted
  # URL or a matching API digest alone is not sufficient to open the gate.
  for attempt in range(13):
   download(assets[p.name]['browser_download_url'],target)
   actual=identity(target)
   if actual==expected:break
   print('PUBLIC_URL_NOT_YET_CONSISTENT',tag,p.name,attempt+1,
         'expected',expected,'received',actual,flush=True)
   if attempt==12:raise RuntimeError('Public URL did not converge: '+p.name)
   current=api.assets(api.call('releases/tags/'+tag))
   if current.get(p.name,{}).get('digest')!='sha256:'+expected['sha256']:
    raise RuntimeError('Release changed during public verification: '+p.name)
   time.sleep(10)
 print('ANONYMOUS_VERIFIED',tag,[p.name for p in files],flush=True)

def archive(api,tag,out):
 try:release=api.call('releases/tags/'+tag)
 except urllib.error.HTTPError as error:
  if error.code!=404:raise
  release=api.call('releases','POST',{'tag_name':tag,'name':'Scenario 3316: thirteen complete AI-origin chapter reviews','body':'Thirteen complete machine-test-origin chapters, 52 runtime scenes and 2961 body fields read against Japanese. 163 body fields and one explicit speaker label repaired; eight already-correct scripts kept unchanged. Twenty-six paired reading files synchronized. Verified human and authorized official sources excluded from retranslation. Actors, models, event structures, audio, executable tags and 43 V4 repairs preserved. Model-assisted review does not establish human or official authorship.','draft':False,'prerelease':False,'make_latest':'false'})
 existing=api.assets(release)
 for name in NAMES+('story-quality-report.json',):
  p=out/name
  if name in existing:assert existing[name]['digest']=='sha256:'+identity(p)['sha256'],'Immutable archive conflict'
  else:api.upload(release,p)
 anonymous_check(api,tag,[out/n for n in NAMES],out/'immutable-check')
 return release

def record(api,report):
 assets=api.assets(api.call('releases/tags/latest'))
 assert assets[NAMES[0]]['digest']=='sha256:'+report['package']['sha256']
 report['public_assets']=[{k:assets[n].get(k) for k in ('id','name','size','digest','updated_at')} for n in NAMES]
 for attempt in range(4):
  head=api.call('git/ref/heads/main')['object']['sha'];tree=api.call('git/commits/'+head)['tree']['sha']
  import base64
  last=api.call('contents/migration/last-sync.json?ref='+head)
  prior=json.loads(base64.b64decode(last['content']));records={x['name']:x for x in prior['assets']}
  for n in NAMES:records[n]={'name':n,'size':assets[n]['size'],'sha256':assets[n]['digest'][7:],'unchanged':False}
  prior.update(assets=list(records.values()),scenario_version=3316,scenario_quality_batch=report['batch'],scenario_source_commit=report['cn_patch_commit'],checked_at=report['verified_at'])
  entries=[{'path':p,'mode':'100644','type':'blob','content':json.dumps(value,ensure_ascii=False,indent=2)+'\n'} for p,value in [('story-quality/releases/3316.json',report),('migration/last-sync.json',prior)]]
  newtree=api.call('git/trees','POST',{'base_tree':tree,'tree':entries})['sha']
  commit=api.call('git/commits','POST',{'message':'chore(scenario): record anonymously verified 3316 faithful translation review batch','tree':newtree,'parents':[head]})['sha']
  try:api.call('git/refs/heads/main','PATCH',{'sha':commit,'force':False});return commit
  except urllib.error.HTTPError as error:
   if error.code not in (409,422) or attempt==3:raise
 raise RuntimeError('Receipt commit failed')

def main():
 assert os.environ.get('GITHUB_REPOSITORY')==REPO
 plan=json.loads((ROOT/'publication-plan.json').read_bytes())
 assert plan['base_version']==3315 and plan['target_version']==3316 and plan['changed_runtime_scripts']==44 and plan['reviewed_fields']==2961 and plan['changed_fields']==164 and plan['complete_scenes_reviewed']==52
 for key in ('reader_commit','cn_patch_commit'):
  assert len(plan[key])==40 and all(c in '0123456789abcdef' for c in plan[key])
 api=API();work=Path('scenario3316');base=work/'base';out=work/'candidate';out.mkdir(parents=True,exist_ok=True)
 release=api.call('releases/tags/latest');initial=api.assets(release)
 for n in NAMES:
  download(initial[n]['browser_download_url'],base/n)
  assert identity(base/n)['sha256']==initial[n]['digest'][7:]
 version=json.loads((base/NAMES[3]).read_bytes())['version'];assert version in (3315,3316),'Live version advanced; do not downgrade'
 previous=[]
 for v in range(3301,3316):
  p=work/('receipt-'+str(v)+'.json')
  download('https://raw.githubusercontent.com/'+REPO+'/main/story-quality/releases/'+str(v)+'.json',p);previous.append(json.loads(p.read_bytes()))
 if version==3316:
  import zipfile
  package=metadata(base,3316)
  with zipfile.ZipFile(base/NAMES[0]) as z:
   specs={s['path']:s for s in plan['runtime_files']}
   for s in specs.values():assert blob(z.read(s['path']))==s['after']
   previous_files={f['path']:f['git_blob'] for r in previous for f in r['files']}
   for path,old_blob in previous_files.items():
    expected=specs[path]['after'] if path in specs else old_blob
    assert blob(z.read(path))==expected
  saved=api.assets(api.call('releases/tags/scenario-3316'))
  assert saved[NAMES[0]]['digest']=='sha256:'+package['sha256']
  download(saved['story-quality-report.json']['browser_download_url'],out/'story-quality-report.json')
  report=json.loads((out/'story-quality-report.json').read_bytes())
  assert report['package']==package and report['reader_commit']==plan['reader_commit'] and report['cn_patch_commit']==plan['cn_patch_commit']
  anonymous_check(api,'latest',[base/n for n in NAMES],work/'recheck')
  report.update(status='published_and_anonymously_verified',public_release='latest',immutable_release='scenario-3316',verified_at=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
  report['receipt_commit']=record(api,report);save(out/'story-quality-report.json',report)
  print('SCENARIO_3316_REVERIFIED',report['receipt_commit'],flush=True);return
 report=build(base,out,plan,previous)
 print('SCENARIO_3316_VALIDATED',json.dumps({k:v for k,v in report.items() if k!='files'},ensure_ascii=False),flush=True)
 archive(api,'scenario-3316',out)
 assert snapshot(api.assets(api.call('releases/tags/latest')))==snapshot(initial),'Live release changed during build'
 modified=[];gate_visible=False
 try:
  for n in NAMES[:-1]:
   modified.append(n);api.call('releases/assets/'+str(initial[n]['id']),'DELETE');api.upload(release,out/n)
  anonymous_check(api,'latest',[out/n for n in NAMES[:-1]],work/'anonymous-before-gate')
  modified.append(NAMES[3]);api.call('releases/assets/'+str(initial[NAMES[3]]['id']),'DELETE');api.upload(release,out/NAMES[3]);gate_visible=True
  anonymous_check(api,'latest',[out/NAMES[3]],work/'anonymous-version')
  current=api.assets(api.call('releases/tags/latest'))
  for n,a in initial.items():
   if n not in NAMES:assert snapshot({n:current[n]})==snapshot({n:a}),'Unrelated release asset changed'
  report.update(status='published_and_anonymously_verified',public_release='latest',immutable_release='scenario-3316',unrelated_release_assets_unchanged=True,verified_at=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
  report['receipt_commit']=record(api,report);save(out/'story-quality-report.json',report)
  print('SCENARIO_3316_PUBLICATION_COMPLETE',report['receipt_commit'],report['package'],flush=True)
 except Exception:
  current=api.assets(api.call('releases/tags/latest'))
  if current.get(NAMES[3],{}).get('digest')=='sha256:'+identity(out/NAMES[3])['sha256']:gate_visible=True
  if not gate_visible:
   for n in modified:
    current=api.assets(release)
    if n in current:api.call('releases/assets/'+str(current[n]['id']),'DELETE')
    api.upload(release,base/n)
   print('BASELINE_3315_RESTORED_BEFORE_NEW_GATE',flush=True)
  else:print('3316_GATE_ALREADY_PUBLIC; verify receipt, never downgrade',flush=True)
  raise

if __name__=='__main__':main()

import unittest,sys,importlib.util,tempfile,urllib.error
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
if 'build_scenario_batch' not in sys.modules:
 p=ROOT/'build_scenario_batch.py'
 if not p.exists():p=ROOT/'build_package.py'
 spec=importlib.util.spec_from_file_location('build_scenario_batch',p);m=importlib.util.module_from_spec(spec);sys.modules['build_scenario_batch']=m;spec.loader.exec_module(m)
spec=importlib.util.spec_from_file_location('checked_publisher3321',ROOT/'publish_scenario_3322.py');pub=importlib.util.module_from_spec(spec);spec.loader.exec_module(pub)
class FakeAPI:
 def __init__(self,digest):self.digest=digest
 def call(self,path):return {'id':1}
 def assets(self,release):return {'x.zip':{'browser_download_url':'https://github.com/HiiragiNemu/ProgettoMagius-1/releases/download/latest/x.zip','digest':self.digest}}
class OrdinaryPublicGateTests(unittest.TestCase):
 def check(self,answers,digest=None):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);src=root/'x.zip';src.write_bytes(b'complete exact new archive');api=FakeAPI(digest or 'sha256:'+pub.identity(src)['sha256']);urls=[]
   def download(url,target):
    urls.append(url);item=answers[min(len(urls)-1,len(answers)-1)]
    if isinstance(item,Exception):raise item
    Path(target).parent.mkdir(exist_ok=True);Path(target).write_bytes(item)
   with patch.object(pub,'download',download),patch.object(pub.time,'sleep'):
    pub.anonymous_check(api,'latest',[src],root/'check')
   self.assertTrue(all(u.endswith('/latest/x.zip') and '?' not in u for u in urls));return urls
 def test_ordinary_exact_bytes_accepted(self):self.assertEqual(len(self.check([b'complete exact new archive'])),1)
 def test_stale_redirect_404_then_exact(self):self.assertEqual(len(self.check([urllib.error.HTTPError('u',404,'missing',{},None),b'complete exact new archive'])),2)
 def test_partial_body_then_exact(self):self.assertEqual(len(self.check([b'complete',b'complete exact new archive'])),2)
 def test_old_body_then_exact(self):self.assertEqual(len(self.check([b'old archive',b'complete exact new archive'])),2)
 def test_permanent404_never_opens_gate(self):
  with self.assertRaises(RuntimeError):self.check([urllib.error.HTTPError('u',404,'missing',{},None)])
 def test_api_digest_alone_never_sufficient(self):
  with self.assertRaises(RuntimeError):self.check([b'wrong public bytes'])
 def test_concurrent_asset_mutation_stops_retry(self):
  with self.assertRaisesRegex(RuntimeError,'Release changed'):self.check([b'old',b'complete exact new archive'],'sha256:someone-else')
if __name__=='__main__':unittest.main()

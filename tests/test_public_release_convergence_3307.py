"""No-network regression coverage for delayed mutable release URLs."""
from pathlib import Path
import sys,tempfile,unittest
from unittest.mock import patch
R=Path(__file__).resolve().parents[1]/'story-quality'/'20260930-06';sys.path.insert(0,str(R))
import publish_scenario_3307 as p

class FakeAPI:
 def __init__(self,digest):self.digest=digest
 def call(self,path):return {'id':1}
 def assets(self,release):return {'test.bin':{'browser_download_url':'https://github.com/HiiragiNemu/ProgettoMagius-1/releases/download/latest/test.bin','digest':self.digest}}

class PublicConsistency(unittest.TestCase):
 def fixture(self):
  temp=tempfile.TemporaryDirectory();root=Path(temp.name);candidate=root/'test.bin';candidate.write_bytes(b'correct-new-package')
  return temp,root,candidate,FakeAPI('sha256:'+p.identity(candidate)['sha256'])
 def test_stale_then_correct_plain_url(self):
  temp,root,candidate,api=self.fixture();calls=[]
  def download(url,path):
   self.assertNotIn('?',url);self.assertIn('/latest/',url);calls.append(url);Path(path).parent.mkdir(parents=True,exist_ok=True);Path(path).write_bytes(b'old-package' if len(calls)==1 else candidate.read_bytes())
  with temp,patch.object(p,'download',download),patch.object(p.time,'sleep') as sleep:
   p.anonymous_check(api,'latest',[candidate],root/'verified');self.assertEqual(len(calls),2);sleep.assert_called_once_with(10)
 def test_never_converges_is_rejected(self):
  temp,root,candidate,api=self.fixture();calls=[]
  def download(url,path):calls.append(url);Path(path).parent.mkdir(parents=True,exist_ok=True);Path(path).write_bytes(b'wrong')
  with temp,patch.object(p,'download',download),patch.object(p.time,'sleep'):
   with self.assertRaises(RuntimeError):p.anonymous_check(api,'latest',[candidate],root/'verified')
   self.assertEqual(len(calls),13)
 def test_publisher_changes_during_wait_is_rejected(self):
  temp,root,candidate,api=self.fixture()
  def download(url,path):Path(path).parent.mkdir(parents=True,exist_ok=True);Path(path).write_bytes(b'wrong');api.digest='sha256:'+'0'*64
  with temp,patch.object(p,'download',download),patch.object(p.time,'sleep') as sleep:
   with self.assertRaises(RuntimeError):p.anonymous_check(api,'latest',[candidate],root/'verified')
   sleep.assert_not_called()

if __name__=='__main__':unittest.main()

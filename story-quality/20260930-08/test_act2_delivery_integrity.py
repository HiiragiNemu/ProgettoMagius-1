"""Historical repair fixtures verify exact edits without pinning future repository text."""
from pathlib import Path
import base64,gzip,json,re,unittest,copy
from exact_fields import replace_strings,blob
ROOT=Path(__file__).resolve().parent
TEXT={'textLeft','textRight','textCenter','narration','progressNarration','Fnarration','fnarration','progressFnarration','textAvLeft','textAvRight','textAvCenter'}
def values(d):return [v for turns in d['story'].values() for t in turns for k,v in t.items() if k in TEXT and isinstance(v,str)]
def tokens(s):return re.findall(r'\[(?!text(?:Red|Blue|Yellow|Black):)[^\[\]]*\]',s)
def without_text(x):
 if isinstance(x,dict):return {k:without_text(v) for k,v in x.items() if k not in TEXT}
 if isinstance(x,list):return [without_text(v) for v in x]
 return x

class Act2DeliveryIntegrity(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.f=json.loads(gzip.decompress((ROOT/'tests/fixtures/act2_delivery_20260930.json.gz').read_bytes()))
  cls.r={x['spec']['id']:x for x in cls.f['runtime']}
 def test_exact_string_replacements(self):
  for x in self.f['runtime']:
   a,b=map(base64.b64decode,(x['before'],x['after']));s=x['spec']
   self.assertEqual(blob(a),s['before']);self.assertEqual(blob(b),s['after']);self.assertEqual(replace_strings(a,s['operations']),b)
 def test_every_edit_reverses_to_the_complete_original_bytes(self):
  for x in self.f['runtime']:
   rev=[[a,c,b] for a,b,c in x['spec']['operations']]
   self.assertEqual(replace_strings(base64.b64decode(x['after']),rev),base64.b64decode(x['before']))
 def test_model_ids_actions_voice_and_structure_unchanged(self):
  for x in self.f['runtime']:
   self.assertEqual(without_text(json.loads(base64.b64decode(x['before']))),without_text(json.loads(base64.b64decode(x['after']))))
 def test_fallback_story_has_all_49_japanese_corresponding_fields(self):
  x=self.r['103105-11_32rIq'];a=values(json.loads(base64.b64decode(x['after'])));j=values(json.loads(base64.b64decode(x['jp'])))
  self.assertEqual(len(a),49);self.assertEqual(len(j),49)
  self.assertEqual([tokens(v) for v in a],[tokens(v) for v in j])
 def test_human_payloads_move_without_retranslation(self):
  x=self.r['102502-1_lDVQb'];a=values(json.loads(base64.b64decode(x['before'])));b=values(json.loads(base64.b64decode(x['after'])))
  self.assertEqual(a[:5],b[:5]);self.assertEqual(a[-1],a[-2])
  for i in range(6,len(b)):
   if i!=13:self.assertEqual(b[i],a[i-1])
  self.assertIn('昨天',b[5]);self.assertIn('也可以参加',b[13])
 def test_shift_preserves_global_controls_and_matches_destination_slots(self):
  x=self.r['102502-1_lDVQb'];a=values(json.loads(base64.b64decode(x['before'])));b=values(json.loads(base64.b64decode(x['after'])));j=values(json.loads(base64.b64decode(x['jp'])))
  self.assertEqual(tokens(''.join(a)),tokens(''.join(b)))
  self.assertEqual([tokens(v) for v in b],[tokens(v) for v in j])
 def test_missing_section_restored_once_and_all_other_sections_preserved(self):
  for x in self.f['exports']:
   if '103105_' not in x['spec']['path']:continue
   a,b=(base64.b64decode(x[k]).decode() for k in ('before','after'))
   self.assertNotIn('Source: 103105-11_',a);self.assertEqual(b.count('Source: 103105-11_'),1)
   start=b.index('---[Section 11]');end=b.index('---[Section 12]')
   self.assertEqual(b[:start]+b[end:],a)
 def test_corrected_first_section_does_not_touch_following_ten(self):
  for x in self.f['exports']:
   if '102502_' not in x['spec']['path']:continue
   a,b=(base64.b64decode(x[k]).decode() for k in ('before','after'))
   self.assertEqual(a[a.index('---[Section 2]'):],b[b.index('---[Section 2]'):])
 def test_project_review_does_not_claim_original_human_authorship(self):
  self.assertTrue(self.f['plan']['original_human_translation_not_claimed_for_fallback_review'])
  self.assertFalse(self.f['plan']['live2d_v4_43_files_changed'])
  self.assertFalse(self.f['plan']['whole_act2_semantic_review_complete'])

if __name__=='__main__':unittest.main()

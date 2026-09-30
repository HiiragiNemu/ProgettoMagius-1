import unittest,json
from exact_json import apply
from translation_rules import validate

class TranslationOnlyTests(unittest.TestCase):
 def pair(self,before='旧句',after='新句'):
  a={'story':{'group_1':[{'chara':[{'id':1,'live2dName':'same-instance'}],'nameLeft':'彩羽','textLeft':before}]}}
  raw=json.dumps(a,ensure_ascii=False).encode();ops=[[['story','group_1',0,'textLeft'],before,after]];candidate=apply(raw,ops)
  return raw,candidate,ops
 def test_plain_review(self):self.assertTrue(validate(*self.pair()))
 def test_existing_sound_unchanged(self):self.assertTrue(validate(*self.pair('[se:123]旧句','[se:123]新句')))
 def test_existing_wait_unchanged(self):self.assertTrue(validate(*self.pair('旧[wait:0.8]句','新[wait:0.8]句')))
 def test_wait_mutation_rejected(self):
  with self.assertRaises(ValueError):validate(*self.pair('[wait:0.8]旧','[wait:1.0]新'))
 def test_voice_missing_rejected(self):
  with self.assertRaises(ValueError):validate(*self.pair('[voiceFull:x]旧','新'))
 def test_actor_mutation_rejected(self):
  with self.assertRaises(ValueError):validate(*self.pair('[chara:1:motion_0]旧','[chara:2:motion_0]新'))
 def test_exp_suffix_not_changed_in_translation(self):
  with self.assertRaises(ValueError):validate(*self.pair('[chara:1:face_x.exp.json]旧','[chara:1:face_x.exp3.json]新'))
 def test_highlight_payload_translated(self):self.assertTrue(validate(*self.pair('[textYellow:キモチ]','[textYellow:心魔]')))
 def test_highlight_type_preserved(self):
  with self.assertRaises(ValueError):validate(*self.pair('[textYellow:キモチ]','[textBlue:心魔]'))
 def test_missing_highlight_rejected(self):
  with self.assertRaises(ValueError):validate(*self.pair('[textYellow:キモチ]','心魔'))
 def test_structural_node_edit_rejected(self):
  a,b,ops=self.pair();d=json.loads(b);d['story']['group_1'][0]['chara'][0]['id']=2
  with self.assertRaises(ValueError):validate(a,json.dumps(d),ops)
 def test_speaker_edit_rejected(self):
  a,b,ops=self.pair();d=json.loads(b);d['story']['group_1'][0]['nameLeft']='小圆'
  with self.assertRaises(ValueError):validate(a,json.dumps(d),ops)
 def test_added_speech_rejected(self):
  a,b,ops=self.pair();d=json.loads(b);d['story']['group_1'].append({'textLeft':'新增'})
  with self.assertRaises(ValueError):validate(a,json.dumps(d),ops)
 def test_unrecorded_display_rejected(self):
  a,b,ops=self.pair();d=json.loads(b);d['story']['group_1'][0]['textRight']='新增'
  with self.assertRaises(ValueError):validate(a,json.dumps(d),ops)
 def test_duplicate_edit_path_rejected(self):
  a,b,ops=self.pair()
  with self.assertRaises(ValueError):validate(a,b,ops+ops)
 def test_token_order_preserved(self):
  with self.assertRaises(ValueError):validate(*self.pair('[se:x][wait:1]旧','[wait:1][se:x]新'))
 def test_bytes_outside_token_unchanged(self):
  a=b'\xef\xbb\xbf{\r\n "story":{"group_1":[{"textLeft":"a", "x":1.0}]}}\r\n'
  b=apply(a,[[['story','group_1',0,'textLeft'],'a','b']]);self.assertEqual(b,a.replace(b'"a"',b'"b"'))
 def test_duplicate_json_keys_rejected(self):
  with self.assertRaises(ValueError):apply(b'{"text":"a","text":"b"}',[])

if __name__=='__main__':unittest.main()

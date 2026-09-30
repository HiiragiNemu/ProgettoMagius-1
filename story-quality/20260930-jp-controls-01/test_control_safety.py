import unittest,json
from exact_json import apply
from control_safety import validate_spec,visible,no_added_undefined_references

class ControlRepairTests(unittest.TestCase):
 def spec(self,old,new,key='textLeft'):
  s={'path':'adv/123-1.json','before':'a'*40,'after':'b'*40,'operations':[[['story','group_1',0,key],old,new]]}
  return s,{s['path']:{'before':s['before'],'after':s['after']}}
 def test_sound_added_without_chinese_change(self):
  s,m=self.spec('原文','[se:7106_telmail]原文');validate_spec(s,m)
 def test_chinese_words_cannot_change(self):
  s,m=self.spec('原文','[se:7106_telmail]改写')
  with self.assertRaises(ValueError):validate_spec(s,m)
 def test_colour_range_cannot_change(self):
  s,m=self.spec('[textYellow:心魔]之石','[textYellow:心魔之石]')
  with self.assertRaises(ValueError):validate_spec(s,m)
 def test_colour_with_moved_sound_keeps_text(self):
  s,m=self.spec('[se:x]发现[textYellow:心魔]','发现[se:y][textYellow:心魔]');validate_spec(s,m)
 def test_only_declared_file(self):
  s,m=self.spec('原文','[se:x]原文')
  with self.assertRaises(ValueError):validate_spec(s,{})
 def test_non_display_field_rejected(self):
  s,m=self.spec('a','b',key='bgm')
  with self.assertRaises(ValueError):validate_spec(s,m)
 def test_exact_scalar_id_preserves_format(self):
  original=b'{ "story": {"group_1":[{"chara":[{"id":1}],"textLeft":"words"}]}}\r\n'
  result=apply(original,[[['story','group_1',0,'chara',0,'id'],1,2]])
  self.assertEqual(result,original.replace(b'"id":1',b'"id":2'))
 def test_duplicate_json_key_rejected(self):
  with self.assertRaises(ValueError):apply(b'{"x":1,"x":2}',[[['x'],2,3]])
 def test_wrong_before_rejected(self):
  with self.assertRaises(ValueError):apply(b'{"x":1}',[[['x'],2,3]])
 def test_duplicate_address_rejected(self):
  with self.assertRaises(ValueError):apply(b'{"x":1}',[[['x'],1,2],[['x'],1,3]])
 def test_bom_crlf_and_unchanged_text_kept(self):
  before=b'\xef\xbb\xbf{\r\n "x":"same", "y":1\r\n}'
  self.assertEqual(apply(before,[[['y'],1,2]]),before.replace(b'"y":1',b'"y":2'))
 def test_no_model_reference_regression(self):
  before=json.dumps({'story':{'group_1':[{'chara':[{'id':1}],'textLeft':'[chara:1:motion_0]原文'}]}})
  bad=before.replace('"id": 1','"id": 2')
  with self.assertRaises(ValueError):no_added_undefined_references(before,bad)
  no_added_undefined_references(before,bad.replace('[chara:1:','[chara:2:'))
 def test_named_instance_must_exist(self):
  before=json.dumps({'story':{'group_1':[{'chara':[{'id':1}],'textLeft':'原文'}]}},ensure_ascii=False)
  after=before.replace('原文','[live2dName:new:motion_0]原文')
  with self.assertRaises(ValueError):no_added_undefined_references(before,after)
 def test_existing_named_instance_is_valid(self):
  before=json.dumps({'story':{'group_1':[{'chara':[{'id':1,'live2dName':'instance'}],'textLeft':'原文'}]}},ensure_ascii=False)
  no_added_undefined_references(before,before.replace('原文','[live2dName:instance:motion_0]原文'))
 def test_existing_unrelated_dangling_is_not_new(self):
  raw=json.dumps({'story':{'group_1':[{'textLeft':'[chara:1:motion_0]原文'}]}})
  no_added_undefined_references(raw,raw)
 def test_literal_bracket_is_not_treated_as_runtime(self):
  self.assertEqual(visible('[类别]原文'),'[类别]原文')
 def test_colour_payload_remains_visible_contract(self):
  self.assertEqual(visible('[flashEffect:x][textBlue:中文]@[wait:1]之后'),'[textBlue:中文]@之后')
 def test_independent_new_empty_slot_can_receive_verified_text(self):
  before='{"story":{"group_1":[{"nameLeft":"甲","textLeft":""}]}}'.encode()
  after=apply(before,[[['story','group_1',0,'textLeft'],'','——！？']])
  self.assertEqual(json.loads(after)['story']['group_1'][0]['nameLeft'],'甲')

if __name__=='__main__':unittest.main()

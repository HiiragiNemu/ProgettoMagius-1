import unittest,json
from exact_fields import replace_strings,blob
from prefix_exact import plan,rows

class ExactJson(unittest.TestCase):
 def test_only_addressed_value(self):
  raw=b'{ "nameLeft": "JP", "textLeft": "JP", "other": {"nameLeft":"JP"} }\r\n'
  out=replace_strings(raw,[[['nameLeft'],'JP','中文']])
  self.assertEqual(out,raw.replace(b'"nameLeft": "JP"','"nameLeft": "中文"'.encode(),1))
 def test_nested_and_array(self):
  raw=b'{"story":{"group_1":[{"nameNarration":"JP","chara":[{"id":1}]}]}}'
  out=replace_strings(raw,[[['story','group_1',0,'nameNarration'],'JP','甲']])
  self.assertEqual(json.loads(out)['story']['group_1'][0]['chara'],[{'id':1}])
 def test_wrong_baseline_rejected(self):
  with self.assertRaises(ValueError):replace_strings(b'{"x":"a"}',[[['x'],'b','c']])
 def test_duplicate_address_rejected(self):
  with self.assertRaises(ValueError):replace_strings(b'{"x":"a"}',[[['x'],'a','b'],[['x'],'a','c']])
 def test_duplicate_json_key_rejected(self):
  with self.assertRaises(ValueError):replace_strings(b'{"x":"a","x":"b"}',[])
 def test_bom_format(self):
  raw=b'\xef\xbb\xbf{\r\n "x": "a"\r\n}\r\n'
  self.assertEqual(replace_strings(raw,[[['x'],'a','b']]),raw.replace(b'"a"',b'"b"'))
 def test_control_text_untouched(self):
  raw='{"nameLeft":"JP","textLeft":"[chara:1:motion_0]原文@下一行"}'.encode()
  out=replace_strings(raw,[[['nameLeft'],'JP','甲']])
  self.assertEqual(json.loads(out)['textLeft'],json.loads(raw)['textLeft'])
 def test_missing_path(self):
  with self.assertRaises(ValueError):replace_strings(b'{"x":"a"}',[[['y'],'a','b']])

class ExactPrefix(unittest.TestCase):
 def sample(self,turns,body,newturns=None,mapping=None,semantic=None):
  old=json.dumps({'story':{'group_1':turns}},ensure_ascii=False).encode();new=json.dumps({'story':{'group_1':newturns or turns}},ensure_ascii=False).encode()
  raw=('--- [Section 1] (Source: 123-1.json) ---\n'+body).encode()
  return raw,plan(raw,lambda f:(old,new,'source/'+f,blob(old)),mapping or {},semantic or set())
 def test_preset_inheritance(self):
  raw,(out,edits,held,_) =self.sample([{'nameNarration':'佳子'},{'narration':'甲'},{'narration':'乙'}],'旁白：甲\n旁白：乙\n')
  self.assertEqual(len(edits),2);self.assertFalse(held);self.assertIn('佳子：甲',out.decode())
 def test_explicit_clear(self):
  _,(out,edits,_,_)=self.sample([{'nameNarration':'佳子','narration':'甲'},{'nameNarration':'','narration':'乙'}],'旁白：甲\n旁白：乙\n')
  self.assertEqual(len(edits),1);self.assertTrue(out.decode().endswith('旁白：乙\n'))
 def test_existing_alias_preserved(self):
  raw,(out,edits,_,_)=self.sample([{'nameNarration':'夏目佳子','narration':'甲'}],'佳子：甲\n')
  self.assertEqual(out,raw);self.assertFalse(edits)
 def test_changed_body_preserved(self):
  raw,(out,edits,held,_)=self.sample([{'nameNarration':'佳子','narration':'原文'}],'旁白：人工润色\n')
  self.assertEqual(out,raw);self.assertFalse(edits);self.assertTrue(held)
 def test_sequence_preserved(self):
  raw,(out,edits,held,_)=self.sample([{'nameNarration':'甲','narration':'一'},{'narration':'二'}],'旁白：二\n旁白：一\n')
  self.assertEqual(out,raw);self.assertTrue(held)
 def test_dialogue_not_narration(self):
  raw,(out,edits,_,_)=self.sample([{'nameLeft':'佳子','textLeft':'甲'}],'旁白：甲\n')
  self.assertEqual(out,raw);self.assertFalse(edits)
 def test_name_localization(self):
  _,(out,edits,_,_)=self.sample([{'nameLeft':'いろは','textLeft':'甲'}],'いろは: 甲\n',[{'nameLeft':'彩羽','textLeft':'甲'}],{'いろは':'彩羽'})
  self.assertEqual(len(edits),1);self.assertTrue(out.decode().endswith('彩羽: 甲\n'))
 def test_no_source_name_guess(self):
  raw,(out,edits,_,_)=self.sample([{'textLeft':'甲'}],'いろは: 甲\n',mapping={'いろは':'彩羽'})
  self.assertEqual(out,raw);self.assertFalse(edits)
 def test_fullscreen(self):
  _,(out,edits,_,_)=self.sample([{'nameFnarration':'眩'},{'Fnarration':'甲'}],'旁白：甲\n')
  self.assertEqual(len(edits),1);self.assertTrue(out.decode().endswith('眩：甲\n'))
 def test_known_semantic_address(self):
  _,(out,edits,_,_)=self.sample([{'nameLeft':'甲','textLeft':'旧句'}],'甲：旧句\n',[{'nameLeft':'甲','textLeft':'新句'}],semantic={('123-1.json','group_1',0,'textLeft')})
  self.assertEqual(edits[0]['kind'],'semantic');self.assertTrue(out.decode().endswith('甲：新句\n'))
 def test_unapproved_semantic_rejected(self):
  raw,(out,edits,held,_)=self.sample([{'nameLeft':'甲','textLeft':'旧句'}],'甲：旧句\n',[{'nameLeft':'甲','textLeft':'新句'}])
  self.assertEqual(out,raw);self.assertFalse(edits);self.assertTrue(held)
 def test_japanese_narrator_held(self):
  raw,(out,edits,_,_)=self.sample([{'nameNarration':'かこ','narration':'甲'}],'旁白：甲\n')
  self.assertEqual(out,raw);self.assertFalse(edits)
 def test_branch_independent(self):
  d={'story':{'group_1':[{'nameNarration':'甲','narration':'一'}],'group_2':[{'narration':'二'}]}}
  self.assertIsNone(rows(d,'group_2')[0]['name'])
 def test_bom_crlf_no_last_newline(self):
  old=json.dumps({'story':{'group_1':[{'nameNarration':'甲','narration':'文本'}]}},ensure_ascii=False).encode()
  raw=b'\xef\xbb\xbf'+ '--- [Section 1] (Source: 123-1.json) ---\r\n  旁白：文本'.encode()
  out,edits,_,_=plan(raw,lambda f:(old,old,'p',blob(old)),{},set())
  self.assertEqual(out,raw.replace('旁白'.encode(),'甲'.encode()))
 def test_idempotent(self):
  old=json.dumps({'story':{'group_1':[{'nameNarration':'甲','narration':'文本'}]}},ensure_ascii=False).encode()
  raw='--- [Section 1] (Source: 123-1.json) ---\n旁白：文本\n'.encode();read=lambda f:(old,old,'p',blob(old))
  out,_,_,_=plan(raw,read,{},set());again,edits,_,_=plan(out,read,{},set())
  self.assertEqual(out,again);self.assertFalse(edits)
 def test_repeated_body_position(self):
  _,(out,edits,_,_)=self.sample([{'nameNarration':'甲','narration':'同句'},{'nameNarration':'乙','narration':'同句'}],'旁白：同句\n旁白：同句\n')
  self.assertTrue(out.decode().endswith('甲：同句\n乙：同句\n'));self.assertEqual(len(edits),2)
 def test_choice_held(self):
  raw,(out,edits,held,_)=self.sample([{'nameNarration':'甲','narration':'文本','select':[{'textSelect':'选项'}]}],'旁白：文本\n')
  self.assertEqual(out,raw);self.assertFalse(edits);self.assertTrue(held)

if __name__=='__main__':unittest.main()

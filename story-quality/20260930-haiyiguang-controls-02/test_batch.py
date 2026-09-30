import unittest,json,hashlib,copy
from exact_json import apply,blob
from batch_rules import rebuild,core

def encoded(x):return json.dumps(x,ensure_ascii=False,separators=(',',':')).encode()
class HaiyiguangBatchTests(unittest.TestCase):
 def namecase(self):
  old=encoded({'story':{'group_1':[{'nameRight':'阿玛比埃小阿鲁','textRight':'<小笼目！>','chara':[{'id':1}]}]}})
  ops=[[['story','group_1',0,'nameRight'],'阿玛比埃小阿鲁','海异光小阿鲁']]
  new=apply(old,ops);return old,{'mode':'exact_name','before':blob(old),'after':blob(new),'operations':ops},new
 def jpcase(self):
  jp=encoded({'story':{'group_1':[{'nameLeft':'海香','textLeft':'[se:x]テスト','chara':[{'id':1}]},{'autoTurnLast':0.1}]},'version':1})
  old=encoded({'story':{'group_1':[{'textLeft':'错位'}]},'version':1})
  ops=[[['story','group_1',0,'textLeft'],'[se:x]テスト','[se:x]中文']];new=apply(jp,ops)
  sha=hashlib.sha256(json.dumps(core(json.loads(jp)),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  return old,jp,{'mode':'reviewed_jp_layout','before':blob(old),'after':blob(new),'jp_sha':blob(jp),'jp_operations':ops,'jp_skeleton_sha256':sha},new
 def test_exact_approved_name(self):
  old,s,new=self.namecase();self.assertEqual(rebuild(s,old),new)
 def test_name_only_cannot_rewrite_dialogue(self):
  old,s,new=self.namecase();s['operations']=[[["story","group_1",0,"textRight"],'<小笼目！>','海异光小阿鲁']]
  with self.assertRaises(ValueError):rebuild(s,old)
 def test_other_name_not_auto_replaced(self):
  old,s,new=self.namecase();s['operations'][0][1]='阿鲁'
  with self.assertRaises(ValueError):rebuild(s,old)
 def test_unapproved_target_not_accepted(self):
  old,s,new=self.namecase();s['operations'][0][2]='别的译名'
  with self.assertRaises(ValueError):rebuild(s,old)
 def test_name_baseline_pin(self):
  old,s,new=self.namecase()
  with self.assertRaises(ValueError):rebuild(s,new)
 def test_name_result_pin(self):
  old,s,new=self.namecase();s['after']='0'*40
  with self.assertRaises(ValueError):rebuild(s,old)
 def test_jp_layout_replay(self):
  old,jp,s,new=self.jpcase();self.assertEqual(rebuild(s,old,jp),new)
 def test_jp_blob_must_be_fixed(self):
  old,jp,s,new=self.jpcase()
  with self.assertRaises(ValueError):rebuild(s,old,jp+b' ')
 def test_jp_required(self):
  old,jp,s,new=self.jpcase()
  with self.assertRaises(ValueError):rebuild(s,old)
 def test_model_identity_cannot_change(self):
  old,jp,s,new=self.jpcase();s['jp_operations'].append([['story','group_1',0,'chara',0,'id'],1,2]);s['after']=blob(apply(jp,s['jp_operations']))
  with self.assertRaises(ValueError):rebuild(s,old,jp)
 def test_timing_node_cannot_change(self):
  old,jp,s,new=self.jpcase();s['jp_operations'].append([['story','group_1',1,'autoTurnLast'],0.1,0.2]);s['after']=blob(apply(jp,s['jp_operations']))
  with self.assertRaises(ValueError):rebuild(s,old,jp)
 def test_sound_cannot_be_dropped(self):
  old,jp,s,new=self.jpcase();s['jp_operations'][0][2]='中文';s['after']=blob(apply(jp,s['jp_operations']))
  with self.assertRaises(ValueError):rebuild(s,old,jp)
 def test_remaining_japanese_not_accepted(self):
  old,jp,s,new=self.jpcase();s['jp_operations'][0][2]='[se:x]テスト仍有日文';s['after']=blob(apply(jp,s['jp_operations']))
  with self.assertRaises(ValueError):rebuild(s,old,jp)
 def test_chinese_colour_scope_allowed(self):
  old,jp,s,new=self.jpcase();s['jp_operations'][0][2]='[se:x]这是[textBlue:中文范围]';s['after']=blob(apply(jp,s['jp_operations']))
  self.assertEqual(rebuild(s,old,jp),apply(jp,s['jp_operations']))
 def test_duplicate_address_rejected(self):
  old,jp,s,new=self.jpcase();s['jp_operations']*=2
  with self.assertRaises(ValueError):rebuild(s,old,jp)
 def test_source_schema_version_kept(self):
  old,jp,s,new=self.jpcase();s['jp_operations'].append([['version'],1,2]);s['after']=blob(apply(jp,s['jp_operations']))
  with self.assertRaises(ValueError):rebuild(s,old,jp)
 def test_bom_crlf_exact_name(self):
  old,s,new=self.namecase();old=b'\xef\xbb\xbf'+old+b'\r\n';s['before']=blob(old);s['after']=blob(apply(old,s['operations']));self.assertTrue(rebuild(s,old).startswith(b'\xef\xbb\xbf'));self.assertTrue(rebuild(s,old).endswith(b'\r\n'))
 def test_reading_dialogue_remains_unchanged_for_name(self):
  old,s,new=self.namecase();result=json.loads(rebuild(s,old));self.assertEqual(result['story']['group_1'][0]['textRight'],'<小笼目！>')

if __name__=='__main__':unittest.main()

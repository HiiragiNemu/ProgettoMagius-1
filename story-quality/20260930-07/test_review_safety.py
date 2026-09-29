import unittest,json
from review_safety import controls,validate_operations,assert_only_recorded_changes

class ReviewSafety(unittest.TestCase):
 def check(self,key='textLeft',before='旧句',after='新句',path='adv/710281-1.json'):
  return validate_operations({'path':path,'operations':[[['story','group_1',0,key],before,after]]},{'710281-1'},{'いろは':'彩羽'})
 def test_reviewed_body_allowed(self):self.assertEqual(self.check(),1)
 def test_unreviewed_story_rejected(self):
  with self.assertRaises(ValueError):self.check(path='adv/other.json')
 def test_name_requires_exact_map(self):
  with self.assertRaises(ValueError):self.check(key='nameLeft',before='いろは',after='小圆')
 def test_verified_name_allowed(self):self.assertEqual(self.check(key='nameLeft',before='いろは',after='彩羽'),1)
 def test_action_not_editable(self):
  with self.assertRaises(ValueError):self.check(key='motion')
 def test_sound_removed_rejected(self):
  with self.assertRaises(ValueError):self.check(before='[se:123]旧句')
 def test_sound_added_rejected(self):
  with self.assertRaises(ValueError):self.check(after='[se:123]新句')
 def test_sound_and_motion_order_preserved(self):
  with self.assertRaises(ValueError):self.check(before='[se:123][chara:1:motion_2]旧句',after='[chara:1:motion_2][se:123]新句')
 def test_wait_value_preserved(self):
  with self.assertRaises(ValueError):self.check(before='旧[wait:0.8]句',after='新[wait:1.0]句')
 def test_colour_payload_edit_allowed(self):self.assertEqual(self.check(before='[textBlack:旧句]',after='[textBlack:新句]'),1)
 def test_colour_identity_preserved(self):
  with self.assertRaises(ValueError):self.check(before='[textBlack:旧句]',after='[textRed:新句]')
 def test_duplicate_field_rejected(self):
  op=[['story','group_1',0,'textLeft'],'旧','新']
  with self.assertRaises(ValueError):validate_operations({'path':'710281-1.json','operations':[op,op]},{'710281-1'}, {})
 def test_embedded_image_kept(self):
  a={'story':{'group_1':[{'nameLeft':'いろは','item':[{'base64':'unchanged bytes'}]}]}}
  b=json.loads(json.dumps(a));b['story']['group_1'][0]['nameLeft']='彩羽'
  ops=[[['story','group_1',0,'nameLeft'],'いろは','彩羽']]
  assert_only_recorded_changes(json.dumps(a),json.dumps(b),ops)
  b['story']['group_1'][0]['item'][0]['base64']='corruption'
  with self.assertRaises(ValueError):assert_only_recorded_changes(json.dumps(a),json.dumps(b),ops)
 def test_unrecorded_body_change_rejected(self):
  a={'story':{'group_1':[{'nameLeft':'いろは','textLeft':'原文'}]}}
  b={'story':{'group_1':[{'nameLeft':'彩羽','textLeft':'加戏'}]}}
  with self.assertRaises(ValueError):assert_only_recorded_changes(json.dumps(a),json.dumps(b),[[['story','group_1',0,'nameLeft'],'いろは','彩羽']])

if __name__=='__main__':unittest.main()

import unittest,json
from duplicate_rules import transplant_reviewed_payload as patch_text,validate_operations,verify_display_only

class DuplicatePayloadTests(unittest.TestCase):
 def test_same_execution_new_chinese(self):self.assertEqual(patch_text('[se:1]正确译文','[se:1]错误旧文'),'[se:1]正确译文')
 def test_preserve_target_exp_suffix(self):self.assertEqual(patch_text('[chara:1:face_a.exp3.json]中文','[chara:1:face_a.exp.json]旧文'),'[chara:1:face_a.exp.json]中文')
 def test_no_new_sound(self):
  with self.assertRaises(ValueError):patch_text('[se:2]文字','[se:1]文字')
 def test_no_new_model(self):
  with self.assertRaises(ValueError):patch_text('[chara:2:motion_0]文字','[chara:1:motion_0]文字')
 def test_no_deleted_wait(self):
  with self.assertRaises(ValueError):patch_text('文字','[wait:1]文字')
 def test_no_reordered_commands(self):
  with self.assertRaises(ValueError):patch_text('[se:1][wait:1]文字','[wait:1][se:1]文字')
 def test_reviewed_chinese_colour_not_japanese_text(self):self.assertEqual(patch_text('[textYellow:心魔]出现','[textYellow:キモチ]出现'),'[textYellow:心魔]出现')
 def test_literal_brackets_do_not_silently_disappear(self):
  with self.assertRaises(ValueError):patch_text('【类别】内容','[类别]内容')
 def test_verified_bracket_only(self):validate_operations('adv/102301-4_Z9WSZ.json',[[['story','group_1',40,'textRight'],'chara:100501:effect_emotion_joy_0][se:7222_happy]可以参加啦！','[chara:100501:effect_emotion_joy_0][se:7222_happy]可以参加啦！']])
 def test_bracket_fix_cannot_rewrite_payload(self):
  with self.assertRaises(ValueError):validate_operations('adv/102301-4_Z9WSZ.json',[[['story','group_1',40,'textRight'],'chara:100501:effect_emotion_joy_0][se:7222_happy]旧句','[chara:100501:effect_emotion_joy_0][se:7222_happy]改写']])
 def test_nontext_object_not_editable(self):
  with self.assertRaises(ValueError):validate_operations('adv/x.json',[[['story','group_1',0,'bg'],'a','b']])
 def test_unrecorded_move_detected(self):
  old={'story':{'group_1':[{'textLeft':'旧','chara':[{'id':1}]}]}};new={'story':{'group_1':[{'textLeft':'新','chara':[{'id':2}]}]}}
  with self.assertRaises(ValueError):verify_display_only(json.dumps(old),json.dumps(new),[[['story','group_1',0,'textLeft'],'旧','新']])

if __name__=='__main__':unittest.main()

import unittest,json,hashlib
from interview_layout import is_interview_marker,interview_names
from frame_prefix import plan_frames
from prefix_exact import clean,rows

def make(turns):return json.dumps({'story':{'group_1':turns}},ensure_ascii=False).encode()
class TitleRecognition(unittest.TestCase):
 def test_raw_card(self):self.assertTrue(is_interview_marker('[textBlack:—取材记录—]@[textBlack:甲]'))
 def test_single_wrapper(self):self.assertTrue(is_interview_marker('[textBlack:―取材记录―@由比 鹤乃]'))
 def test_japanese(self):self.assertTrue(is_interview_marker('[textBlack:―取材記録―]@[textBlack:環いろは]'))
 def test_rendered_card(self):self.assertTrue(is_interview_marker('<black>—取材记录—</black>\\n<black>甲</black>'))
 def test_actual_newline(self):self.assertTrue(is_interview_marker('—采访记录—\n甲'))
 def test_ordinary_sentence(self):self.assertFalse(is_interview_marker('我们采访记录的魔法少女等人的心路历程'))
 def test_ordinary_quote(self):self.assertFalse(is_interview_marker('“现公开一份采访记录，对象是作家@采访通过文字消息进行……”'))
 def test_ordinary_colour(self):self.assertFalse(is_interview_marker('[textBlack:这是一份采访记录]'))
 def test_later_title_not_first(self):self.assertFalse(is_interview_marker('有人说@—取材记录—'))
 def test_blank_none_number(self):
  for x in ('',None,123):self.assertFalse(is_interview_marker(x))
 def test_legacy_names_unchanged(self):self.assertEqual(interview_names(clean('[textBlack:—取材记录—]@[textBlack:甲]@[textBlack:乙]')),['<black>甲</black>','<black>乙</black>'])

class ExactExpandedCards(unittest.TestCase):
 def run_plan(self,raw,old,new=None,mapping=None,allowed=None):
  return plan_frames(raw,lambda f:(old,new or old,'source/'+f,'verified-blob'),mapping or {},allowed or set())
 def base(self,body):return ('---[Section 1] (Source: 123-1.json) ---\n'+body).encode()
 def test_real_card_name_repair(self):
  d=make([{'nameLeft':'梅丽莎','textLeft':'开场'},{'narration':'[textBlack:—取材记录—]@[textBlack:梅丽莎]'}, {'nameLeft':'梅丽莎','textLeft':'[textBlack:回忆]'}])
  raw=self.base('旧名字: 开场\n\n―― 取材记录 ――\n旁白: <black>梅丽莎</black>\n旧名字: <black>回忆</black>\n')
  out,e,h,_=self.run_plan(raw,d,mapping={'旧名字':'梅丽莎'});self.assertFalse(h);self.assertEqual(len(e),2);self.assertIn('旁白: <black>梅丽莎</black>',out.decode())
 def test_default_helper_still_holds_cards(self):
  with self.assertRaises(ValueError):rows(json.loads(make([{'narration':'—取材记录—'}])),'group_1')
 def test_ordinary_mention_preserved(self):
  d=make([{'nameNarration':'笼目','narration':'我们采访记录的经历'}]);raw=self.base('旁白: 我们采访记录的经历\n')
  out,e,h,_=self.run_plan(raw,d);self.assertEqual(len(e),1);self.assertFalse(h);self.assertTrue(out.decode().endswith('笼目: 我们采访记录的经历\n'))
 def test_body_mismatch_preserves_entire_section(self):
  d=make([{'nameNarration':'甲','narration':'一'},{'narration':'二'}]);raw=self.base('旁白: 一\n旁白: 别的翻译\n')
  out,e,h,_=self.run_plan(raw,d);self.assertEqual(out,raw);self.assertFalse(e);self.assertTrue(h)
 def test_physical_multiline_prefix_only(self):
  d=make([{'nameNarration':'甲','narration':'一\n二'}]);raw=self.base('旁白: 一\n二\n')
  out,e,h,_=self.run_plan(raw,d);self.assertFalse(h);self.assertEqual(len(e),1);self.assertEqual(out,raw.replace('旁白'.encode(),'甲'.encode()))
 def test_multiline_continuation_mismatch(self):
  d=make([{'nameNarration':'甲','narration':'一\n二'}]);raw=self.base('旁白: 一\n三\n')
  out,e,h,_=self.run_plan(raw,d);self.assertEqual(out,raw);self.assertFalse(e);self.assertTrue(h)
 def test_correct_alias_is_not_overwritten(self):
  d=make([{'nameNarration':'夏目佳子','narration':'一'}]);raw=self.base('佳子: 一\n')
  out,e,_,_=self.run_plan(raw,d);self.assertEqual(out,raw);self.assertFalse(e)
 def test_unknown_name_not_guessed(self):
  d=make([{'textLeft':'一'}]);raw=self.base('旧名字: 一\n')
  out,e,_,_=self.run_plan(raw,d,mapping={'旧名字':'甲'});self.assertEqual(out,raw);self.assertFalse(e)
 def test_explicit_anonymous_remains(self):
  d=make([{'nameNarration':'','narration':'一'}]);raw=self.base('旁白: 一\n')
  out,e,_,_=self.run_plan(raw,d);self.assertEqual(out,raw);self.assertFalse(e)
 def test_choice_held(self):
  d=make([{'select':[{'textSelect':'选项'}]}]);raw=self.base('选项: 选项\n')
  out,e,h,_=self.run_plan(raw,d);self.assertEqual(out,raw);self.assertTrue(h)
 def test_bom_crlf_final_no_newline(self):
  d=make([{'nameNarration':'甲','narration':'一'}]);raw=b'\xef\xbb\xbf'+self.base('旁白: 一').replace(b'\n',b'\r\n')
  out,e,h,_=self.run_plan(raw,d);self.assertFalse(h);self.assertEqual(out,raw.replace('旁白'.encode(),'甲'.encode()))
 def test_unapproved_prose_change_rejected(self):
  a=make([{'nameNarration':'甲','narration':'一'}]);b=make([{'nameNarration':'甲','narration':'二'}]);raw=self.base('甲: 一\n')
  out,e,h,_=self.run_plan(raw,a,b);self.assertEqual(out,raw);self.assertTrue(h)
 def test_approved_prose_change_only(self):
  a=make([{'nameNarration':'甲','narration':'一'}]);b=make([{'nameNarration':'甲','narration':'二'}]);raw=self.base('甲: 一\n')
  out,e,h,_=self.run_plan(raw,a,b,allowed={('123-1.json','group_1',0,'narration')});self.assertFalse(h);self.assertTrue(out.decode().endswith('甲: 二\n'))
 def test_idempotent(self):
  d=make([{'nameNarration':'甲','narration':'一'}]);raw=self.base('旁白: 一\n');out,_,_,_=self.run_plan(raw,d);again,e,_,_=self.run_plan(out,d);self.assertEqual(out,again);self.assertFalse(e)

if __name__=='__main__':unittest.main()

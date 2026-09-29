"""Regression cases for text loss and preassigned speaker state (no network)."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('channel_extractor', ROOT/'reconstruction_v12.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)

class TextChannels(unittest.TestCase):
    def render(self, turns):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'123-1.json'
            path.write_text(json.dumps({'story': turns if isinstance(turns, dict) else {'group_1':turns}}, ensure_ascii=False), encoding='utf-8')
            return r.build_txt_from_json(str(path))
    def test_both_dialogue_sides(self):
        result=self.render([{'nameLeft':'那由他','nameRight':'彩羽','textLeft':'问题','textRight':'回答'}])
        self.assertIn('那由他: 问题\n彩羽: 回答\n', result)
    def test_all_three_sides(self):
        result=self.render([{'textLeft':'左','textRight':'右','textCenter':'中'}])
        for value in ['左','右','中']: self.assertIn('旁白: '+value+'\n',result)
    def test_preassigned_narrator(self):
        result=self.render([{'nameNarration':'丽'},{'narration':'独白'}])
        self.assertIn('丽: 独白\n',result)
    def test_narrator_survives_dialogue(self):
        result=self.render([{'nameNarration':'丽'},{'nameLeft':'静香','textLeft':'对白'},{'narration':'独白'}])
        self.assertIn('丽: 独白\n',result)
    def test_explicit_narrator_clear(self):
        result=self.render([{'nameNarration':'丽'},{'nameNarration':''},{'narration':'匿名'}])
        self.assertIn('旁白: 匿名\n',result)
    def test_named_monologue_sequence(self):
        result=self.render([{'nameNarration':'那由他','narration':'一'},{'narration':'二'},{'narration':'三'}])
        self.assertIn('那由他: 一\n那由他: 二\n那由他: 三\n',result)
    def test_fnarration(self):
        result=self.render([{'nameFnarration':'甲'},{'Fnarration':'全屏'}])
        self.assertIn('甲: 全屏\n',result)
    def test_fnarration_alias(self):
        result=self.render([{'nameFnarration':'甲','progressFnarration':'接续'}])
        self.assertIn('甲: 接续\n',result)
    def test_narration_and_dialogue(self):
        result=self.render([{'narration':'旁白','nameLeft':'甲','textLeft':'回应'}])
        self.assertIn('旁白: 旁白\n甲: 回应\n',result)
    def test_empty_narration_does_not_hide_dialogue(self):
        self.assertIn('旁白: 回应\n',self.render([{'narration':'','textRight':'回应'}]))
    def test_two_narration_channels(self):
        result=self.render([{'nameFnarration':'甲','Fnarration':'全屏','nameNarration':'乙','narration':'普通'}])
        self.assertIn('甲: 全屏\n乙: 普通\n',result)
    def test_empty_primary_alias_falls_back(self):
        self.assertIn('旁白: 备用\n',self.render([{'textLeft':'','textAvLeft':'备用'}]))
    def test_choice_cannot_hide_dialogue(self):
        result=self.render([{'select':[{'textSelect':'选择','group':'group_2'}],'textLeft':'提示'}])
        self.assertIn('选项: 【选择】',result)
        self.assertIn('旁白: 提示\n',result)
    def test_empty_name_is_not_cached(self):
        result=self.render([{'chara':[{'id':1,'pos':0}],'nameLeft':'旧名','textLeft':'一'}, {'nameLeft':'','textLeft':'二'}])
        self.assertIn('旁白: 二\n',result)
    def test_branch_narrator_isolation(self):
        result=self.render({'group_1':[{'nameNarration':'甲','narration':'一'}], 'group_2':[{'narration':'二'}]})
        self.assertIn('旁白: 二\n',result)
    def test_colour_text_and_controls(self):
        self.assertIn('甲: <yellow>词语</yellow>\\n尾\n',self.render([{'nameLeft':'甲','textLeft':'[textYellow:词语]@[wait:1]尾'}]))
    def test_generic_text(self):
        self.assertIn('甲: 通用\n',self.render([{'name':'甲','text':'通用'}]))
    def test_visible_text_type_error(self):
        with self.assertRaises(ValueError): self.render([{'textLeft':123}])

if __name__=='__main__':unittest.main()

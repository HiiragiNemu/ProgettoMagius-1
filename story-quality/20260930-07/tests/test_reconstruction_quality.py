"""Regression tests for source-safe Reader extraction; no network required."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / 'reconstruction_v12.py'
if not MODULE.exists():
    MODULE = Path(__file__).with_name('reconstruction_v12.py')
spec = importlib.util.spec_from_file_location('reconstruction_quality', MODULE)
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


class ReconstructionQualityTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        r.GLOBAL_ID_MAP.clear()
        r.BRANCH_REPORT.clear()

    def tearDown(self):
        self.directory.cleanup()

    def source(self, name, turns):
        p = self.root / name
        p.write_text(json.dumps({'story': turns}, ensure_ascii=False), encoding='utf-8')
        return str(p)

    def render(self, turns, name='123-1.json'):
        return r.build_txt_from_json(self.source(name, turns))

    def test_no_cross_file_or_language_name_leak(self):
        self.render({'group_1': [{'chara': [{'id': 800600, 'pos': 0}],
                                 'nameLeft': '日文原稿中的人物', 'textLeft': '旧稿'}]}, '111-1.json')
        result = self.render({'group_1': [{'chara': [{'id': 800600, 'pos': 0}],
                                           'textLeft': '不具名店员'}]}, '222-1.json')
        self.assertIn('旁白: 不具名店员\n', result)
        self.assertNotIn('日文原稿中的人物', result)

    def test_explicit_empty_name_stays_anonymous(self):
        result = self.render({'group_1': [
            {'chara': [{'id': 1, 'pos': 0}], 'nameLeft': '旧姓名', 'textLeft': '一'},
            {'nameLeft': '', 'textLeft': '二'}, {'textLeft': '三'}]})
        self.assertIn('旁白: 二\n旁白: 三\n', result)

    def test_in_file_inheritance_and_narration(self):
        result = self.render({'group_1': [
            {'chara': [{'id': 1, 'pos': 0}], 'nameLeft': '千春', 'textLeft': '一'},
            {'textLeft': '二'}, {'nameNarration': '千春', 'narration': '三'},
            {'narration': '四'}, {'nameNarration': '', 'narration': '五'}]})
        self.assertIn('千春: 一\n千春: 二\n千春: 三\n千春: 四\n旁白: 五\n', result)

    def test_unique_fixed_character_forward_reference_is_local(self):
        result = self.render({'group_1': [
            {'chara': [{'id': 305301, 'pos': 1}], 'textCenter': '先说话'},
            {'nameCenter': '牧野郁美', 'textCenter': '再署名'},
            {'nameCenter': '', 'textCenter': '明确匿名'}]})
        self.assertIn('牧野郁美: 先说话', result)
        self.assertIn('旁白: 明确匿名', result)
        anonymous = self.render({'group_1': [
            {'chara': [{'id': 800600, 'pos': 0}], 'textLeft': '先说话'},
            {'nameLeft': '可复用模型', 'textLeft': '后来署名'}]})
        self.assertIn('旁白: 先说话', anonymous)

    def test_array_form_and_inline_control_rendering(self):
        result = self.render([{'nameRight': '沙绪',
                               'textRight': '[se:1]甲@[textYellow:乙][br]丙[wait:1]'}])
        self.assertIn('沙绪: 甲\\n<yellow>乙</yellow>\\n丙\n', result)

    def test_natural_branch_order(self):
        result = self.render({k: [{'narration': k}] for k in ('group_10', 'group_2', 'group_1')})
        self.assertLess(result.index('旁白: group_1\n'), result.index('旁白: group_2\n'))
        self.assertLess(result.index('旁白: group_2\n'), result.index('旁白: group_10\n'))

    def test_corrupt_json_raises_instead_of_silent_empty(self):
        p = self.root / '123-1.json'
        p.write_text('{', encoding='utf-8')
        with self.assertRaises(ValueError):
            r.build_txt_from_json(str(p))

    def test_invalid_story_shape_raises(self):
        with self.assertRaises(ValueError):
            self.render('not a story')
        with self.assertRaises(ValueError):
            self.render({'group_1': ['not a turn']})

    def invoke_main(self):
        cwd, dirs = os.getcwd(), r.TARGET_DIRS
        try:
            os.chdir(self.root)
            r.TARGET_DIRS = ['.']
            with contextlib.redirect_stdout(io.StringIO()):
                r.main()
        finally:
            os.chdir(cwd)
            r.TARGET_DIRS = dirs

    def test_failed_group_cannot_overwrite_complete_aggregate(self):
        self.source('123-1.json', {'group_1': [{'narration': '第一节'}]})
        (self.root / '123-2.json').write_text('{', encoding='utf-8')
        p = self.root / '123_1-2.txt'
        p.write_text('原完整稿', encoding='utf-8')
        with self.assertRaises(SystemExit):
            self.invoke_main()
        self.assertEqual(p.read_text(), '原完整稿')
        self.assertFalse((self.root / '123_1-2.txt.bak').exists())

    def test_equivalent_aliases_survive_and_stay_identical(self):
        self.source('123-1.json', {'group_1': [{'nameLeft': '千春', 'textLeft': '新稿'}]})
        for name in ('123_1.txt', '123_1-1.txt', '123_1-9.txt'):
            (self.root / name).write_text('原稿', encoding='utf-8')
        self.invoke_main()
        self.assertEqual((self.root/'123_1.txt').read_bytes(), (self.root/'123_1-1.txt').read_bytes())
        self.assertIn('新稿', (self.root/'123_1-1.txt').read_text())
        self.assertEqual((self.root/'123_1-9.txt').read_text(), '原稿')

    def test_choices_and_empty_scripts(self):
        result = self.render({'group_1': [{'select': [{'textSelect': '选择', 'group': 'group_2'}]}],
                              'group_2': [{'nameLeft': '甲', 'textLeft': '结果'}]})
        self.assertIn('选项: 【选择】→ group_2', result)
        self.assertEqual(self.render([]), '')


if __name__ == '__main__':
    unittest.main()

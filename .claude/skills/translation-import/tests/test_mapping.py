"""Offline regression tests for Chinese sentence order and protected markup."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from html_blocks import Plan, compare_html, visible_text
from skeleton import build_entries
from validate import check_description


class StructureTests(unittest.TestCase):
    def test_complete_formatted_phrases_can_change_order(self):
        en = '<p>You gain <em>advantage</em> on <strong>saving throws</strong>.</p>'
        zh = '<p>你進行<strong>豁免</strong>時具有<em>優勢</em>。</p>'
        self.assertEqual(check_description(en, zh), [])

    def test_links_and_references_can_change_order_within_paragraph(self):
        en = '<p>@UUID[A]{A} and @UUID[B]{B}: &Reference[Dash] and &Reference[Dodge].</p>'
        zh = '<p>&Reference[Dodge]{迴避}與&Reference[Dash]{疾走}：@UUID[B]{乙}和@UUID[A]{甲}。</p>'
        self.assertEqual(check_description(en, zh), [])

    def test_link_reordering_keeps_its_formatting(self):
        en = '<p><em>@UUID[A]{A}</em>, <strong>@UUID[B]{B}</strong>.</p>'
        zh = '<p><strong>@UUID[B]{乙}</strong>與<em>@UUID[A]{甲}</em>。</p>'
        self.assertEqual(check_description(en, zh), [])
        wrong = '<p><strong>@UUID[A]{甲}</strong>與<em>@UUID[B]{乙}</em>。</p>'
        self.assertTrue(check_description(en, wrong))

    def test_changed_lost_or_duplicated_link_is_rejected(self):
        en = '<p>@UUID[A]{A} and @UUID[B]{B}.</p>'
        for zh in ['<p>@UUID[C]{甲}和@UUID[B]{乙}。</p>',
                   '<p>@UUID[A]{甲}。</p>', '<p>@UUID[A]{甲}和@UUID[A]{甲}。</p>']:
            with self.subTest(zh=zh):
                self.assertTrue(check_description(en, zh))

    def test_moving_link_between_paragraphs_is_rejected(self):
        en = '<p>@UUID[A]{A}</p><p>@UUID[B]{B}</p>'
        zh = '<p>@UUID[B]{乙}</p><p>@UUID[A]{甲}</p>'
        self.assertTrue(check_description(en, zh))

    def test_reference_modifiers_and_rolls_are_protected(self):
        en = '<p>&Reference[Dash apply=false] [[/heal 2d4]]{2d4}</p>'
        zh = '<p>恢復[[/heal 2d4]]{2d4}點生命值，&Reference[Dash apply=false]{疾走}。</p>'
        self.assertEqual(check_description(en, zh), [])
        self.assertTrue(check_description(en, zh.replace('apply=false', 'apply=true')))
        self.assertTrue(check_description(en, zh.replace('[[/heal 2d4]]', '[[/heal 4d4]]')))

    def test_nested_format_and_attributes_remain_protected(self):
        en = '<p><em><strong class="x">Bonus</strong></em></p>'
        for zh in ['<p><strong class="x"><em>好處</em></strong></p>',
                   '<p><em><strong class="y">好處</strong></em></p>']:
            self.assertTrue(check_description(en, zh))

    def test_section_and_table_structure_survives(self):
        en = '<section class="secret hide-in-embed"><p class="hanging">Text</p><table><tr><th>Type</th><td>Value</td></tr></table></section>'
        zh = en.replace('Text', '文字').replace('Type', '類型').replace('Value', '數值')
        self.assertEqual(check_description(en, zh), [])
        self.assertTrue(check_description(en, zh.replace('class="hanging"', 'class="other"')))
        self.assertTrue(check_description(en, zh.replace('<table>', '').replace('</table>', '')))

    def test_tables_and_classed_paragraphs_are_checked_for_english(self):
        for html in ['<p class="hanging">Untranslated</p>', '<table><tr><td>Untranslated</td></tr></table>']:
            self.assertTrue(any('英文殘留' in error for error in check_description(html, html)))

    def test_entities_void_tags_and_comments_round_trip(self):
        html = '<p>A &amp; B &Reference[Dash]<br />C&#160;D<img src="x" /></p><!-- unchanged -->'
        self.assertEqual(Plan(html).build({}), html)
        self.assertEqual(visible_text('<em>甲</em>&amp;&Reference[Dash]{疾走}'), '甲&疾走')

    def test_malformed_html_is_rejected(self):
        self.assertTrue(compare_html('<p>Text</p>', '<p><em>文字</p>'))

    def test_literal_code_is_protected(self):
        en = '<p>Use <code>@abilities.int.mod</code>.</p>'
        zh = '<p>使用<code>@abilities.int.mod</code>。</p>'
        self.assertEqual(check_description(en, zh), [])
        self.assertTrue(check_description(en, zh.replace('int.mod', 'wis.mod')))

    def test_uuid_label_cannot_disappear(self):
        self.assertTrue(check_description('<p>@UUID[A]{Name}</p>', '<p>@UUID[A]</p>'))


class DraftMappingTests(unittest.TestCase):
    def setUp(self):
        self.en = {'Example': {'name': 'Example', 'description': '<p>You gain <em>advantage</em> on <strong>saving throws</strong>.</p>'}}
        self.zh = '你進行<strong>豁免</strong>時具有<em>優勢</em>。'
        self.sheet = {'schema_version': 2, 'entries': {'Example': {
            'name': '範例', 'name_en': 'Example', 'blocks': [{
                'id': 'b0001', 'en': Plan(self.en['Example']['description']).blocks[0].html,
                'zh': self.zh, 'source': 'draft', 'basis': ''}]}}}
        self.draft = {'Example': '範例你進行豁免時具有優勢。'}

    def test_output_keeps_complete_draft_sentence(self):
        result = build_entries(self.sheet, self.en, self.draft)
        self.assertEqual(result['entries']['Example']['description'], '<p>' + self.zh + '</p>')

    def test_english_order_rewrite_is_not_in_draft(self):
        self.sheet['entries']['Example']['blocks'][0]['zh'] = '你具有<em>優勢</em>，當進行<strong>豁免</strong>時。'
        with self.assertRaisesRegex(ValueError, '完整中文不在底稿'):
            build_entries(self.sheet, self.en, self.draft)

    def test_blank_does_not_silently_fall_back_to_english(self):
        self.sheet['entries']['Example']['blocks'][0]['zh'] = ''
        with self.assertRaisesRegex(ValueError, '未填寫完整中文'):
            build_entries(self.sheet, self.en, self.draft)

    def test_supplement_requires_explicit_basis(self):
        block = self.sheet['entries']['Example']['blocks'][0]
        block.update(source='supplement', zh='你具有<em>優勢</em>，當進行<strong>豁免</strong>時。')
        with self.assertRaisesRegex(ValueError, '補翻須列明'):
            build_entries(self.sheet, self.en, self.draft)

    def test_draft_text_cannot_be_replaced_with_unlabelled_link(self):
        en = {'Example': {'name': 'Example', 'description': '<p>@UUID[A]{Name}</p>'}}
        sheet = copy.deepcopy(self.sheet)
        sheet['entries']['Example']['blocks'] = [{'id': 'b0001', 'en': '@UUID[A]{Name}', 'zh': '@UUID[A]', 'source': 'draft'}]
        with self.assertRaisesRegex(ValueError, '遺失可見文字'):
            build_entries(sheet, en, {'Example': '範例中文名稱'})

    def test_changed_en_and_old_sheet_require_new_extraction(self):
        self.sheet['schema_version'] = 1
        with self.assertRaisesRegex(ValueError, '重新 extract'):
            build_entries(self.sheet, self.en, self.draft)
        self.sheet['schema_version'] = 2
        self.sheet['entries']['Example']['blocks'][0]['en'] = 'Other'
        with self.assertRaisesRegex(ValueError, 'EN 已變動'):
            build_entries(self.sheet, self.en, self.draft)

    def test_identical_english_blocks_map_independently(self):
        en = {'Example': {'name': 'Example', 'description': '<table><tr><td>Same</td><td>Same</td></tr></table>'}}
        sheet = copy.deepcopy(self.sheet)
        sheet['entries']['Example']['blocks'] = [
            {'id': 'b0001', 'en': 'Same', 'zh': '甲', 'source': 'draft'},
            {'id': 'b0002', 'en': 'Same', 'zh': '乙', 'source': 'draft'}]
        result = build_entries(sheet, en, {'Example': '甲乙'})
        self.assertEqual(result['entries']['Example']['description'], '<table><tr><td>甲</td><td>乙</td></tr></table>')

    def test_cli_extract_build_validate_round_trip(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            book = root / 'compendium' / 'en' / 'example'
            book.mkdir(parents=True)
            (book / 'example.feats.json').write_text(json.dumps({'entries': self.en}), encoding='utf-8')
            sheet_path, draft_path, aligned, upload = [root / name for name in ['sheet.json', 'draft.txt', 'aligned.json', 'upload.json']]

            def run(script, *args):
                return subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)], capture_output=True, encoding='utf-8')

            result = run('skeleton.py', '--repo', root, 'extract', '--book', 'example', '--component', 'feats', '--out', sheet_path)
            self.assertEqual(result.returncode, 0, result.stderr)
            extracted = json.loads(sheet_path.read_text(encoding='utf-8'))
            extracted['entries']['Example'].update(self.sheet['entries']['Example'])
            sheet_path.write_text(json.dumps(extracted), encoding='utf-8')
            draft_path.write_text('### Example\n範例\n你進行豁免時具有優勢。\n', encoding='utf-8')
            result = run('skeleton.py', '--repo', root, 'build', sheet_path, '--draft', draft_path, '--out', aligned)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = run('validate.py', aligned, '--repo', root, '--book', 'example', '--component', 'feats', '--out', upload)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(json.loads(upload.read_text(encoding='utf-8'))['entries']['Example']['description'], '<p>' + self.zh + '</p>')

    def test_failed_batch_does_not_write_partial_upload(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            book = root / 'compendium' / 'en' / 'example'
            book.mkdir(parents=True)
            entries = {'Good': {'description': '<p>Text</p>'}, 'Bad': {'description': '<p>@UUID[A]{Name}</p>'}}
            (book / 'example.feats.json').write_text(json.dumps({'entries': entries}), encoding='utf-8')
            aligned, upload = root / 'aligned.json', root / 'upload.json'
            aligned.write_text(json.dumps({'entries': {'Good': {'name': '好', 'description': '<p>文字</p>'},
                                                      'Bad': {'name': '壞', 'description': '<p>@UUID[B]{名稱}</p>'}}}), encoding='utf-8')
            result = subprocess.run([sys.executable, str(SCRIPTS / 'validate.py'), str(aligned), '--repo', str(root),
                                     '--book', 'example', '--component', 'feats', '--out', str(upload)],
                                    capture_output=True, encoding='utf-8')
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(upload.exists())


if __name__ == '__main__':
    unittest.main()

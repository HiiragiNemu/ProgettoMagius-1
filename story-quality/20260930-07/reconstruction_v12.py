"""从剧情 JSON 生成阅读文本；聚合完成不代表译文已经校对。"""
import json
import os
import re
import shutil
import tempfile
from collections import defaultdict

TARGET_DIRS = [
    "magireco-source-master/Scenarios_full",
    "magireco-translate-data-master/Scenarios_full",
]
# 仅作本次运行的统计，绝不参与其他文件的说话人推断。
GLOBAL_ID_MAP = {}
BRANCH_REPORT = defaultdict(list)
INTERVIEW_MARKERS = ['取材記録', '采访记录', '取材记录', '取材録']


def natural_key(value):
    return tuple((0, int(s)) if s.isdigit() else (1, s)
                 for s in re.split(r'(\d+)', value))


def clean_and_format_content(text):
    if not isinstance(text, str):
        return ""
    text = text.replace('@', '\\n').replace('[br]', '\\n')
    text = text.replace('「textBlack:', '[textBlack:').replace('『textBlack:', '[textBlack:')
    for colour in ('Red', 'Blue', 'Yellow', 'Black'):
        text = re.sub(r'\[text' + colour + r':(.*?)\]',
                      r'<' + colour.lower() + r'>\1</' + colour.lower() + '>',
                      text, flags=re.DOTALL)
    return re.sub(r'\[.*?\]', '', text).strip()


def story_groups(data, filename):
    if not isinstance(data, dict) or 'story' not in data:
        raise ValueError(f'{filename}: missing story object')
    story = data['story']
    if isinstance(story, list):
        story = {'group_1': story}
    if not isinstance(story, dict):
        raise ValueError(f'{filename}: invalid story container')
    groups = []
    for key in sorted(story, key=natural_key):
        if not key.startswith('group_'):
            continue
        turns = story[key]
        if not isinstance(turns, list) or any(not isinstance(t, dict) for t in turns):
            raise ValueError(f'{filename}: invalid turns in {key}')
        groups.append((key, turns))
    if story and not groups:
        raise ValueError(f'{filename}: no recognised story groups')
    return groups


def extract_branch_info(data, json_filename):
    groups = story_groups(data, json_filename)
    if len(groups) <= 1:
        return None
    selects = []
    for group, turns in groups:
        for item in turns:
            for opt in item.get('select', []):
                selects.append({'from_group': group, 'to_group': opt.get('group', '?'),
                                'text': opt.get('textSelect', '?'),
                                'alt_id': opt.get('alternativeId', '?')})
    return {'file': json_filename, 'groups': [g for g, _ in groups],
            'group_count': len(groups), 'selects': selects,
            'skip_transitions': data.get('skipTransitionList', [])}


def is_interview_marker(text):
    # A title card starts with a standalone title. Prose mentioning an
    # interview is still prose and must never be dropped during extraction.
    if not isinstance(text, str) or not text:
        return False
    plain = re.sub(r'\[text(?:Black|Red|Blue|Yellow):([^\]]*)\]', r'\1', text, flags=re.DOTALL)
    plain = re.sub(r'</?(?:black|red|blue|yellow)>', '', plain, flags=re.IGNORECASE)
    first = re.split(r'@|\\n|\r?\n|\[br\]', plain, maxsplit=1)[0].strip()
    return re.fullmatch(r'[\s―—–\-－ー─]*(?:取材記録|采访记录|取材记录|取材録)[\s―—–\-－ー─]*', first) is not None


def extract_interview_name(cleaned_text):
    names = []
    for part in cleaned_text.split('\\n'):
        value = re.sub(r'\[textBlack:(.*?)\]', r'\1', part).strip()
        if value and not any(token in value for token in ('记录', '記録', '―')):
            names.append(value)
    return names


def build_txt_from_json(json_path):
    # 解析错误必须传给调用者；返回空串会使整组缺章却被当作成功。
    with open(json_path, 'r', encoding='utf-8-sig') as stream:
        data = json.load(stream)
    filename = os.path.basename(json_path)
    match = re.search(r'[-_](\d+)(?:_|\.)', filename)
    section = match.group(1) if match else '?'
    groups = story_groups(data, filename)
    branch = extract_branch_info(data, filename)
    if branch:
        BRANCH_REPORT[os.path.dirname(json_path)].append(branch)
    output = []
    for group_name, turns in groups:
        lines = []
        pos_to_id = dict.fromkeys(('Left', 'Right', 'Center'))
        explicit = dict.fromkeys(pos_to_id)
        # 通用 NPC 模型会被复用，日文与中文目录也会顺序处理。
        # 因此只允许同一文件、同一分支内的姓名回退。
        local_names = {}
        # 同一分支里已明确、唯一命名的固定角色可用于前向引用。
        # 不跨文件收集，也不为会被复用的通用 NPC 模型预设姓名。
        seed_positions = dict.fromkeys(pos_to_id)
        candidates = defaultdict(set)
        for turn in turns:
            for chara in turn.get('chara', []):
                cid = chara.get('id')
                if cid and 'pos' in chara:
                    pos = 'Left' if chara['pos'] == 0 else 'Center' if chara['pos'] == 1 else 'Right'
                    seed_positions[pos] = str(cid)
            for pos, cid in seed_positions.items():
                value = turn.get('name' + pos)
                if cid and cid.isdigit() and int(cid) < 700000 and isinstance(value, str) and value:
                    candidates[cid].add(value)
        local_names.update((cid, next(iter(names))) for cid, names in candidates.items() if len(names) == 1)
        narrator = '旁白'
        fnarrator = '旁白'
        for item in turns:
            for chara in item.get('chara', []):
                cid = chara.get('id')
                if cid and 'pos' in chara:
                    pos = 'Left' if chara['pos'] == 0 else 'Center' if chara['pos'] == 1 else 'Right'
                    if pos_to_id[pos] and pos_to_id[pos] != str(cid):
                        explicit[pos] = None
                    pos_to_id[pos] = str(cid)
            for pos in pos_to_id:
                key = 'name' + pos
                if key in item:
                    value = item[key]
                    if not isinstance(value, str):
                        raise ValueError(f'{filename}: invalid {key}')
                    explicit[pos] = value
                    cid = pos_to_id[pos]
                    if cid and value:
                        local_names[cid] = value
                        GLOBAL_ID_MAP[(json_path, group_name, cid)] = value
            # Names are state commands: they may precede their first visible text.
            if 'nameNarration' in item:
                narrator = item['nameNarration'] or '旁白'
            if 'nameFnarration' in item:
                fnarrator = item['nameFnarration'] or '旁白'
            if 'select' in item:
                for option in item['select']:
                    text = option.get('textSelect', '')
                    if text:
                        lines.append(f"选项: 【{text}】→ {option.get('group', '')}\n")
            if 'narration' in item and is_interview_marker(str(item['narration'])):
                cleaned = clean_and_format_content(str(item['narration']))
                if cleaned:
                    lines.append('\n―― 取材记录 ――\n')
                    lines.extend(f'旁白: {name}\n' for name in extract_interview_name(cleaned))
                narrator = '旁白'
            def emit(value, speaker):
                if value is None or value == '':
                    return
                if not isinstance(value, str):
                    raise ValueError(f'{filename}: non-string display text')
                cleaned = clean_and_format_content(value)
                if cleaned:
                    lines.append(f'{speaker}: {cleaned}\n')

            # Independent text channels must not suppress one another.  Alias
            # keys represent the same channel; use its first non-empty value.
            emit(item.get('Fnarration') or item.get('fnarration') or
                 item.get('progressFnarration'), fnarrator)
            if not ('narration' in item and is_interview_marker(str(item['narration']))):
                emit(item.get('narration') or item.get('progressNarration'), narrator)
            for pos in ('Left', 'Right', 'Center'):
                value = item.get('text' + pos) or item.get('textAv' + pos)
                if not value:
                    continue
                if explicit[pos] is not None:
                    speaker = explicit[pos] or '旁白'
                else:
                    speaker = local_names.get(pos_to_id[pos]) or '旁白'
                emit(value, speaker)
            if item.get('text') and not any(item.get('text' + p) or item.get('textAv' + p)
                                           for p in ('Left', 'Right', 'Center')):
                emit(item['text'], item.get('name') or '旁白')
        if lines:
            if group_name == 'group_1':
                heading = f'\n---[Section {section}] (Source: {filename}) ---\n'
            else:
                label = group_name.replace('group_', 'Branch ')
                heading = f'\n--- [Section {section} - {label}] (Source: {filename}) ---\n'
            output.append(heading + ''.join(lines))
    return ''.join(output)


def print_branch_report():
    if BRANCH_REPORT:
        print('多分支剧情报告')
        for folder, entries in sorted(BRANCH_REPORT.items()):
            print(f'{os.path.basename(folder)}: {len(entries)} 个多分支文件')


def write_text_atomic(path, content):
    if os.path.exists(path):
        with open(path, encoding='utf-8') as stream:
            if stream.read() == content:
                return False
        if not os.path.exists(path + '.bak'):
            shutil.copy2(path, path + '.bak')
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n',
                                         dir=os.path.dirname(path), delete=False) as stream:
            temporary = stream.name
            stream.write(content)
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            os.unlink(temporary)
    return True


def main():
    rebuilt = skipped = failures = 0
    GLOBAL_ID_MAP.clear()
    BRANCH_REPORT.clear()
    for relative in TARGET_DIRS:
        base = os.path.join(os.getcwd(), relative)
        if not os.path.isdir(base):
            continue
        for root, dirs, files in os.walk(base):
            dirs.sort(key=natural_key)
            groups = defaultdict(list)
            for name in files:
                if not name.endswith('.json'):
                    continue
                match = re.match(r'^(\d+)', name)
                if not match:
                    continue
                fid = match.group(1)
                if fid.startswith('51701') and len(fid) >= 7:
                    key = f'51701_{int(fid[5:]) // 10}'
                elif len(fid) >= 6 and fid.startswith('5'):
                    key = fid[:5]
                else:
                    key = fid
                groups[key].append(name)
            for key in sorted(groups, key=natural_key):
                names = sorted(groups[key], key=natural_key)
                first = re.match(r'^(\d+)[-_](\d+)', names[0])
                last = re.match(r'^(\d+)[-_](\d+)', names[-1])
                id_first = first.group(1) if first else key
                id_last = last.group(1) if last else key
                start = first.group(2) if first else '1'
                end = last.group(2) if last else str(len(names))
                if id_first != id_last:
                    target = f'{id_first}-{id_last[-2:]}_{start}-{end}.txt'
                elif start == end:
                    target = f'{id_first}_{start}.txt'
                else:
                    target = f'{id_first}_{start}-{end}.txt'
                # 整组解析成功后才能更新任何 TXT 或备份；不发布缺章的聚合稿。
                try:
                    content = ''.join(build_txt_from_json(os.path.join(root, name)) for name in names)
                except (ValueError, TypeError, KeyError, OSError) as exc:
                    failures += 1
                    print(f'ERROR: {root}/{key}: {exc}')
                    continue
                if not content:
                    continue
                outputs = {target}
                if id_first == id_last and start == end:
                    alias = f'{id_first}_{start}-{end}.txt'
                    if alias in files:
                        outputs.add(alias)
                # 不再按前缀把其他 TXT 猜成“半翻译”并改名。
                # 单节 _1 与 _1-1 是等价入口，保留并同步；其他范围留待显式迁移。
                for name in sorted(outputs):
                    if write_text_atomic(os.path.join(root, name), content):
                        rebuilt += 1
                        print(f'生成阅读文本: {name} ({len(names)} 份 JSON，未判定翻译质量)')
                    else:
                        skipped += 1
    print_branch_report()
    print(f'更新 {rebuilt}，相同 {skipped}，失败组 {failures}')
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()

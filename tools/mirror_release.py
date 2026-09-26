#!/usr/bin/env python3
"""Copy only player-facing Release assets; never copy source trees or secrets.

The source-owned workflow is the sole scheduled writer. SOURCE_TOKEN is read-only
for that repository; TARGET_TOKEN exists only in Actions. No token enters output.
"""
from __future__ import annotations
import argparse
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

PACKAGES = (
    'cn_js_update.zip', 'cn_scenario_update.zip', 'cn_js_delta.zip',
    'cn_base_00_db.zip', 'cn_base_01_json.zip', 'cn_base_02.zip',
    'cn_base_03.zip', 'cn_base_04.zip', 'cn_base_05.zip', 'cn_base_06.zip',
    'cn_magica_resource.zip', 'cn_scenario_img.zip', 'cn_voice_01.zip',
    'cn_voice_02_done.zip', 'movie.zip', 'movie2.zip',
)
APK = 'magireco-latest-legacy-client.apk'
APK_META = 'magireco-latest-legacy-client.version.json'
METADATA = (
    'cn_js_update_manifest.json', 'cn_scenario_update_manifest.json',
    'cn_js_delta_manifest.json', 'manifest.json', APK_META,
    'version_js.json', 'version_scenario.json', 'version_js_delta.json',
)
REQUIRED = frozenset(PACKAGES + (APK,) + METADATA)
# These are build dependencies, not arbitrary extra assets in the source release.
OPTIONAL = frozenset(('apk-overlay-atlas.zip', 'apk-overlay-atlas-e34fdda8.zip'))
CONFIG_PATH = 'configures/personal-online-config.json'
MAX_JSON = 32 * 1024 * 1024

class Failure(RuntimeError):
    pass

class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        u = urllib.parse.urlparse(newurl)
        host = u.hostname or ''
        if u.scheme != 'https' or not (host == 'github.com' or host.endswith('.github.com')
                                      or host.endswith('.githubusercontent.com')):
            raise Failure('Rejected redirect outside HTTPS GitHub transport')
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None:
            redirected.remove_header('Authorization')
        return redirected

class API:
    def __init__(self, repo, token=''):
        if (not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo)
                or any(p in ('.', '..') for p in repo.split('/'))):
            raise Failure('Invalid repository identifier')
        self.repo, self.token = repo, token
        self.base = 'https://api.github.com/repos/' + repo + '/'
        self.opener = urllib.request.build_opener(SafeRedirect())

    def open(self, path, method='GET', data=None, extra=None, upload=False):
        url = ('https://uploads.github.com/repos/' + self.repo + '/' + path
               if upload else self.base + path)
        headers = {'Accept': 'application/vnd.github+json',
                   'User-Agent': 'ProgettoMagius-Resource-Mirror',
                   'X-GitHub-Api-Version': '2022-11-28'}
        if self.token:
            headers['Authorization'] = 'Bearer ' + self.token
        if extra:
            headers.update(extra)
        if isinstance(data, dict):
            data = json.dumps(data).encode()
            headers['Content-Type'] = 'application/json'
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        return self.opener.open(req, timeout=300)

    def json(self, path, method='GET', data=None, missing=False):
        try:
            with self.open(path, method, data) as response:
                raw = response.read(MAX_JSON + 1)
                if len(raw) > MAX_JSON:
                    raise Failure('API JSON exceeds size limit')
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            if missing and exc.code == 404:
                return None
            raise Failure('GitHub API ' + method + ' failed: HTTP ' + str(exc.code)) from None

    def download(self, asset, out):
        with self.open('releases/assets/' + str(asset['id']), extra={
                'Accept': 'application/octet-stream'}) as response, out.open('wb') as f:
            sha, md5, size = hashlib.sha256(), hashlib.md5(), 0
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > asset['size']:
                    raise Failure('Asset larger than its approved descriptor')
                f.write(chunk); sha.update(chunk); md5.update(chunk)
        if size != asset['size'] or 'sha256:' + sha.hexdigest() != asset['digest']:
            raise Failure('Asset content identity failed: ' + asset['name'])
        return {'size': size, 'sha256': sha.hexdigest(), 'md5': md5.hexdigest()}

    def upload(self, release, path):
        name = path.name
        kind = 'application/json' if name.endswith('.json') else 'application/octet-stream'
        with path.open('rb') as f, self.open(
                'releases/' + str(release['id']) + '/assets?name=' + urllib.parse.quote(name),
                method='POST', data=f, upload=True,
                extra={'Content-Type': kind, 'Content-Length': str(path.stat().st_size)}) as r:
            result = json.load(r)
        digest = digest_file(path)
        if result.get('size') != path.stat().st_size or result.get('digest') != 'sha256:' + digest:
            raise Failure('Uploaded asset identity failed: ' + name)
        return result

    def file(self, path, ref='main', missing=False):
        data = self.json('contents/' + path + '?ref=' + urllib.parse.quote(ref), missing=missing)
        if data is None:
            return None, None
        if data.get('encoding') != 'base64':
            raise Failure('Unexpected contents encoding')
        return base64.b64decode(data['content']), data['sha']


def digest_file(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def asset_map(api, release):
    out = {}
    for page in range(1, 101):
        rows = api.json('releases/' + str(release['id']) + '/assets?per_page=100&page=' + str(page))
        for item in rows:
            if item['name'] in out:
                raise Failure('Duplicate release asset name')
            out[item['name']] = item
        if len(rows) < 100:
            return out
    raise Failure('Asset pagination limit exceeded')


def select_assets(release, assets):
    if release.get('draft') or release.get('prerelease'):
        raise Failure('Source release must be published and non-prerelease')
    missing = REQUIRED - assets.keys()
    if missing:
        raise Failure('Required player assets missing: ' + ', '.join(sorted(missing)))
    chosen = {k: v for k, v in assets.items() if k in REQUIRED | OPTIONAL}
    for name, a in chosen.items():
        if a.get('state') != 'uploaded' or not isinstance(a.get('size'), int) or a['size'] <= 0:
            raise Failure('Incomplete source asset: ' + name)
        if not re.fullmatch(r'sha256:[0-9a-f]{64}', a.get('digest') or ''):
            raise Failure('Missing authoritative SHA-256: ' + name)
    return chosen


def identity(assets):
    return {n: (a['id'], a['size'], a['digest']) for n, a in assets.items()}


def publication_order(names):
    first = ['cn_js_delta.zip', APK, 'cn_scenario_update.zip', 'cn_js_update.zip']
    data = [n for n in first if n in names]
    data += sorted(n for n in names if not n.endswith('.json') and n not in data)
    # Version metadata always follows the complete data set.
    return data + [n for n in METADATA if n in names]


def check_monotonic(old, new):
    def version(value):
        text = str(value)
        if not re.fullmatch(r'[0-9]+(?:\.[0-9]+)*', text):
            raise Failure('Invalid version identifier')
        return tuple(map(int, text.split('.')))
    if version(new['version']) < version(old['version']):
        raise Failure('Refusing a public version rollback')
    if version(new['version']) == version(old['version']):
        for key in ('size', 'sha256', 'md5'):
            if key in old and key in new and str(old[key]).lower() != str(new[key]).lower():
                raise Failure('Same version has a different content identity')


def public_config(config, target):
    out = copy.deepcopy(config)
    base = 'https://github.com/' + target + '/releases/download/latest/'
    out['client']['apk_url'] = base + APK
    out.setdefault('settings', {})['offline_url'] = 'https://github.com/' + target + '/releases/tag/latest'
    for item in out.get('branch_versions', {}).values():
        if isinstance(item, dict) and 'mainline_apk_url' in item:
            item['mainline_apk_url'] = base + APK
    existing = [m for m in out.get('mirrors', []) if m.get('base') != base]
    # Preserve existing acceleration and old entries. The public mirror is an extra fallback.
    out['mirrors'] = existing + [{'name': '公开资源仓直连', 'base': base,
                                  'weight': 70, 'chunks': 4, 'enabled': True}]
    if 'ui_credits' in out:
        out['ui_credits']['github_url'] = 'https://github.com/' + target
    return out


def check_metadata(meta, assets, config):
    client, apk_meta = config['client'], meta[APK_META]
    for key in ('version', 'sha256', 'size'):
        if str(client[key]) != str(apk_meta[key]):
            raise Failure('Client gate / APK metadata mismatch: ' + key)
    if (int(client['size']) != assets[APK]['size'] or
            'sha256:' + client['sha256'] != assets[APK]['digest']):
        raise Failure('Client gate does not identify the source APK')
    for version_name, package in (
            ('version_js.json', 'cn_js_update.zip'),
            ('version_scenario.json', 'cn_scenario_update.zip'),
            ('version_js_delta.json', 'cn_js_delta.zip')):
        v = meta[version_name]
        if int(v['size']) != assets[package]['size'] or not re.fullmatch(r'[0-9a-fA-F]{32}', v['md5']):
            raise Failure('Invalid package version identity: ' + version_name)
    delta = meta['version_js_delta.json']
    if delta.get('base_js_sha256') != assets['cn_js_update.zip']['digest'][7:]:
        raise Failure('Cumulative update does not match frozen full JS')


def anonymous_verify(target, assets, config_bytes=None):
    opener = urllib.request.build_opener(SafeRedirect())
    base = 'https://github.com/' + target + '/releases/download/latest/'
    for name in sorted(assets):
        request = urllib.request.Request(base + name, headers={
            'User-Agent': 'ProgettoMagius-Anonymous-Verify', 'Range': 'bytes=0-0',
            'Accept-Encoding': 'identity'})
        with opener.open(request, timeout=120) as response:
            expected = 'bytes 0-0/' + str(assets[name]['size'])
            if response.status != 206 or response.headers.get('Content-Range') != expected:
                raise Failure('Anonymous range verification failed: ' + name)
            if len(response.read(2)) != 1:
                raise Failure('Unexpected range body: ' + name)
    if config_bytes is not None:
        u = 'https://raw.githubusercontent.com/' + target + '/main/legacy/config.json?verify=' + str(time.time_ns())
        with opener.open(u, timeout=60) as response:
            if response.read(MAX_JSON + 1) != config_bytes:
                raise Failure('Public configuration did not converge')


def mirror(source, target, work):
    release = source.json('releases/tags/latest')
    selected = select_assets(release, asset_map(source, release))
    raw_config, config_sha = source.file(CONFIG_PATH)
    config = json.loads(raw_config)
    downloaded_meta = {}
    for name in METADATA:
        p = work / name
        source.download(selected[name], p)
        downloaded_meta[name] = json.loads(p.read_text(encoding='utf-8'))
    check_metadata(downloaded_meta, selected, config)
    dest = target.json('releases/tags/latest', missing=True)
    if dest is None:
        dest = target.json('releases', 'POST', {
            'tag_name': 'latest', 'target_commitish': 'main', 'name': 'Public game resources',
            'body': 'Verified player-facing resource mirror. Source code is not distributed here.',
            'draft': True, 'prerelease': False})
    current = asset_map(target, dest)
    old_config, _ = target.file('legacy/config.json', missing=True)
    if old_config:
        check_monotonic(json.loads(old_config)['client'], config['client'])
    for name in ('version_js.json', 'version_scenario.json', 'version_js_delta.json'):
        if name in current:
            prior = work / ('prior-' + name)
            target.download(current[name], prior)
            check_monotonic(json.loads(prior.read_text()), downloaded_meta[name])
    changed, records = [], []
    backup = work / 'backup'; backup.mkdir()
    try:
        for name in publication_order(selected):
            wanted, old = selected[name], current.get(name)
            if old and (old.get('digest'), old.get('size')) == (wanted['digest'], wanted['size']):
                records.append({'name': name, 'sha256': wanted['digest'][7:], 'size': wanted['size'], 'unchanged': True})
                continue
            path = work / name
            record = source.download(wanted, path)
            # Validate MD5 as well as SHA-256 for changed hot-update packages.
            for vn, pn in (('version_js.json', 'cn_js_update.zip'), ('version_scenario.json', 'cn_scenario_update.zip'), ('version_js_delta.json', 'cn_js_delta.zip')):
                if name == pn and record['md5'] != downloaded_meta[vn]['md5'].lower():
                    raise Failure('Package MD5 does not match version metadata: ' + name)
            if old:
                target.download(old, backup / name)
            changed.append((name, old))
            if old:
                target.json('releases/assets/' + str(old['id']), 'DELETE')
            target.upload(dest, path)
            path.unlink()
            records.append(dict(name=name, **record))
            print('VERIFIED_ASSET', name, wanted['size'], flush=True)
        latest = source.json('releases/tags/latest')
        again = select_assets(latest, asset_map(source, latest))
        _, now_sha = source.file(CONFIG_PATH)
        if identity(again) != identity(selected) or now_sha != config_sha:
            raise Failure('Source changed during synchronization; rerun after publication settles')
        dest_assets = asset_map(target, dest)
        for name, wanted in selected.items():
            got = dest_assets.get(name, {})
            if (got.get('digest'), got.get('size')) != (wanted['digest'], wanted['size']):
                raise Failure('Destination identity drift: ' + name)
        if dest['draft']:
            target.json('releases/' + str(dest['id']), 'PATCH', {'draft': False, 'make_latest': 'false'})
        anonymous_verify(target.repo, selected)
        promoted = public_config(config, target.repo)
        config_bytes = (json.dumps(promoted, ensure_ascii=False, indent=2) + '\n').encode()
        report = {'schema': 1, 'status': 'assets_verified', 'source_config_blob': config_sha,
                  'asset_count': len(selected), 'client_version': config['client']['version'],
                  'assets': records, 'checked_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                  'apk_font_replacement_verified': False, 'existing_apk_private_cutover_verified': False}
        # Both public control-plane files move in one fast-forward commit. Never copy source code.
        head = target.json('git/ref/heads/main')['object']['sha']
        tree = target.json('git/commits/' + head)['tree']['sha']
        new_tree = target.json('git/trees', 'POST', {'base_tree': tree, 'tree': [
            {'path': 'legacy/config.json', 'mode': '100644', 'type': 'blob', 'content': config_bytes.decode()},
            {'path': 'migration/last-sync.json', 'mode': '100644', 'type': 'blob', 'content': json.dumps(report, ensure_ascii=False, indent=2) + '\n'}]})
        commit = target.json('git/commits', 'POST', {'message': 'chore(resources): 同步已核验的公开资源配置', 'tree': new_tree['sha'], 'parents': [head]})
        target.json('git/refs/heads/main', 'PATCH', {'sha': commit['sha'], 'force': False})
        # The commit above is the publication boundary; never roll data back after it.
        changed.clear()
        anonymous_verify(target.repo, {}, config_bytes)
        print('PUBLIC_MIRROR_READY', config['client']['version'], len(selected), flush=True)
        return report
    except Exception:
        if changed and dest.get('draft'):
            try:
                target.json('releases/' + str(dest['id']), 'PATCH', {'draft': True})
            except Exception:
                print('DRAFT_RESTORE_FAILED', flush=True)
        for name, old in reversed(changed):
            try:
                present = asset_map(target, dest).get(name)
                if present:
                    target.json('releases/assets/' + str(present['id']), 'DELETE')
                if old:
                    target.upload(dest, backup / name)
            except Exception:
                print('ROLLBACK_FAILED', name, flush=True)
        raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', required=True)
    p.add_argument('--target', required=True)
    p.add_argument('--plan', action='store_true')
    args = p.parse_args()
    if args.source == args.target:
        raise Failure('Source and target must differ')
    source = API(args.source, os.environ.get('SOURCE_TOKEN', ''))
    target = API(args.target, os.environ.get('TARGET_TOKEN', ''))
    if args.plan:
        release = source.json('releases/tags/latest')
        chosen = select_assets(release, asset_map(source, release))
        print(json.dumps({'assets': publication_order(chosen), 'bytes': sum(a['size'] for a in chosen.values())}, indent=2))
        return
    if not source.token or not target.token:
        raise Failure('Source read token and target write token must be configured in Actions')
    with tempfile.TemporaryDirectory(prefix='resource-mirror-') as tmp:
        report = mirror(source, target, Path(tmp))
    Path('mirror-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')

if __name__ == '__main__':
    try:
        main()
    except Failure as e:
        raise SystemExit(str(e))
    except Exception as e:
        # Do not print signed redirect URLs or authentication-bearing exception context.
        raise SystemExit('Mirror failed (' + type(e).__name__ + '); check publication report before changing repository visibility')

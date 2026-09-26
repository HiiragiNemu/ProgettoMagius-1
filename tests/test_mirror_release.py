import copy
import importlib.util
from pathlib import Path
import unittest
import urllib.request

spec = importlib.util.spec_from_file_location('mirror', Path(__file__).parents[1] / 'tools/mirror_release.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

def assets():
    return {name: {'name': name, 'id': n+1, 'size': 12, 'state': 'uploaded', 'digest': 'sha256:'+'a'*64}
            for n, name in enumerate(sorted(m.REQUIRED))}

def config():
    return {'client': {'version': '1.0.193', 'sha256': 'a'*64, 'size': 12, 'apk_url': 'https://old.example/client.apk'},
            'mirrors': [{'name': 'CDN', 'base': 'https://cdn.example/', 'weight': 140, 'enabled': True}],
            'settings': {'chunks': 4}, 'branch_versions': {'retired': {'supported': False, 'mainline_apk_url': 'https://old.example/client.apk'}},
            'ui_credits': {'list': [{'text': '原有署名'}], 'github_url': 'https://old.example/'}}

class Policy(unittest.TestCase):
    def test_player_list_matches_sixteen_packages(self):
        self.assertEqual(len(m.PACKAGES), 16)
        self.assertEqual(len(m.REQUIRED), 25)
    def test_only_allowlisted_files(self):
        a = assets(); a['private-audit.zip'] = {'name': 'private-audit.zip'}
        self.assertEqual(set(m.select_assets({}, a)), m.REQUIRED)
    def test_draft_and_prerelease_rejected(self):
        for flag in ('draft', 'prerelease'):
            with self.assertRaises(m.Failure): m.select_assets({flag: True}, assets())
    def test_missing_player_file_rejected(self):
        a = assets(); del a['cn_js_delta.zip']
        with self.assertRaises(m.Failure): m.select_assets({}, a)
    def test_missing_hash_rejected(self):
        a = assets(); a[m.APK]['digest'] = None
        with self.assertRaises(m.Failure): m.select_assets({}, a)
    def test_incomplete_asset_rejected(self):
        a = assets(); a[m.APK]['state'] = 'starter'
        with self.assertRaises(m.Failure): m.select_assets({}, a)
    def test_payload_before_versions_and_priority(self):
        order = m.publication_order(m.REQUIRED)
        self.assertEqual(order[:2], ['cn_js_delta.zip', m.APK])
        self.assertEqual(set(order), m.REQUIRED)
        self.assertLess(max(i for i,n in enumerate(order) if not n.endswith('.json')),
                        min(i for i,n in enumerate(order) if n.endswith('.json')))
    def test_config_does_not_change_identity_or_mutate_input(self):
        old = config(); before = copy.deepcopy(old)
        new = m.public_config(old, 'Example/Public')
        self.assertEqual(old, before)
        for key in ('version', 'size', 'sha256'): self.assertEqual(old['client'][key], new['client'][key])
        self.assertEqual(new['settings']['chunks'], 4)
        self.assertEqual(new['mirrors'][0], old['mirrors'][0])
        self.assertEqual(new['ui_credits']['list'], old['ui_credits']['list'])
        self.assertFalse(new['branch_versions']['retired']['supported'])
        self.assertTrue(new['client']['apk_url'].startswith('https://github.com/Example/Public/'))
    def test_config_is_idempotent(self):
        once = m.public_config(config(), 'Example/Public')
        self.assertEqual(once, m.public_config(once, 'Example/Public'))
    def test_downgrade_rejected(self):
        with self.assertRaises(m.Failure): m.check_monotonic({'version':'1.0.194'}, {'version':'1.0.193'})
    def test_same_version_different_bytes_rejected(self):
        with self.assertRaises(m.Failure): m.check_monotonic({'version':1,'md5':'a'}, {'version':1,'md5':'b'})
    def test_numeric_versions(self):
        m.check_monotonic({'version':'1.0.99'}, {'version':'1.0.100'})
    def test_unsafe_repository_rejected(self):
        for repo in ('../private', 'owner/name?token=secret', 'owner/name/extra'):
            with self.assertRaises(m.Failure): m.API(repo)
    def test_redirect_drops_bearer(self):
        r = urllib.request.Request('https://api.github.com/a', headers={'Authorization':'Bearer secret'})
        redirected = m.SafeRedirect().redirect_request(r, None, 302, '', {}, 'https://release-assets.githubusercontent.com/x')
        self.assertIsNone(redirected.get_header('Authorization'))
    def test_redirect_rejects_http_or_external_host(self):
        r = urllib.request.Request('https://api.github.com/a')
        for url in ('http://github.com/a', 'https://github.com.evil.example/a', 'https://evil.example/a'):
            with self.assertRaises(m.Failure): m.SafeRedirect().redirect_request(r, None, 302, '', {}, url)
    def test_pagination(self):
        class Fake:
            def json(self, path):
                return [{'name':str(n)} for n in range(100)] if path.endswith('page=1') else [{'name':'last'}]
        self.assertEqual(len(m.asset_map(Fake(), {'id': 1})), 101)
    def test_metadata_agrees_with_release(self):
        meta = {m.APK_META: {'version':'1.0.193', 'size':12, 'sha256':'a'*64}}
        for name in ('version_js.json','version_scenario.json','version_js_delta.json'):
            meta[name]={'version':1,'size':12,'md5':'b'*32}
        meta['version_js_delta.json']['base_js_sha256']='a'*64
        m.check_metadata(meta, assets(), config())
        meta[m.APK_META]['sha256']='c'*64
        with self.assertRaises(m.Failure): m.check_metadata(meta, assets(), config())

if __name__ == '__main__': unittest.main()

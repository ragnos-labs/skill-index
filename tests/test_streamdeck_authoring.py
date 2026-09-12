"""Isolated behavioral tests; no real profiles, credentials, or devices."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/streamdeck-authoring/scripts'
def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module
sd = load('streamdeck'); runner = load('command_runner')


class DeckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.target = self.root / '12345678-1234-5678-1234-567812345678.sdProfile'
        self.page = '12345678-1234-5678-1234-567812345679'
        self.ws = self.root / 'workspace'; self.plugins = self.root / 'plugins'; self.plugins.mkdir()
        a = sd.generic(sd.OPEN, 'Open', {'path': str(self.root), 'unknown': 12})
        a['ActionID'] = '12345678-1234-5678-1234-567812345680'
        a['vendorUnknown'] = {'retain': True}
        sd.write(self.target / 'manifest.json', {'Name': 'Fixture', 'Version': '3.0', 'Device': {'Model': sd.MODEL, 'UUID': 'local-test'}, 'Pages': {'Current': self.page, 'Default': self.page, 'Pages': [self.page]}, 'UnknownRoot': True})
        sd.write(self.target / 'Profiles' / self.page / 'manifest.json', {'Name': 'One', 'Icon': '', 'UnknownPage': 123, 'Controllers': [{'Type': 'Keypad', 'Actions': {'0,0': a}}, {'Type': 'Encoder', 'Actions': {}}]})
        sd.adopt(self.target, self.ws)
        self.recipe = sd.read(self.ws / 'recipe.json'); self.catalog = sd.read(self.ws / 'catalog.json')
        self.cid = self.recipe['pages'][0]['controls'][0]['id']
        self.candidate = self.root / 'candidate'; self.planpath = self.root / 'plan'

    def tearDown(self): self.tmp.cleanup()
    def save(self):
        sd.write(self.ws / 'recipe.json', self.recipe); sd.write(self.ws / 'catalog.json', self.catalog)
    def change(self): self.recipe['pages'][0]['controls'][0]['title'] = 'Changed'; self.save()
    def prepare(self):
        sd.build(self.ws, self.candidate)
        return sd.plan(self.ws, self.candidate, self.plugins, self.planpath)
    def installed(self):
        self.prepare()
        with patch.object(sd, 'ensure_closed'): return sd.apply(self.planpath)
    def current_page(self): return sd.read(self.target / 'Profiles' / self.page / 'manifest.json')
    def put_page(self, page): sd.write(self.target / 'Profiles' / self.page / 'manifest.json', page)

    def test_capture_does_not_change_profile(self):
        self.assertEqual(sd.tree_hash(self.target), sd.tree_hash(self.ws / 'adoption-backup'))

    def test_build_is_deterministic_and_has_no_workspace_writes(self):
        original, before = sd.tree_hash(self.target), sd.tree_hash(self.ws)
        sd.build(self.ws, self.candidate); second = self.root / 'second'; sd.build(self.ws, second)
        self.assertEqual(sd.tree_hash(self.candidate), sd.tree_hash(second))
        self.assertEqual(before, sd.tree_hash(self.ws)); self.assertEqual(original, sd.tree_hash(self.target))

    def test_apply_and_exact_rollback(self):
        original = sd.tree_hash(self.target); base = (self.ws / 'baseline.json').read_bytes()
        self.change(); receipt = self.installed()['receipt']
        self.assertNotEqual(original, sd.tree_hash(self.target))
        self.assertEqual(sd.read(self.target / 'manifest.json')['UnknownRoot'], True)
        self.assertEqual(self.current_page()['UnknownPage'], 123)
        self.assertTrue(sd.actions(self.current_page(), 'Keypad')['0,0']['vendorUnknown']['retain'])
        with patch.object(sd, 'ensure_closed'): sd.rollback(receipt)
        self.assertEqual(original, sd.tree_hash(self.target)); self.assertEqual(base, (self.ws / 'baseline.json').read_bytes())

    def test_manual_edit_preserved_without_requested_change(self):
        page = self.current_page(); sd.actions(page, 'Keypad')['0,0']['States'][0]['Title'] = 'Manual'; self.put_page(page)
        self.prepare()
        page = sd.read(self.planpath / 'profile' / 'Profiles' / self.page / 'manifest.json')
        self.assertEqual(sd.actions(page, 'Keypad')['0,0']['States'][0]['Title'], 'Manual')

    def test_conflicting_manual_edit_stops(self):
        page = self.current_page(); sd.actions(page, 'Keypad')['0,0']['Settings']['unknown'] = 99; self.put_page(page)
        self.change()
        with self.assertRaisesRegex(sd.Error, 'manually edited'): self.prepare()

    def test_manual_move_stops_overlapping_change(self):
        page = self.current_page(); a = sd.actions(page, 'Keypad'); a['1,0'] = a.pop('0,0'); self.put_page(page)
        self.change()
        with self.assertRaisesRegex(sd.Error, 'moved'): self.prepare()

    def test_manual_deletion_stops_overlapping_change(self):
        page = self.current_page(); sd.actions(page, 'Keypad').clear(); self.put_page(page); self.change()
        with self.assertRaisesRegex(sd.Error, 'removed'): self.prepare()

    def test_transient_state_is_ignored(self):
        page = self.current_page(); sd.actions(page, 'Keypad')['0,0']['State'] = 1; self.put_page(page)
        self.change(); self.prepare()

    def test_destination_occupied_stops(self):
        page = self.current_page(); sd.actions(page, 'Keypad')['1,0'] = sd.generic(sd.OPEN, 'Manual', {}); self.put_page(page)
        self.recipe['pages'][0]['controls'][0]['position'] = '1,0'; self.save()
        with self.assertRaisesRegex(sd.Error, 'occupied'): self.prepare()

    def test_new_page_and_dial(self):
        self.catalog['actions']['dial'] = {'controllers': ['Encoder'], 'action': sd.generic('example.brightness', 'Dim', {'device': 'private'})}
        self.recipe['pages'].append({'id': 'second', 'name': 'Two', 'controls': [{'id': 'dial', 'controller': 'Encoder', 'position': '0,0', 'action': 'dial'}]}); self.save()
        self.assertEqual(len(sd.compile_profile(self.ws)['managed']['pages']), 2)

    def test_missing_plugin(self):
        self.catalog['actions'][self.cid]['action']['Plugin']['UUID'] = 'example.light'; self.save()
        with self.assertRaisesRegex(sd.Error, 'Missing plugins'): self.prepare()

    def test_unsupported_controller(self):
        self.recipe['pages'][0]['controls'][0]['controller'] = 'Encoder'; self.save()
        with self.assertRaisesRegex(sd.Error, 'support controller'): sd.compile_profile(self.ws)

    def test_duplicate_position(self):
        a = copy.deepcopy(self.recipe['pages'][0]['controls'][0]); a['id'] = 'duplicate'; self.recipe['pages'][0]['controls'].append(a); self.save()
        with self.assertRaisesRegex(sd.Error, 'occupied'): sd.compile_profile(self.ws)

    def test_missing_resource_and_traversal(self):
        self.recipe['pages'][0]['controls'][0]['icon'] = '../outside.svg'; self.save()
        with self.assertRaisesRegex(sd.Error, 'relative'): sd.compile_profile(self.ws)
        self.recipe['pages'][0]['controls'][0]['icon'] = 'absent.svg'; self.save()
        with self.assertRaisesRegex(sd.Error, 'Missing resource'): sd.compile_profile(self.ws)

    def test_symlink_resource(self):
        (self.ws / 'icon.svg').symlink_to(self.ws / 'recipe.json'); self.recipe['pages'][0]['controls'][0]['icon'] = 'icon.svg'; self.save()
        with self.assertRaisesRegex(sd.Error, 'Symlink'): sd.compile_profile(self.ws)

    def test_bad_version_and_model(self):
        self.recipe['version'] = 99; self.save()
        with self.assertRaises(sd.Error): sd.compile_profile(self.ws)
        self.recipe['version'] = 1; self.catalog['device']['Model'] = 'unknown'; self.save()
        with self.assertRaisesRegex(sd.Error, 'model'): sd.compile_profile(self.ws)

    def test_stale_profile_rejected_without_profile_write(self):
        self.change(); self.prepare(); page = self.current_page(); page['Manual'] = True; self.put_page(page)
        before = sd.tree_hash(self.target)
        with patch.object(sd, 'ensure_closed'), self.assertRaisesRegex(sd.Error, 'Stale plan'): sd.apply(self.planpath)
        self.assertEqual(before, sd.tree_hash(self.target))

    def test_stale_catalog_rejected(self):
        self.change(); self.prepare(); self.catalog['extra'] = True; self.save()
        with patch.object(sd, 'ensure_closed'), self.assertRaisesRegex(sd.Error, 'catalog changed'): sd.apply(self.planpath)

    def test_stale_resource_rejected(self):
        (self.ws / 'icon.svg').write_text('<svg/>'); self.recipe['pages'][0]['controls'][0]['icon'] = 'icon.svg'; self.save(); self.prepare()
        (self.ws / 'icon.svg').write_text('<svg>changed</svg>')
        with patch.object(sd, 'ensure_closed'), self.assertRaisesRegex(sd.Error, 'resource changed'): sd.apply(self.planpath)

    def test_lock_contention(self):
        self.change(); self.prepare()
        with sd.locked(self.ws), patch.object(sd, 'ensure_closed'), self.assertRaisesRegex(sd.Error, 'lock'): sd.apply(self.planpath)

    def test_process_guard(self):
        fake = subprocess.CompletedProcess([], 0, '/Applications/Elgato Stream Deck.app/Contents/MacOS/Stream Deck\n', '')
        with patch.object(sd.subprocess, 'run', return_value=fake), self.assertRaisesRegex(sd.Error, 'Close Stream Deck'): sd.ensure_closed()

    def test_rollback_refuses_later_manual_edit(self):
        self.change(); receipt = self.installed()['receipt']; page = self.current_page(); page['Manual'] = 3; self.put_page(page)
        with patch.object(sd, 'ensure_closed'), self.assertRaisesRegex(sd.Error, 'changed after'): sd.rollback(receipt)

    def test_interrupted_replace_recovers(self):
        self.change(); self.prepare(); original = sd.tree_hash(self.target); rename = Path.rename
        def crash(path, destination):
            if '.stage-' in path.name: raise OSError('simulated interruption')
            return rename(path, destination)
        with patch.object(sd, 'ensure_closed'), patch.object(Path, 'rename', crash), self.assertRaises(OSError): sd.apply(self.planpath)
        self.assertFalse(self.target.exists())
        with patch.object(sd, 'ensure_closed'): sd.rollback(self.ws / 'pending.json')
        self.assertEqual(original, sd.tree_hash(self.target))

    def test_macro_structure_delay_and_order(self):
        self.catalog['actions']['macro'] = {'kind': 'multi', 'steps': [{'action': self.cid}, {'delay_ms': 200}, {'action': self.cid}]}
        self.recipe['pages'][0]['controls'][0]['action'] = 'macro'; self.save()
        action = next(iter(sd.compile_profile(self.ws)['managed']['controls'].values()))['action']
        self.assertEqual(action['Plugin']['UUID'], 'com.elgato.streamdeck.multiactions')
        self.assertEqual([a['UUID'] for a in action['Actions'][0]['Actions']], [sd.OPEN, sd.DELAY, sd.OPEN])
        self.assertEqual(action['Actions'][0]['Actions'][1]['Settings']['Delay'], 200)

    def test_nested_macro_rejected(self):
        self.catalog['actions']['macro'] = {'kind': 'multi', 'steps': [{'action': 'macro'}]}
        self.recipe['pages'][0]['controls'][0]['action'] = 'macro'; self.save()
        with self.assertRaisesRegex(sd.Error, 'Nested'): sd.compile_profile(self.ws)

    def test_command_metacharacters_pass_as_literal_arguments(self):
        text = '$(touch nope); `echo hi` "quoted"'
        self.catalog['actions'][self.cid] = {'kind': 'command', 'argv': [str(Path(sys.executable).resolve()), '-c', 'import sys; print(sys.argv[1])', text], 'cwd': str(self.root), 'timeout': 5}
        self.save(); receipt = self.installed()['receipt']
        info = sd.read(receipt); launcher = next(Path(info['runtime_target']).glob('commands/*.command'))
        result = subprocess.run([str(launcher)], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0); self.assertIn(text, result.stdout); self.assertFalse((self.root / 'nope').exists())

    def test_invalid_command_timeout(self):
        self.catalog['actions'][self.cid] = {'kind': 'command', 'argv': [str(Path(sys.executable).resolve())], 'cwd': str(self.root), 'timeout': 0}; self.save()
        with self.assertRaisesRegex(sd.Error, 'timeout'): sd.compile_profile(self.ws)

    def test_build_refuses_existing_directory(self):
        self.candidate.mkdir(); (self.candidate / 'keep').write_text('keep')
        with self.assertRaises(sd.Error): sd.build(self.ws, self.candidate)
        self.assertEqual((self.candidate / 'keep').read_text(), 'keep')

    def test_navigation(self):
        self.catalog['actions'][self.cid] = {'kind': 'navigation', 'direction': 'next'}; self.save()
        a = next(iter(sd.compile_profile(self.ws)['managed']['controls'].values()))['action']
        self.assertEqual(a['UUID'], 'com.elgato.streamdeck.page.next')

    def test_noop_preserves_exact_profile(self):
        before = sd.tree_hash(self.target); self.prepare()
        with patch.object(sd, 'ensure_closed'): result = sd.apply(self.planpath)
        self.assertEqual(result['status'], 'unchanged')
        self.assertEqual(before, sd.tree_hash(self.target))

    def test_build_and_plan_reject_live_output(self):
        before = sd.tree_hash(self.target)
        with self.assertRaisesRegex(sd.Error, 'protected'): sd.build(self.ws, self.target / 'bad')
        sd.build(self.ws, self.candidate)
        with self.assertRaisesRegex(sd.Error, 'protected'): sd.plan(self.ws, self.candidate, self.plugins, self.target / 'bad')
        with self.assertRaisesRegex(sd.Error, 'protected'): sd.build(self.ws, self.ws / 'bad')
        self.assertEqual(before, sd.tree_hash(self.target))

    def test_rollback_without_candidate(self):
        import shutil
        before = sd.tree_hash(self.target); self.change(); receipt = self.installed()['receipt']
        shutil.rmtree(self.candidate)
        with patch.object(sd, 'ensure_closed'): sd.rollback(receipt)
        self.assertEqual(before, sd.tree_hash(self.target))

    def test_wrong_pending_transaction_rejected_before_rollback(self):
        self.change(); receipt = self.installed()['receipt']; before = sd.tree_hash(self.target)
        sd.write(self.ws / 'pending.json', {'transaction': 'different'})
        with patch.object(sd, 'ensure_closed'), self.assertRaisesRegex(sd.Error, 'Different pending'): sd.rollback(receipt)
        self.assertEqual(before, sd.tree_hash(self.target))

    def test_interrupted_rollback_recovers(self):
        before = sd.tree_hash(self.target); self.change(); receipt = self.installed()['receipt']; rename = Path.rename
        def crash(path, destination):
            if '.restore-' in path.name: raise OSError('simulated rollback interruption')
            return rename(path, destination)
        with patch.object(sd, 'ensure_closed'), patch.object(Path, 'rename', crash), self.assertRaises(OSError): sd.rollback(receipt)
        self.assertFalse(self.target.exists())
        with patch.object(sd, 'ensure_closed'): sd.rollback(receipt)
        self.assertEqual(before, sd.tree_hash(self.target))

    def test_transaction_symlink_has_no_external_writes(self):
        external = self.root / 'external'; external.mkdir(); (self.ws / 'transactions').symlink_to(external)
        self.change(); self.prepare()
        with patch.object(sd, 'ensure_closed'), self.assertRaisesRegex(sd.Error, 'Symlink'): sd.apply(self.planpath)
        self.assertEqual(list(external.iterdir()), [])

    def test_managed_controls_can_swap(self):
        second = copy.deepcopy(self.recipe['pages'][0]['controls'][0]); second.update(id='second', position='1,0')
        self.recipe['pages'][0]['controls'].append(second); self.save(); self.installed()
        self.recipe['pages'][0]['controls'][0]['position'] = '1,0'; self.recipe['pages'][0]['controls'][1]['position'] = '0,0'; self.save()
        self.candidate = self.root / 'candidate2'; self.planpath = self.root / 'plan2'; self.prepare()
        page = sd.read(self.planpath / 'profile' / 'Profiles' / self.page / 'manifest.json')
        self.assertEqual(sd.actions(page, 'Keypad')['1,0']['ActionID'], '12345678-1234-5678-1234-567812345680')

    def test_nested_captured_macro_is_rejected(self):
        outer = sd.generic(sd.MULTI, 'Multi', {}); outer['Actions'] = [{'Actions': [sd.generic(sd.MULTI, 'Multi', {})]}]
        self.catalog['actions'][self.cid]['action'] = outer; self.save()
        with self.assertRaisesRegex(sd.Error, 'Nested'): sd.compile_profile(self.ws)

    def test_missing_command_file_placeholder(self):
        self.catalog['actions'][self.cid] = {'kind': 'command', 'argv': [str(Path(sys.executable).resolve()), '{runtime}/absent.py'], 'cwd': str(self.root), 'timeout': 10}; self.save()
        with self.assertRaisesRegex(sd.Error, 'Unbound'): sd.compile_profile(self.ws)


class RunnerTests(unittest.TestCase):
    def test_timeout(self):
        def execute(*a, **kw): raise subprocess.TimeoutExpired('fixture', 1)
        self.assertEqual(runner.run({'title': 'fixture', 'argv': ['/bin/echo'], 'cwd': '/', 'timeout': 1}, execute), 124)
    def test_malformed_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / 'bad.json'; f.write_text('not json')
            self.assertEqual(runner.main(f), 2)

    def test_diagnostic_probe_failed_or_malformed(self):
        for code, output in [(1, '{}'), (0, '[]'), (0, 'not-json'), (0, '{"SPDisplaysDataType": {}}'), (0, '{"SPDisplaysDataType": [4]}')]:
            result = subprocess.CompletedProcess([], code, output, '')
            self.assertEqual(runner.display_state(result, 'fixture'), 'unavailable')

    def test_diagnostic_probe_online_and_absent(self):
        payload = {'SPDisplaysDataType': [{'spdisplays_ndrvs': [{'_name': 'fixture', 'spdisplays_online': 'spdisplays_yes'}]}]}
        self.assertEqual(runner.display_state(subprocess.CompletedProcess([], 0, json.dumps(payload), ''), 'fixture'), 'online')
        self.assertEqual(runner.display_state(subprocess.CompletedProcess([], 0, '{"SPDisplaysDataType": []}', ''), 'fixture'), 'not active')


if __name__ == '__main__': unittest.main()

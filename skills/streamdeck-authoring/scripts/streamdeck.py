#!/usr/bin/env python3
"""Local Stream Deck + profile authoring. Python standard library, no network."""
from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
import zipfile
from contextlib import contextmanager

VERSION = 1
MODEL = '20GBD9901'
OPEN = 'com.elgato.streamdeck.system.open'
MULTI = 'com.elgato.streamdeck.multiactions.routine'
DELAY = 'com.elgato.streamdeck.multiactions.delay'
NAME = re.compile(r'^[a-z0-9][a-z0-9-]{0,63}$')


class Error(Exception):
    pass


def require(condition, message):
    if not condition:
        raise Error(message)


def encoded(data):
    return (json.dumps(data, sort_keys=True, indent=2, ensure_ascii=True) + '\n').encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError) as exc:
        raise Error('Cannot read JSON: ' + str(path)) from exc


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded(data))


def absolute(path):
    p = Path(path).expanduser()
    require(p.is_absolute(), 'Use an absolute path: ' + str(path))
    require(not any(part == '..' for part in p.parts), 'Parent traversal is not allowed')
    for node in [p, *p.parents]:
        require(not node.is_symlink(), 'Symlink path is not allowed: ' + str(node))
    return p


def child(root, relative):
    p = Path(relative)
    require(not p.is_absolute() and p.parts and all(x not in ('.', '..') for x in p.parts),
            'Invalid relative resource path')
    return absolute(Path(root) / p)


def tree(path):
    path = absolute(path)
    require(path.is_dir(), 'Missing directory: ' + str(path))
    result = {}
    for p in sorted(path.rglob('*')):
        require(not p.is_symlink(), 'Symlink in resource tree')
        if p.is_file():
            result[p.relative_to(path).as_posix()] = {'sha256': digest(p.read_bytes()),
                                                    'mode': p.stat().st_mode & 0o777}
        else:
            require(p.is_dir(), 'Unsupported special file')
    return result


def tree_hash(path):
    return digest(encoded(tree(path)))


def atomic_json(path, data):
    path = absolute(path)
    tmp = path.with_name(path.name + '.tmp-' + uuid.uuid4().hex)
    try:
        with tmp.open('xb') as f:
            f.write(encoded(data)); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def stable(profile_id, kind, name):
    return str(uuid.uuid5(uuid.UUID(profile_id), kind + ':' + name))


def authored(action):
    """Ignore only Stream Deck's observed selected state, including macro children."""
    if isinstance(action, list):
        return [authored(x) for x in action]
    if not isinstance(action, dict):
        return action
    return {k: authored(v) for k, v in action.items()
            if not (k == 'State' and 'UUID' in action)}


def actions(page, kind):
    found = [c for c in page.get('Controllers', []) if c.get('Type') == kind]
    require(len(found) <= 1, 'Duplicate controller')
    if not found:
        page.setdefault('Controllers', []).append({'Type': kind, 'Actions': {}})
        found = [page['Controllers'][-1]]
    if found[0].get('Actions') is None:
        found[0]['Actions'] = {}
    return found[0]['Actions']


def profile(path):
    root = read(Path(path) / 'manifest.json')
    require(root.get('Version') == '3.0', 'Unsupported profile format')
    require(root.get('Device', {}).get('Model') == MODEL, 'Only Stream Deck + is supported in v1')
    ids = root.get('Pages', {}).get('Pages', [])
    require(isinstance(ids, list) and ids and len(ids) == len(set(ids)), 'Invalid page list')
    pages = {}
    for page_id in ids:
        uuid.UUID(page_id)
        pages[page_id] = read(child(path, 'Profiles/' + page_id + '/manifest.json'))
    return root, pages


def inventory(path):
    root, pages = profile(path)
    return {'profile': root['Name'], 'model': MODEL,
            'pages': [{'id': k, 'name': p.get('Name', ''),
                       'controllers': {c['Type']: len(c.get('Actions') or {})
                                       for c in p.get('Controllers', [])}}
                      for k, p in pages.items()], 'digest': tree_hash(path)}


def normalize_ids(action, prefix):
    if isinstance(action, dict):
        if 'ActionID' in action:
            action['ActionID'] = str(uuid.uuid5(uuid.UUID(prefix), 'action'))
        for k, value in action.items():
            if isinstance(value, (list, dict)):
                normalize_ids(value, str(uuid.uuid5(uuid.UUID(prefix), k)))
    elif isinstance(action, list):
        for i, value in enumerate(action):
            normalize_ids(value, str(uuid.uuid5(uuid.UUID(prefix), str(i))))


def validate_native(value, inside_multi=False):
    if isinstance(value, dict):
        is_multi = value.get('UUID') == MULTI
        require(not (inside_multi and is_multi), 'Nested Multi Actions are unsupported')
        for key, v in value.items():
            if key != 'Plugin': validate_native(v, inside_multi or is_multi)
    elif isinstance(value, list):
        for v in value: validate_native(v, inside_multi)


def image_references(value):
    if isinstance(value, dict):
        for k, v in value.items():
            if k in ('Image', 'background') and isinstance(v, str) and v.startswith('Images/'):
                yield v
            yield from image_references(v)
    elif isinstance(value, list):
        for v in value:
            yield from image_references(v)


def adopt(target, workspace):
    """Capture a private baseline; does not change the installed profile."""
    target, workspace = absolute(target), absolute(workspace)
    require(not workspace.exists(), 'Adoption requires a new workspace')
    before = tree_hash(target)
    root, pages = profile(target)
    pid = str(uuid.UUID(target.name.removesuffix('.sdProfile')))
    recipe = {'version': VERSION, 'profile_id': pid, 'name': root['Name'],
              'pages': []}
    catalog = {'version': VERSION, 'device': root['Device'], 'actions': {}}
    managed = {'pages': {}, 'controls': {}}
    resources = {}
    for n, (page_uuid, page) in enumerate(pages.items()):
        page_id = 'page-' + str(n + 1)
        recipe_page = {'id': page_id, 'name': page.get('Name', ''), 'controls': []}
        recipe['pages'].append(recipe_page)
        managed['pages'][page_id] = {'uuid': page_uuid, 'name': page.get('Name', '')}
        for c in page.get('Controllers', []):
            for pos, action in (c.get('Actions') or {}).items():
                require(c['Type'] in ('Keypad', 'Encoder'), 'Unsupported populated controller')
                cid = page_id + '-' + c['Type'].lower() + '-' + pos.replace(',', '-')
                catalog['actions'][cid] = {'controllers': [c['Type']], 'action': action,
                                           'resources': {}}
                for image in image_references(action):
                    src = child(target, 'Profiles/' + page_uuid + '/' + image)
                    require(src.is_file(), 'Missing native resource')
                    rel = 'assets/' + page_id + '/' + image
                    resources[rel] = src
                    catalog['actions'][cid]['resources'][image] = rel
                recipe_page['controls'].append({'id': cid, 'position': pos,
                                               'controller': c['Type'], 'action': cid})
                managed['controls'][cid] = {'page': page_uuid, 'controller': c['Type'],
                                            'position': pos, 'action': action}
    require(tree_hash(target) == before, 'Profile changed during capture')
    workspace.mkdir(parents=True, mode=0o700)
    try:
        for rel, src in resources.items():
            dest = child(workspace, rel); dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
        write(workspace / 'recipe.json', recipe)
        write(workspace / 'catalog.json', catalog)
        write(workspace / 'baseline.json', {'version': VERSION, 'target': str(target),
                                          'profile_id': pid, 'managed': managed,
                                          'runtime': None})
        shutil.copytree(target, workspace / 'adoption-backup')
        require(tree_hash(workspace / 'adoption-backup') == before, 'Capture backup mismatch')
        return {'status': 'adopted', 'workspace': str(workspace), 'profile_changed': False}
    except BaseException:
        shutil.rmtree(workspace)
        raise


def validate_command(spec):
    require(isinstance(spec.get('argv'), list) and spec['argv'] and
            all(isinstance(x, str) and '\0' not in x for x in spec['argv']), 'Invalid command argv')
    exe = absolute(spec['argv'][0])
    require(exe.is_file() and os.access(exe, os.X_OK), 'Command executable missing')
    require(absolute(spec['cwd']).is_dir(), 'Command working directory missing')
    require(type(spec.get('timeout')) in (int, float) and 0 < spec['timeout'] <= 3600,
            'Command timeout must be between 0 and 3600 seconds')


def load_inputs(workspace):
    workspace = absolute(workspace)
    recipe, catalog = read(workspace / 'recipe.json'), read(workspace / 'catalog.json')
    require(recipe.get('version') == VERSION and catalog.get('version') == VERSION,
            'Unsupported recipe/catalog version')
    require(catalog.get('device', {}).get('Model') == MODEL, 'Unsupported device model')
    uuid.UUID(recipe['profile_id'])
    require(isinstance(recipe.get('name'), str) and recipe['name'], 'Missing profile name')
    require(isinstance(recipe.get('pages'), list) and recipe['pages'], 'At least one page required')
    require(isinstance(catalog.get('actions'), dict), 'Invalid action catalog')
    return workspace, recipe, catalog


def compile_profile(workspace):
    workspace, recipe, catalog = load_inputs(workspace)
    baseline = read(workspace / 'baseline.json') if (workspace / 'baseline.json').exists() else None
    require(not baseline or baseline['profile_id'] == recipe['profile_id'], 'Profile identity changed')
    old = baseline['managed'] if baseline else {'pages': {}, 'controls': {}}
    payload = {}; managed = {'pages': {}, 'controls': {}}; manifests = {}; dependencies = {}
    runtime = {}; profile_id = recipe['profile_id']; page_ids = {}; control_ids = set()
    namespace = str(uuid.UUID(profile_id))
    for p in recipe['pages']:
        require(isinstance(p, dict) and isinstance(p.get('id'), str) and NAME.fullmatch(p['id']), 'Invalid page ID')
        require(p['id'] not in page_ids, 'Duplicate page ID')
        page_ids[p['id']] = old['pages'].get(p['id'], {}).get('uuid', stable(namespace, 'page', p['id']))

    def resource(rel):
        p = child(workspace, rel)
        require(p.is_file(), 'Missing resource: ' + rel)
        dependencies[str(p)] = {'sha256': digest(p.read_bytes()), 'mode': p.stat().st_mode & 0o777}
        return p.read_bytes()

    def make_action(ref, controller, aid, page_uuid, nested=False):
        require(ref in catalog['actions'], 'Unknown action reference: ' + str(ref))
        spec = catalog['actions'][ref]
        kind = spec.get('kind', 'native')
        require(controller in spec.get('controllers', ['Keypad']), 'Action does not support controller')
        if kind == 'native':
            result = copy.deepcopy(spec['action'])
            validate_native(result, nested)
            require(isinstance(result.get('UUID'), str), 'Native action UUID missing')
            require(not nested or result['UUID'] != MULTI, 'Nested Multi Actions are unsupported')
            for rel in image_references(result):
                require(rel in spec.get('resources', {}), 'Native resource mapping missing: ' + rel)
                key = 'Profiles/' + page_uuid + '/' + rel
                data = resource(spec['resources'][rel])
                require(key not in payload or payload[key] == data, 'Resource filename collision')
                payload[key] = data
            normalize_ids(result, aid)
        elif kind == 'open':
            target = absolute(spec['path']); require(target.exists(), 'Open target missing')
            result = generic(OPEN, 'Open', {'path': str(target), 'openInBackground': False})
        elif kind == 'command':
            validate_command(spec)
            executable = absolute(spec['argv'][0])
            dependencies[str(executable)] = {'sha256': digest(executable.read_bytes()), 'mode': executable.stat().st_mode & 0o777}
            config = {k: copy.deepcopy(spec[k]) for k in ('argv', 'cwd', 'timeout')}
            config['title'] = spec.get('title', ref)
            files = spec.get('files', [])
            require(isinstance(files, list) and len(files) == len(set(files)), 'Invalid command files')
            for arg in config['argv']:
                if '{runtime}' in arg:
                    require(arg.startswith('{runtime}/') and arg[len('{runtime}/'):] in files, 'Unbound runtime argument')
            for relative in files:
                require(relative.startswith('assets/'), 'Command files must be under assets/')
                require('{runtime}/' + relative in config['argv'], 'Command file must have an argv placeholder')
                data = resource(relative)
                runtime[relative] = data
            runtime['commands/' + aid + '.json'] = encoded(config)
            result = generic(OPEN, 'Open', {'path': '{runtime}/commands/' + aid + '.command',
                                           'openInBackground': False})
        elif kind == 'navigation':
            require(controller == 'Keypad' and not nested, 'Navigation must be a top-level key')
            require(spec.get('direction') in ('next', 'previous'), 'Invalid navigation direction')
            result = generic('com.elgato.streamdeck.page.' + spec['direction'],
                             'Next Page' if spec['direction'] == 'next' else 'Previous Page', {})
            result['Plugin'] = {'Name': 'Pages', 'UUID': 'com.elgato.streamdeck.page', 'Version': '1.0'}
        elif kind == 'multi':
            require(controller == 'Keypad' and not nested, 'Nested Multi Actions are unsupported')
            require(isinstance(spec.get('steps'), list) and spec['steps'], 'Empty macro')
            steps = []
            for i, step in enumerate(spec['steps']):
                sid = stable(aid, 'step', str(i))
                require(isinstance(step, dict), 'Invalid macro step')
                if set(step) == {'delay_ms'}:
                    require(type(step['delay_ms']) is int and 0 <= step['delay_ms'] <= 3600000,
                            'Invalid macro delay')
                    item = generic(DELAY, 'Delay', {'Delay': step['delay_ms']}); item['ActionID'] = sid
                else:
                    require(set(step) == {'action'}, 'Macro step must be action or delay_ms')
                    item = make_action(step['action'], 'Keypad', sid, page_uuid, True)
                steps.append(item)
            result = generic(MULTI, 'Multi Action', {})
            result['Actions'] = [{'Actions': steps}, {'Actions': []}]
            result['Plugin'] = {'Name': 'Multi Action', 'UUID': 'com.elgato.streamdeck.multiactions', 'Version': '1.0'}
        else:
            raise Error('Unknown action kind: ' + str(kind))
        if kind != 'native' and 'states' in spec:
            require(isinstance(spec['states'], list) and spec['states'] and all(isinstance(x, dict) for x in spec['states']), 'Invalid appearance states')
            result['States'] = copy.deepcopy(spec['states'])
            for rel in image_references(result['States']):
                require(rel in spec.get('resources', {}), 'Appearance resource mapping missing')
                payload['Profiles/' + page_uuid + '/' + rel] = resource(spec['resources'][rel])
        result['ActionID'] = aid
        return result

    for p in recipe['pages']:
        page_uuid = page_ids[p['id']]
        require(isinstance(p.get('name'), str), 'Invalid page name')
        managed['pages'][p['id']] = {'uuid': page_uuid, 'name': p['name']}
        page = {'Name': p['name'], 'Icon': '', 'Controllers': []}; occupied = set()
        require(isinstance(p.get('controls'), list), 'Invalid controls')
        for c in p['controls']:
            cid = c['id']; require(isinstance(cid, str) and NAME.fullmatch(cid), 'Invalid control ID')
            require(cid not in control_ids, 'Duplicate control ID'); control_ids.add(cid)
            ct = c['controller']; pos = c['position']
            require(ct in ('Keypad', 'Encoder'), 'Unsupported controller')
            allowed = {f'{x},{y}' for x in range(4) for y in range(2 if ct == 'Keypad' else 1)}
            require(pos in allowed and (ct, pos) not in occupied, 'Invalid or occupied position')
            occupied.add((ct, pos))
            aid = old['controls'].get(cid, {}).get('action', {}).get('ActionID', stable(namespace, 'control', cid))
            action = make_action(c['action'], ct, aid, page_uuid)
            if 'title' in c:
                require(isinstance(c['title'], str), 'Invalid title')
                for state in action['States']:
                    state.update({'Title': c['title'], 'ShowTitle': True})
            if 'icon' in c:
                data = resource(c['icon']); rel = 'Images/authored-' + digest(data)[:20] + Path(c['icon']).suffix
                payload['Profiles/' + page_uuid + '/' + rel] = data
                for state in action['States']:
                    state['Image'] = rel
            actions(page, ct)[pos] = action
            managed['controls'][cid] = {'page': page_uuid, 'controller': ct,
                                       'position': pos, 'action': action}
        manifests['Profiles/' + page_uuid + '/manifest.json'] = page
    default = stable(namespace, 'page', 'default')
    root = {'Name': recipe['name'], 'Device': catalog['device'], 'Version': '3.0',
            'Pages': {'Pages': list(page_ids.values()), 'Current': next(iter(page_ids.values())), 'Default': default}}
    manifests['manifest.json'] = root
    manifests['Profiles/' + default + '/manifest.json'] = {'Name': '', 'Icon': '', 'Controllers': []}
    if runtime:
        runtime['command_runner.py'] = Path(__file__).with_name('command_runner.py').read_bytes()
    runtime_id = digest(encoded({k: digest(v) for k, v in sorted(runtime.items())}))
    runtime_target = workspace / 'releases' / runtime_id
    interpreter = str(Path(sys.executable).resolve())
    require(not any(c.isspace() for c in interpreter), 'Interpreter path cannot contain whitespace')
    for rel in list(runtime):
        if rel.startswith('commands/') and rel.endswith('.json'):
            config = json.loads(runtime[rel]); config['argv'] = [x.replace('{runtime}', str(runtime_target)) for x in config['argv']]
            runtime[rel] = encoded(config)
            launcher = ('#!' + interpreter + '\nimport runpy\nfrom pathlib import Path\n'
                        'm = runpy.run_path(str(Path(__file__).resolve().parents[1] / "command_runner.py"))\n'
                        'raise SystemExit(m["main"](str(Path(__file__).with_suffix(".json"))))\n')
            runtime[rel.removesuffix('.json') + '.command'] = launcher.encode()
    def replace(value):
        if isinstance(value, dict): return {k: replace(v) for k, v in value.items()}
        if isinstance(value, list): return [replace(v) for v in value]
        if isinstance(value, str): return value.replace('{runtime}', str(runtime_target))
        return value
    manifests, managed = replace(manifests), replace(managed)
    payload.update({k: encoded(v) for k, v in manifests.items()})
    return {'files': payload, 'runtime': runtime, 'runtime_target': str(runtime_target),
            'managed': managed, 'dependencies': dependencies, 'profile_id': profile_id,
            'inputs': {str(workspace / x): digest((workspace / x).read_bytes())
                       for x in ('recipe.json', 'catalog.json')}, 'workspace': str(workspace)}


def generic(uid, name, settings):
    return {'ActionID': '', 'UUID': uid, 'Name': name, 'LinkedTitle': True, 'Resources': None,
            'Settings': settings, 'State': 0, 'States': [{'Title': name, 'ShowTitle': True}],
            'Plugin': {'UUID': uid, 'Name': name, 'Version': '1.0'}}


def emit_files(root, files):
    for rel, data in files.items():
        target = child(root, rel); target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        target.chmod(0o700 if rel.endswith('.command') else 0o600)


def check_output(workspace, output):
    workspace, output = absolute(workspace), absolute(output)
    protected = [workspace]
    if (workspace / 'baseline.json').exists():
        target = absolute(read(workspace / 'baseline.json')['target'])
        protected.append(target.parent if target.parent.name == 'ProfilesV3' else target)
    for root in protected:
        require(output != root and root not in output.parents and output not in root.parents,
                'Output overlaps protected workspace or profiles directory')


def build(workspace, output):
    output = absolute(output); check_output(workspace, output); compiled = compile_profile(workspace)
    require(not output.exists(), 'Build output must not exist')
    require(not str(output).startswith(str(absolute(workspace)) + '/releases/'), 'Cannot build into live releases')
    output.mkdir(parents=True, mode=0o700)
    try:
        emit_files(output / 'profile', compiled.pop('files'))
        runtime = compiled.pop('runtime')
        (output / 'runtime').mkdir(); emit_files(output / 'runtime', runtime)
        compiled.update({'profile_digest': tree_hash(output / 'profile'),
                         'runtime_digest': tree_hash(output / 'runtime')})
        write(output / 'candidate.json', compiled)
        with zipfile.ZipFile(output / 'profile.streamDeckProfile', 'x', zipfile.ZIP_DEFLATED) as archive:
            for rel in sorted(tree(output / 'profile')):
                info = zipfile.ZipInfo(compiled['profile_id'] + '.sdProfile/' + rel, (2020, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, child(output / 'profile', rel).read_bytes())
        return {'status': 'built', 'candidate': str(output), 'profile_changed': False}
    except BaseException:
        shutil.rmtree(output)
        raise


def check_candidate(candidate):
    candidate = absolute(candidate); data = read(candidate / 'candidate.json')
    require(tree_hash(candidate / 'profile') == data['profile_digest'], 'Candidate profile changed')
    require(tree_hash(candidate / 'runtime') == data['runtime_digest'], 'Candidate runtime changed')
    for p, h in data['inputs'].items():
        require(digest(absolute(p).read_bytes()) == h, 'Recipe or catalog changed; rebuild')
    for p, info in data['dependencies'].items():
        path = absolute(p)
        require(digest(path.read_bytes()) == info['sha256'] and path.stat().st_mode & 0o777 == info['mode'],
                'Supporting resource changed; rebuild')
    return data


def check_plugins(profile_path, plugin_dir):
    plugins = absolute(plugin_dir)
    require(plugins.is_dir(), 'Plugin directory missing')
    _, pages = profile(profile_path)
    missing = set()
    def visit(v):
        if isinstance(v, dict):
            uid = v.get('Plugin', {}).get('UUID', '')
            if uid and not uid.startswith('com.elgato.streamdeck.'):
                if not (plugins / (uid + '.sdPlugin')).is_dir(): missing.add(uid)
            for val in v.values(): visit(val)
        elif isinstance(v, list):
            for val in v: visit(val)
    for page in pages.values(): visit(page)
    require(not missing, 'Missing plugins: ' + ', '.join(sorted(missing)))


def merge(target, candidate, baseline):
    root, pages = profile(target); new_root, new_pages = profile(candidate)
    before = baseline['managed']; after = read(Path(candidate).parent / 'candidate.json')['managed']
    conflicts = []; changes = []
    root = copy.deepcopy(root); pages = copy.deepcopy(pages)
    # Conservatively retain user page ordering; append new pages, reject populated deletions.
    for key, info in after['pages'].items():
        prev = before['pages'].get(key)
        if prev:
            if info['uuid'] not in pages:
                conflicts.append(key + ': page removed manually'); continue
            name = pages[info['uuid']].get('Name', '')
            if info['name'] != prev['name']:
                if name not in (prev['name'], info['name']): conflicts.append(key + ': page name conflict')
                else: pages[info['uuid']]['Name'] = info['name']
        else:
            require(info['uuid'] not in pages, 'New page UUID collision')
            pages[info['uuid']] = copy.deepcopy(new_pages[info['uuid']])
            for c in pages[info['uuid']]['Controllers']: c['Actions'] = {}
            root['Pages']['Pages'].append(info['uuid'])
    def locate(cid, info):
        aid = info['action']['ActionID']; matches = []
        for pgid, page in pages.items():
            for c in page.get('Controllers', []):
                for pos, a in (c.get('Actions') or {}).items():
                    if a.get('ActionID') == aid: matches.append((pgid, c['Type'], pos, a))
        return matches
    pending_controls = []
    for cid in sorted(set(before['controls']) | set(after['controls'])):
        prev, want = before['controls'].get(cid), after['controls'].get(cid)
        if prev == want: continue
        if prev and want and authored(prev) == authored(want): continue
        if prev:
            matches = locate(cid, prev)
            expected = (prev['page'], prev['controller'], prev['position'])
            if len(matches) != 1 or matches[0][:3] != expected or authored(matches[0][3]) != authored(prev['action']):
                conflicts.append(cid + ': manually edited, moved, or removed'); continue
            actions(pages[prev['page']], prev['controller']).pop(prev['position'])
        pending_controls.append((cid, want))
    for cid, want in pending_controls:
        if want:
            if want['page'] not in pages:
                conflicts.append(cid + ': missing destination page'); continue
            dest = actions(pages[want['page']], want['controller'])
            if want['position'] in dest:
                conflicts.append(cid + ': destination occupied'); continue
            dest[want['position']] = copy.deepcopy(want['action'])
        changes.append(cid)
    for key, info in before['pages'].items():
        if key in after['pages']: continue
        page = pages.get(info['uuid'])
        if page and any(c.get('Actions') for c in page.get('Controllers', [])):
            conflicts.append(key + ': removed page has retained controls'); continue
        if info['uuid'] in root['Pages']['Pages']: root['Pages']['Pages'].remove(info['uuid'])
        pages.pop(info['uuid'], None)
    require(not conflicts, 'Conflicts: ' + '; '.join(conflicts))
    require(root['Pages']['Pages'], 'Cannot remove every page')
    if root['Pages']['Current'] not in root['Pages']['Pages']: root['Pages']['Current'] = root['Pages']['Pages'][0]
    # Profile renaming is intentionally not automated; identity/name is user-owned.
    files = {}
    if root != read(Path(target) / 'manifest.json'): files['manifest.json'] = encoded(root)
    for k, v in pages.items():
        rel = 'Profiles/' + k + '/manifest.json'
        if not child(target, rel).exists() or read(child(target, rel)) != v: files[rel] = encoded(v)
    candidate_files = tree(candidate)
    for rel in candidate_files:
        if not rel.endswith('manifest.json'):
            dest = child(target, rel); data = child(candidate, rel).read_bytes()
            used_by_change = any(rel == 'Profiles/' + after['controls'][cid]['page'] + '/' + image
                                 for cid in changes if cid in after['controls']
                                 for image in image_references(after['controls'][cid]['action']))
            if dest.exists() and dest.read_bytes() != data:
                require(not used_by_change, 'Existing resource differs: ' + rel)
            elif not dest.exists():
                files[rel] = data
    return files, changes


def plan(workspace, candidate, plugins, output):
    workspace, candidate, output = absolute(workspace), absolute(candidate), absolute(output)
    check_output(workspace, output)
    require(not output.exists(), 'Plan output must not exist')
    data = check_candidate(candidate); baseline = read(workspace / 'baseline.json')
    require(data['workspace'] == str(workspace) and data['profile_id'] == baseline['profile_id'], 'Wrong candidate workspace')
    target = absolute(baseline['target']); target_digest = tree_hash(target)
    files, changes = merge(target, candidate / 'profile', baseline)
    check_plugins(candidate / 'profile', plugins)
    output.mkdir(parents=True, mode=0o700)
    try:
        shutil.copytree(target, output / 'profile')
        emit_files(output / 'profile', files)
        # Remove authored pages absent from merged root; preserve other ancillary pages.
        existing = profile(target)[0]['Pages']['Pages']; merged = read(output / 'profile' / 'manifest.json')['Pages']['Pages']
        for pid in set(existing) - set(merged): shutil.rmtree(output / 'profile' / 'Profiles' / pid)
        require(tree_hash(target) == target_digest, 'Profile changed while planning')
        receipt = {'version': VERSION, 'workspace': str(workspace), 'target': str(target),
                   'candidate': str(candidate), 'candidate_digest': tree_hash(candidate),
                   'baseline_digest': digest((workspace / 'baseline.json').read_bytes()),
                   'target_digest': target_digest, 'result_digest': tree_hash(output / 'profile'),
                   'plugins': str(absolute(plugins)), 'changes': changes,
                   'runtime_target': data['runtime_target'], 'runtime_digest': data['runtime_digest']}
        write(output / 'plan.json', receipt)
        return {'status': 'planned', 'plan': str(output), 'changed_controls': changes,
                'profile_changed': False}
    except BaseException:
        shutil.rmtree(output); raise


def ensure_closed():
    result = subprocess.run(['/bin/ps', 'ax', '-o', 'comm='], capture_output=True, text=True, timeout=10)
    require(result.returncode == 0, 'Cannot establish Stream Deck process state')
    require(not any('/Stream Deck.app/Contents/MacOS/' in x or
                    '/Elgato Stream Deck.app/Contents/MacOS/' in x for x in result.stdout.splitlines()),
            'Close Stream Deck before changing profiles')


@contextmanager
def locked(workspace):
    workspace = absolute(workspace); require(workspace.is_dir(), 'Workspace missing')
    path = workspace / 'install.lock'; absolute(path)
    with path.open('a+') as lock:
        try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc: raise Error('Another installation holds the lock') from exc
        try: yield
        finally: fcntl.flock(lock, fcntl.LOCK_UN)


def apply(plan_dir):
    plan_dir = absolute(plan_dir); p = read(plan_dir / 'plan.json'); ws = absolute(p['workspace'])
    with locked(ws):
        ensure_closed()
        require(not (ws / 'pending.json').exists(), 'Recover pending installation with rollback first')
        target = absolute(p['target']); candidate = absolute(p['candidate'])
        baseline_before = read(ws / 'baseline.json')
        require(target == absolute(baseline_before['target']), 'Plan target does not match baseline')
        require(tree_hash(target) == p['target_digest'], 'Stale plan: target changed')
        require(digest((ws / 'baseline.json').read_bytes()) == p['baseline_digest'], 'Stale plan: baseline changed')
        require(tree_hash(candidate) == p['candidate_digest'], 'Stale plan: candidate changed')
        require(tree_hash(plan_dir / 'profile') == p['result_digest'], 'Staged profile changed')
        data = check_candidate(candidate); check_plugins(plan_dir / 'profile', p['plugins'])
        runtime_target = absolute(p['runtime_target'])
        require(runtime_target == ws / 'releases' / runtime_target.name, 'Invalid release target')
        if runtime_target.exists(): require(tree_hash(runtime_target) == p['runtime_digest'], 'Release content changed')
        if p['target_digest'] == p['result_digest'] and baseline_before['managed'] == data['managed']:
            return {'status': 'unchanged', 'changed_controls': [], 'device_outcome': 'unverified'}
        token = uuid.uuid4().hex; tx = absolute(ws / 'transactions' / token); tx.mkdir(parents=True, mode=0o700)
        shutil.copytree(target, tx / 'backup')
        require(tree_hash(tx / 'backup') == p['target_digest'], 'Backup mismatch')
        shutil.copy2(ws / 'baseline.json', tx / 'baseline-before.json')
        stage = target.with_name(target.name + '.stage-' + token)
        displaced = target.with_name(target.name + '.previous-' + token)
        require(not stage.exists() and not displaced.exists(), 'Transaction path collision')
        shutil.copytree(plan_dir / 'profile', stage)
        require(tree_hash(stage) == p['result_digest'], 'Staging mismatch')
        baseline_after = copy.deepcopy(baseline_before)
        baseline_after.update(managed=data['managed'], runtime=str(runtime_target))
        write(tx / 'baseline-after.json', baseline_after)
        journal = dict(p, baseline_after_digest=digest(encoded(baseline_after)), transaction=str(tx), stage=str(stage), displaced=str(displaced), phase='prepared',
                       runtime_existed=runtime_target.exists())
        write(tx / 'receipt.json', journal); atomic_json(ws / 'pending.json', journal)
        try:
            if not runtime_target.exists():
                runtime_target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(candidate / 'runtime', runtime_target)
                require(tree_hash(runtime_target) == p['runtime_digest'], 'Runtime copy mismatch')
            ensure_closed()
            require(tree_hash(target) == p['target_digest'], 'Target changed before replacement')
            target.rename(displaced); stage.rename(target)
            require(tree_hash(target) == p['result_digest'], 'Installed profile mismatch')
            atomic_json(ws / 'baseline.json', baseline_after)
            journal['baseline_after_digest'] = digest((ws / 'baseline.json').read_bytes())
            journal['phase'] = 'installed'
            atomic_json(tx / 'receipt.json', journal); (ws / 'pending.json').unlink()
            shutil.rmtree(displaced)
            return {'status': 'installed', 'receipt': str(tx / 'receipt.json'),
                    'changed_controls': p['changes'], 'device_outcome': 'unverified'}
        except BaseException:
            # Leave all evidence intact. Explicit rollback is deterministic and guarded.
            raise


def rollback(receipt):
    receipt = absolute(receipt); p = read(receipt); ws = absolute(p['workspace'])
    with locked(ws):
        ensure_closed(); target = absolute(p['target']); tx = absolute(p['transaction'])
        require(tx.parent == ws / 'transactions', 'Invalid transaction path')
        pending = ws / 'pending.json'
        if pending.exists():
            require(read(pending)['transaction'] == str(tx), 'Different pending transaction')
        require(tree_hash(tx / 'backup') == p['target_digest'], 'Backup changed')
        before = tx / 'baseline-before.json'
        require(digest(before.read_bytes()) == p['baseline_digest'], 'Baseline backup changed')
        require(absolute(read(before)['target']) == target, 'Receipt target mismatch')
        allowed = {p['baseline_digest'], p['baseline_after_digest']}
        require(digest((ws / 'baseline.json').read_bytes()) in allowed, 'Baseline changed after installation')
        rollback_journal = tx / 'rollback.json'
        if rollback_journal.exists():
            recovery = read(rollback_journal)
            restore, saved = absolute(recovery['restore']), absolute(recovery['saved'])
            require(restore.parent == target.parent and restore.name.startswith(target.name + '.restore-'), 'Invalid restore path')
            require(saved.parent == tx and saved.name.startswith('replaced-'), 'Invalid saved profile path')
        else:
            restore = target.with_name(target.name + '.restore-' + uuid.uuid4().hex)
            saved = tx / ('replaced-' + uuid.uuid4().hex)
        if target.exists():
            require(tree_hash(target) in (p['result_digest'], p['target_digest']), 'Profile changed after installation')
        else:
            displaced = absolute(p['displaced'])
            require(displaced.parent == target.parent and displaced.name.startswith(target.name + '.previous-'), 'Invalid displaced path')
            require((displaced.is_dir() and tree_hash(displaced) == p['target_digest']) or
                    (saved.is_dir() and tree_hash(saved) in (p['result_digest'], p['target_digest'])),
                    'Missing recoverable profile')
        if not restore.exists(): shutil.copytree(tx / 'backup', restore)
        require(tree_hash(restore) == p['target_digest'], 'Restore copy mismatch')
        atomic_json(rollback_journal, {'restore': str(restore), 'saved': str(saved), 'phase': 'prepared'})
        if target.exists():
            if tree_hash(target) != p['target_digest']:
                require(not saved.exists(), 'Recovery destination occupied')
                target.rename(saved)
            else:
                shutil.rmtree(restore)
        if not target.exists(): restore.rename(target)
        atomic_json(ws / 'baseline.json', read(before))
        require(tree_hash(target) == p['target_digest'], 'Restoration mismatch')
        if pending.exists(): pending.unlink()
        # Immutable releases remain retained; restored profile uses its previous resource paths.
        atomic_json(tx / 'restored.json', {'status': 'restored', 'target_digest': p['target_digest']})
        return {'status': 'restored', 'profile': str(target), 'digest': p['target_digest']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true')
    subs = parser.add_subparsers(dest='command', required=True)
    p = subs.add_parser('inspect'); p.add_argument('--profile', required=True)
    p = subs.add_parser('adopt'); p.add_argument('--profile', required=True); p.add_argument('--workspace', required=True)
    p = subs.add_parser('validate'); p.add_argument('--workspace', required=True); p.add_argument('--plugins')
    p = subs.add_parser('build'); p.add_argument('--workspace', required=True); p.add_argument('--output', required=True)
    p = subs.add_parser('plan'); p.add_argument('--workspace', required=True); p.add_argument('--candidate', required=True); p.add_argument('--plugins', required=True); p.add_argument('--output', required=True)
    p = subs.add_parser('apply'); p.add_argument('--plan', required=True)
    p = subs.add_parser('rollback'); p.add_argument('--receipt', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'inspect': result = inventory(absolute(args.profile))
        elif args.command == 'adopt': result = adopt(args.profile, args.workspace)
        elif args.command == 'build': result = build(args.workspace, args.output)
        elif args.command == 'plan': result = plan(args.workspace, args.candidate, args.plugins, args.output)
        elif args.command == 'apply': result = apply(args.plan)
        elif args.command == 'rollback': result = rollback(args.receipt)
        else:
            data = compile_profile(args.workspace)
            if args.plugins:
                with tempfile.TemporaryDirectory() as tmp:
                    emit_files(Path(tmp).resolve(), data['files']); check_plugins(Path(tmp).resolve(), args.plugins)
            result = {'status': 'valid', 'pages': len(data['managed']['pages']),
                      'controls': len(data['managed']['controls']), 'device_outcome': 'unverified'}
        print(json.dumps(result, indent=2) if args.json else '\n'.join(f'{k}: {v}' for k, v in result.items()))
        return 0
    except (Error, OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        result = {'status': 'error', 'error': str(exc)}
        print(json.dumps(result) if args.json else 'Error: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())

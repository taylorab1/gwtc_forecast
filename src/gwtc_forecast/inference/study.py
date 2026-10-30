"""Small file-based entry points; release adapters remain explicit student work."""
from __future__ import annotations
import json
import os
from pathlib import Path
from ..io.contracts import read_event_contract, read_selection_contract, read_hyperposterior_contract
from .training import load_prior_spec, fit_bbh_training
from .frozen import compare_frozen_pair
from ..populations.matched_bbh import MatchedBBH

def _path(value, base):
    p = Path(os.path.expandvars(value)).expanduser()
    return p.resolve() if p.is_absolute() else (base / p).resolve()

def audit_study(path):
    path = Path(path).resolve()
    spec = json.loads(path.read_text())
    missing = []
    for key in ('training_event_contracts', 'heldout_event_contracts'):
        if not spec.get(key):
            missing.append(f'{key}: no contracts listed')
        for filename in spec.get(key, []):
            if not _path(filename, path.parent).is_file():
                missing.append(f'{key}: missing {filename}')
    if not spec.get('selection_contracts'):
        missing.append('no selection contracts listed')
    for run, filename in spec.get('selection_contracts', {}).items():
        if not _path(filename, path.parent).is_file():
            missing.append(f'selection {run}: missing {filename}')
    for key in ('prior_spec', 'qualification_report'):
        if not spec.get(key) or not _path(spec[key], path.parent).is_file():
            missing.append(f'{key}: missing')
    if spec.get('prior_spec') and _path(spec['prior_spec'], path.parent).is_file():
        prior = load_prior_spec(_path(spec['prior_spec'], path.parent))
        if prior.get('status') != 'frozen_for_training':
            missing.append('priors are development candidates, not frozen')
    return {'status': 'BLOCKED' if missing else 'INPUT_PATHS_PRESENT_NOT_SCIENTIFIC_VALIDATION', 'missing': missing, 'automatic_authorization': False, 'next_step': 'Resolve only the inputs required by the current milestone; do not download the full catalog now.'}

def _load(path, section):
    p = Path(path).resolve()
    s = json.loads(p.read_text())
    base = p.parent
    if not s.get(section):
        raise ValueError(f'no {section} specified')
    events = [read_event_contract(_path(x, base)) for x in s[section]]
    required = {e.run for e in events}
    selections = {r: read_selection_contract(_path(s['selection_contracts'][r], base)) for r in required}
    for r, c in selections.items():
        if r != c.run:
            raise ValueError('selection run key/contract mismatch')
    return (s, base, events, selections)

def fit_study(path, *, feature, outdir, seed=20260904, nlive=500):
    s, base, events, selections = _load(path, 'training_event_contracts')
    return fit_bbh_training(events, selections, prior_spec_path=_path(s['prior_spec'], base), feature=feature, outdir=outdir, seed=seed, nlive=nlive, qualification_reference=_path(s['qualification_report'], base))

def score_study(path, *, outdir):
    s, base, events, selections = _load(path, 'heldout_event_contracts')
    if s.get('allow_retrospective_scoring') is not True:
        raise ValueError('retrospective scoring has not been explicitly authorized in the study specification')
    if any((not e.metadata.get('validated') for e in events)) or any((not c.metadata.get('validated') for c in selections.values())):
        raise ValueError('scoring requires validated PE and selection contracts')
    if not s.get('qualification_report') or not _path(s['qualification_report'], base).is_file():
        raise ValueError('missing qualification report')
    ps = load_prior_spec(_path(s['prior_spec'], base))
    if ps.get('status') != 'frozen_for_training':
        raise ValueError('priors are not frozen')
    posterior_paths = s.get('training_posteriors', {})
    posteriors = [read_hyperposterior_contract(_path(posterior_paths[k], base)) for k in ('continuum', 'highpeak')]
    if any((not p.metadata.get('sampler_qualified') for p in posteriors)):
        raise ValueError('training sampler and finite-draw support are not qualified')
    import hashlib
    identity = hashlib.sha256(_path(s['prior_spec'], base).read_bytes()).hexdigest()
    if any((p.metadata.get('prior_spec_sha256') != identity for p in posteriors)):
        raise ValueError('posterior and current prior/model specification differ')
    models = [MatchedBBH(feature=f, **ps['model_options']) for f in (False, True)]
    if [p.model_name for p in posteriors] != [m.name for m in models]:
        raise ValueError('posterior model identities differ from the requested comparison')
    out = Path(outdir).resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError('output already contains results')
    report = compare_frozen_pair(events, selections, models, posteriors)
    out.mkdir(parents=True, exist_ok=True)
    (out / 'frozen_comparison.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    return report

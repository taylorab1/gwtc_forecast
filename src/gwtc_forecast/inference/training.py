"""Optional Bilby/Dynesty training-only adapter for validated statistical objects.

No release priors, event memberships, or sensitivity normalizations are guessed.
This adapter is not executed on public data as part of the distribution build.


Implementation notes
--------------------
Avoid module-level optional dependency and support likelihood(parameters)
as well as the self.parameters API in the inherited pinned environment.
Reproducibility is recorded, not inferred from a seed alone."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
from ..statistics.objects import HyperPosterior
from ..statistics.likelihood import catalog_log_likelihood
from ..io.contracts import write_hyperposterior_contract
from ..populations.matched_bbh import MatchedBBH

def load_prior_spec(path):
    spec = json.loads(Path(path).read_text())
    if set(spec['shared']) & set(spec['feature_only']):
        raise ValueError('shared and feature-only priors must not overlap')
    expected = {'f_high', 'mu_high', 'sigma_high'}
    if set(spec['feature_only']) != expected:
        raise ValueError("feature-only prior must contain exactly the high component's parameters")
    return spec

def training_log_likelihood(parameters, *, events, selections, model):
    h = HyperPosterior({k: np.array([v], float) for k, v in parameters.items()}, model_name=model.name)
    evaluation = catalog_log_likelihood(events, selections, model, h)
    return float(evaluation.log_likelihood[0])

def make_bilby_likelihood(bilby, *, parameter_names, events, selections, model):

    class TrainingLikelihood(bilby.Likelihood):

        def __init__(self):
            super().__init__(parameters={k: None for k in parameter_names})

        def log_likelihood(self, parameters=None):
            pars = self.parameters if parameters is None else parameters
            return training_log_likelihood(pars, events=events, selections=selections, model=model)
    return TrainingLikelihood()

def fit_bbh_training(events, selections, *, prior_spec_path, feature, outdir, seed, sampler='dynesty', nlive=500, dlogz=0.1, qualification_reference=None):
    if not qualification_reference or not Path(qualification_reference).is_file():
        raise ValueError('training requires an inspectable qualification report, not an enable flag')
    if not events or len({e.event_id for e in events}) != len(events):
        raise ValueError('unique nonempty training catalog required')
    allowed_runs = {'O1', 'O2', 'O1O2', 'O3', 'O3a', 'O3b'}
    if any((e.run not in allowed_runs for e in events)):
        raise ValueError('O4/future data cannot enter this training adapter')
    if any((not e.metadata.get('validated') for e in events)):
        raise ValueError('all real event contracts must be validated before training')
    if any((not selections[e.run].metadata.get('validated') for e in events)):
        raise ValueError('all training selection campaigns must be validated')
    spec = load_prior_spec(prior_spec_path)
    if spec.get('status') != 'frozen_for_training':
        raise ValueError('development priors have not been frozen; review training-only prior predictions first')
    output = Path(outdir).expanduser().resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError('choose an unused fit attempt directory; no silent overwrite/resume')
    try:
        import bilby
    except ImportError as exc:
        raise RuntimeError('Install the documented science environment for Bilby/Dynesty training') from exc
    raw = {**spec['shared'], **(spec['feature_only'] if feature else {})}
    priors = bilby.core.prior.PriorDict()
    for name, value in raw.items():
        if isinstance(value, (int, float)):
            priors[name] = float(value)
        else:
            kind = value['distribution']
            if kind not in {'Uniform', 'LogUniform'}:
                raise ValueError(f'unsupported prior distribution {kind}')
            priors[name] = getattr(bilby.core.prior, kind)(minimum=value['minimum'], maximum=value['maximum'], name=name)
    model = MatchedBBH(feature=feature, **spec['model_options'])
    likelihood = make_bilby_likelihood(bilby, parameter_names=raw, events=events, selections=selections, model=model)
    output.mkdir(parents=True, exist_ok=True)
    np.random.seed(seed)
    if hasattr(bilby.core.utils, 'random') and hasattr(bilby.core.utils.random, 'seed'):
        bilby.core.utils.random.seed(seed)
    result = bilby.run_sampler(likelihood=likelihood, priors=priors, sampler=sampler, nlive=int(nlive), dlogz=float(dlogz), outdir=str(output), label=model.name, resume=False, plot=False)
    samples = {}
    for name in raw:
        if name in result.posterior:
            samples[name] = np.asarray(result.posterior[name], float)
        elif isinstance(raw[name], (int, float)):
            samples[name] = np.full(len(result.posterior), raw[name], float)
        else:
            raise ValueError(f'sampler omitted parameter {name}')
    posterior = HyperPosterior(samples, model_name=model.name, metadata={'representation': 'sampler_posterior_rows', 'trained_on': [e.event_id for e in events], 'training_runs': sorted({e.run for e in events}), 'training_only': True, 'prior_spec_sha256': hashlib.sha256(Path(prior_spec_path).read_bytes()).hexdigest(), 'model_options': spec['model_options'], 'sampler': sampler, 'bilby_version': bilby.__version__, 'seed': int(seed), 'qualification_reference': str(qualification_reference), 'sampler_qualified': False, 'log_evidence_up_to_common_constants': float(result.log_evidence), 'log_evidence_error_reported_by_sampler': float(result.log_evidence_err)})
    write_hyperposterior_contract(output / 'training_posterior.h5', posterior)
    (output / 'NOTICE.md').write_text('Training finished. Sampler agreement, numerical likelihood accuracy and held-out support remain to be qualified. This is not a validated predictive result.\n')
    return posterior

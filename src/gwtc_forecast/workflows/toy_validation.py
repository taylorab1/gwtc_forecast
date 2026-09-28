from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

from ..populations.toy_mass import BrokenPowerLaw, PowerLaw, PowerLawPlusPeak
from ..statistics.diagnostics import (
    bootstrap_predictive_score,
    leave_one_event_out_influence,
    summarize_ess,
)
from ..statistics.likelihood import catalog_log_likelihood
from ..statistics.objects import EventPosterior, HyperPosterior, SelectionCampaign
from ..statistics.predictive import predictive_log_score, prequential_score
from .common import write_json_atomic

LOW = 5.0
HIGH = 90.0
LOG_UNIFORM_PRIOR = -np.log(HIGH - LOW)


def _detection_probability(mass: np.ndarray, *, run: str) -> np.ndarray:
    mass = np.asarray(mass, dtype=float)
    shift = 1.5 if run == "ToyO4b" else 0.0
    probability = 0.04 + 0.90 / (1.0 + np.exp(-(mass - 24.0 + shift) / 6.5))
    return np.clip(probability, 0.0, 0.98)


def _truncated_normal(
    rng: np.random.Generator,
    *,
    mean: float,
    sigma: float,
    size: int,
    low: float = LOW,
    high: float = HIGH,
) -> np.ndarray:
    accepted: list[float] = []
    while len(accepted) < size:
        candidates = rng.normal(mean, sigma, size=max(64, 2 * (size - len(accepted))))
        accepted.extend(candidates[(candidates >= low) & (candidates <= high)].tolist())
    return np.asarray(accepted[:size], dtype=float)


def _selection_campaign(
    rng: np.random.Generator, *, run: str, generated: int
) -> SelectionCampaign:
    proposed = rng.uniform(LOW, HIGH, size=generated)
    found = rng.random(generated) < _detection_probability(proposed, run=run)
    masses = proposed[found]
    if len(masses) < 1000:
        raise RuntimeError("toy selection campaign unexpectedly has too few detections")
    return SelectionCampaign(
        run=run,
        samples={"mass_1_source": masses},
        log_draw_density=np.full(len(masses), LOG_UNIFORM_PRIOR),
        # Each found injection contributes 1/N_generated.  The detection mask has
        # already been applied, so the sum estimates the detection efficiency.
        log_base_weight=np.full(len(masses), -np.log(generated)),
        metadata={
            "generated": generated,
            "found": int(found.sum()),
            "draw": "uniform mass_1_source",
            "purpose": "deterministic end-to-end statistics validation",
        },
    )


def _detected_true_mass(
    rng: np.random.Generator,
    model: PowerLawPlusPeak,
    hyperparameters: dict[str, float],
    *,
    run: str,
) -> float:
    while True:
        candidate = float(model.sample(rng, 1, hyperparameters)[0])
        if rng.random() < float(_detection_probability(np.asarray([candidate]), run=run)[0]):
            return candidate


def _events(
    rng: np.random.Generator,
    *,
    count_per_run: int,
    posterior_samples: int,
) -> list[EventPosterior]:
    true_model = PowerLawPlusPeak()
    truth = {
        "alpha": -2.0,
        "m_min": LOW,
        "m_max": HIGH,
        "peak_fraction": 0.55,
        "peak_mean": 35.0,
        "peak_sigma": 3.0,
    }
    events: list[EventPosterior] = []
    for run in ("ToyO4a", "ToyO4b"):
        for index in range(count_per_run):
            true_mass = _detected_true_mass(rng, true_model, truth, run=run)
            sigma = 1.2 + 0.012 * true_mass
            posterior = _truncated_normal(
                rng,
                mean=true_mass,
                sigma=sigma,
                size=posterior_samples,
            )
            event_id = f"{run}_{index + 1:03d}"
            events.append(
                EventPosterior(
                    event_id=event_id,
                    run=run,
                    samples={"mass_1_source": posterior},
                    log_pe_prior=np.full(posterior_samples, LOG_UNIFORM_PRIOR),
                    metadata={
                        "true_mass_1_source": true_mass,
                        "measurement_sigma": sigma,
                        "pe_prior": "Uniform(5, 90)",
                    },
                )
            )
    return events


def _peak_hyperposterior(rng: np.random.Generator, draws: int) -> HyperPosterior:
    return HyperPosterior(
        model_name="toy_peak",
        samples={
            "alpha": rng.normal(-2.0, 0.10, draws),
            "m_min": np.full(draws, LOW),
            "m_max": np.full(draws, HIGH),
            "peak_fraction": np.clip(rng.normal(0.55, 0.045, draws), 0.30, 0.75),
            "peak_mean": rng.normal(35.0, 0.65, draws),
            "peak_sigma": np.clip(rng.normal(3.0, 0.35, draws), 1.5, 5.0),
        },
        metadata={"status": "synthetic draws near the generating population"},
    )


def _smooth_hyperposterior(rng: np.random.Generator, draws: int) -> HyperPosterior:
    return HyperPosterior(
        model_name="toy_smooth",
        samples={
            "alpha": rng.normal(-1.55, 0.14, draws),
            "m_min": np.full(draws, LOW),
            "m_max": np.full(draws, HIGH),
        },
        metadata={"status": "synthetic smooth competitor"},
    )


def _break_hyperposterior(rng: np.random.Generator, draws: int) -> HyperPosterior:
    return HyperPosterior(
        model_name="toy_break",
        samples={
            "alpha_low": rng.normal(-1.0, 0.15, draws),
            "alpha_high": rng.normal(-3.0, 0.20, draws),
            "m_min": np.full(draws, LOW),
            "m_break": rng.normal(35.0, 0.8, draws),
            "m_max": np.full(draws, HIGH),
        },
        metadata={"status": "synthetic broken-power-law competitor"},
    )


def _evaluate_model(
    *,
    name: str,
    model: Any,
    hyperposterior: HyperPosterior,
    events: list[EventPosterior],
    selections: dict[str, SelectionCampaign],
    tolerance: float,
    bootstrap_rng: np.random.Generator,
) -> dict[str, Any]:
    evaluation = catalog_log_likelihood(events, selections, model, hyperposterior)
    joint_score = predictive_log_score(evaluation.log_likelihood, hyperposterior)
    sequential = prequential_score(
        events,
        evaluation,
        hyperposterior,
        tolerance=tolerance,
    )
    event_ess = np.concatenate(
        [item.effective_sample_size for item in evaluation.events.values()]
    )
    selection_ess = np.concatenate(
        [item.effective_sample_size for item in evaluation.selections.values()]
    )
    bootstrap = bootstrap_predictive_score(
        evaluation.log_likelihood,
        hyperposterior,
        rng=bootstrap_rng,
        replicates=200,
    )
    influence = leave_one_event_out_influence(events, evaluation, hyperposterior)
    return {
        "name": name,
        "joint_log_score": joint_score,
        "prequential_log_score": sequential.cumulative_log_score,
        "joint_prequential_absolute_difference": sequential.absolute_difference,
        "minimum_event_ess": float(np.min(event_ess)),
        "minimum_selection_ess": float(np.min(selection_ess)),
        "event_ess_summary": asdict(summarize_ess(event_ess)),
        "selection_ess_summary": asdict(summarize_ess(selection_ess)),
        "hyperposterior_draw_bootstrap": asdict(bootstrap),
        "leave_one_event_out_influence": [asdict(item) for item in influence],
        "steps": [asdict(step) for step in sequential.steps],
    }


def run_toy_validation(
    *,
    output_dir: Path | None = None,
    seed: int = 20260821,
    count_per_run: int = 10,
    posterior_samples: int = 600,
    hyperposterior_draws: int = 32,
    generated_injections_per_run: int = 50_000,
    tolerance: float = 1.0e-9,
) -> dict[str, Any]:
    """Run a deterministic vertical slice of the predictive-statistics pipeline.

    The generating model has a strong localized peak.  The smoke test therefore
    requires the peak model to beat a smooth power law.  This is not a claim
    about the real GW catalog; it is an implementation and sign-convention test.
    """

    rng = np.random.default_rng(seed)
    selections = {
        run: _selection_campaign(
            rng, run=run, generated=generated_injections_per_run
        )
        for run in ("ToyO4a", "ToyO4b")
    }
    events = _events(
        rng,
        count_per_run=count_per_run,
        posterior_samples=posterior_samples,
    )
    competitors = {
        "peak": (PowerLawPlusPeak(), _peak_hyperposterior(rng, hyperposterior_draws)),
        "break": (BrokenPowerLaw(), _break_hyperposterior(rng, hyperposterior_draws)),
        "smooth": (PowerLaw(), _smooth_hyperposterior(rng, hyperposterior_draws)),
    }
    models = {
        name: _evaluate_model(
            name=name,
            model=model,
            hyperposterior=hyperposterior,
            events=events,
            selections=selections,
            tolerance=tolerance,
            bootstrap_rng=np.random.default_rng(seed + {"peak": 11, "break": 22, "smooth": 33}[name]),
        )
        for name, (model, hyperposterior) in competitors.items()
    }
    delta_peak_smooth = (
        models["peak"]["joint_log_score"] - models["smooth"]["joint_log_score"]
    )
    delta_peak_break = (
        models["peak"]["joint_log_score"] - models["break"]["joint_log_score"]
    )
    passed = bool(
        delta_peak_smooth > 2.0
        and all(
            item["joint_prequential_absolute_difference"] <= tolerance
            for item in models.values()
        )
    )
    report: dict[str, Any] = {
        "schema": "gwtc_forecast.toy_validation.v1",
        "status": "PASS" if passed else "FAIL",
        "purpose": (
            "Implementation validation only; no real-catalog scientific inference."
        ),
        "seed": seed,
        "configuration": {
            "count_per_run": count_per_run,
            "posterior_samples": posterior_samples,
            "hyperposterior_draws": hyperposterior_draws,
            "generated_injections_per_run": generated_injections_per_run,
            "tolerance": tolerance,
        },
        "events": [
            {
                "event_id": event.event_id,
                "run": event.run,
                "true_mass_1_source": event.metadata["true_mass_1_source"],
            }
            for event in events
        ],
        "selection_campaigns": {
            run: campaign.metadata for run, campaign in selections.items()
        },
        "models": models,
        "comparisons": {
            "delta_peak_minus_smooth": delta_peak_smooth,
            "delta_peak_minus_break": delta_peak_break,
        },
        "acceptance": {
            "peak_beats_smooth_by_more_than_2_log_units": delta_peak_smooth > 2.0,
            "joint_equals_prequential": all(
                item["joint_prequential_absolute_difference"] <= tolerance
                for item in models.values()
            ),
        },
    }
    if output_dir is not None:
        output_dir = Path(output_dir)
        write_json_atomic(output_dir / "toy_validation.json", report)
        rows = ["event_id,run,true_mass_1_source"]
        rows.extend(
            f"{item['event_id']},{item['run']},{item['true_mass_1_source']:.10g}"
            for item in report["events"]
        )
        (output_dir / "toy_events.csv").write_text("\n".join(rows) + "\n")
    if not passed:
        raise RuntimeError(
            "Toy predictive validation failed. Inspect the emitted report before "
            "using the statistical layer."
        )
    return report

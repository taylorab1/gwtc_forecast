"""Explicit extraction when population-coordinate priors have ALREADY been evaluated.

This adapter deliberately does not infer labels, priors, or injection weights
from column names. It is suitable for producing candidate contracts for review.
"""
from __future__ import annotations
from pathlib import Path
from typing import Mapping
import h5py
import numpy as np
from ..statistics.objects import EventPosterior

def event_from_structured_hdf5(path: Path, *, dataset: str, columns: Mapping[str, str], event_id: str, run: str, log_prior_in_target_coordinates: np.ndarray, analysis_label: str, prior_reference: str, log_sample_weights=None):
    if not analysis_label.strip() or not prior_reference.strip() or (not dataset.strip()):
        raise ValueError('explicit dataset, analysis label, and prior reference required')
    with h5py.File(path, 'r') as f:
        node = f[dataset]
        if not isinstance(node, h5py.Dataset) or node.dtype.names is None or node.ndim != 1:
            raise ValueError('expected a one-dimensional structured posterior dataset')
        if set(columns.values()) - set(node.dtype.names):
            raise KeyError('some mapped columns are absent')
        samples = {target: np.asarray(node.fields(native)[()], float) for target, native in columns.items()}
    return EventPosterior(event_id, run, samples, log_prior_in_target_coordinates, metadata={'source_path': str(Path(path).resolve()), 'dataset': dataset, 'analysis_label': analysis_label, 'prior_reference': prior_reference, 'coordinates': list(columns), 'validated': False, 'posterior_rows': 'unqualified'}, log_sample_weights=log_sample_weights)

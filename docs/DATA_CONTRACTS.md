# Analysis-ready data contracts

The public release files are immutable raw inputs. Release-specific adapters
must write compact HDF5 contracts under `GWTC_PROCESSED_ROOT`; downstream
statistics consume only those contracts.

## Processed event (`gwtc_forecast.processed_event.v2`)

```text
attributes:
  schema
  event_id
  run
  metadata_json
samples/
  <one one-dimensional dataset per population coordinate>
log_pe_prior
log_sample_weights
```

`log_sample_weights` is normalized and records how the stored rows represent
the event posterior. Equal-weight public products store `-log(K)` for every
row. It must not be confused with the later population importance ratio.
Readers remain backward compatible with `processed_event.v1`; absence of the
weight dataset in a v1 file is interpreted as equal weight.

Required metadata includes source record, filename, MD5, frozen PE label,
waveform analysis, whether the source product was originally equal weight, the
source weight field when applicable, prior adapter version, cosmology,
coordinate/Jacobian convention, and code commit.

## Processed selection (`gwtc_forecast.processed_selection.v1`)

```text
attributes:
  schema
  run
  metadata_json
samples/
  <one one-dimensional dataset per population coordinate>
log_draw_density
log_base_weight
```

Required metadata includes the generated count, found-mask definition, FAR or
search threshold, run mask, release mixture definition, source checksum,
normalization derivation, validation points, and code commit.

The contract can be read either in full or through
`iter_selection_contract_chunks`. Chunking does not renormalize individual
chunks: each stored `log_base_weight` retains the global campaign
normalization. The streamed likelihood accumulator combines `sum(w)` and
`sum(w^2)` in log space so that efficiency and ESS match the in-memory result.

## Processed hyperposterior (`gwtc_forecast.processed_hyperposterior.v1`)

```text
attributes:
  schema
  model_name
  metadata_json
samples/
  <one one-dimensional dataset per released hyperparameter>
log_weights
```

Required metadata includes the source release role, posterior/result filename,
source checksum, released model implementation, prior definition, whether the
draws were originally equal-weight, and the adapter/code commit.

## Immutability rule

An adapter writes to a temporary file and atomically renames it. A changed
mapping creates a new versioned contract rather than silently modifying a
previously scored object.

# Official release schema notes for the first Codex campaign

These notes distill the public release documentation already included in the
pilot manifest. They narrow the discovery problem, but they do not open the
production-scoring gate.

## O4 PE summary tables

The GWTC-4.1 and GWTC-5 parameter-estimation releases include one lightweight
HDF5 summary table and one combined HDF5 file per event. The four index columns
that connect them are:

```text
result_label
  Unique row label, documented as {gw_name}-{result_samples_key}.

gw_name
  Catalog event identifier.

result_file_name
  Combined event HDF5 containing all released analyses for that event.

result_samples_key
  Key/analysis label inside the combined event HDF5.
```

The repository reads these fields without Astropy or GWPy through:

```bash
make pe-index
```

Outputs:

```text
$GWTC_RESULTS_ROOT/pilot/inventory/pe_release_index.json
$GWTC_RESULTS_ROOT/pilot/inventory/o4a_pe_candidates.csv
$GWTC_RESULTS_ROOT/pilot/inventory/o4b_pe_candidates.csv
```

The official tutorial demonstrates that event files can contain labels such as
`C00:IMRPhenomXPHM-SpinTaylor`, `C00:IMRPhenomXPNR`, `C00:NRSur7dq4`, and
`C00:SEOBNRv5PHM`, with availability varying by event. It also demonstrates a
waveform-priority filter only as an example. This repository does **not** turn
that example into a production label policy.

The next audit must establish whether the GWTC population analysis used a
specific waveform, an event-dependent priority, a released mixed posterior, or
a dedicated population sample product. It must then reconstruct the exact PE
prior in the same coordinates as the population density.

## O4a+O4b sensitivity table

The public sensitivity HDF5 has root attributes including:

```text
gps_start
gps_end
total_analysis_time
total_generated
num_accepted
searches
date
```

The documented data table is a one-dimensional compound dataset named
`events`. Relevant source-population columns include:

```text
mass1_source
mass2_source
q
z
spin1_magnitude
spin1_polar_angle
spin1_azimuthal_angle
spin2_magnitude
spin2_polar_angle
spin2_azimuthal_angle
weights
time_geocenter
```

For a mass-spin-redshift target population, the release example constructs the
log draw density from:

```text
lnpdraw_mass1_source
+ lnpdraw_mass2_source_GIVEN_mass1_source
+ lnpdraw_z
+ lnpdraw_spin1_magnitude
+ lnpdraw_spin1_polar_angle
+ lnpdraw_spin1_azimuthal_angle
+ lnpdraw_spin2_magnitude
+ lnpdraw_spin2_polar_angle
+ lnpdraw_spin2_azimuthal_angle
```

Search-specific FAR fields follow the pattern `<search>_far`; the release
example uses the minimum FAR across searches and illustrates a threshold of one
per year. The combined-campaign example has the form

```text
sum(weights[found] * exp(log_p_population - log_p_draw)) / total_generated
```

The official observing intervals documented with the release are:

```text
O4a: 1368975618 <= time_geocenter < 1389456018
O4b: 1396969218 <= time_geocenter < 1422118818
```

Run-specific normalization is deliberately still unresolved. Splitting rows by
`time_geocenter` is not by itself proof that the denominator should be a simple
run subtotal, because the release uses wall-time mixture weights and records
month-level generation information. `make selection-schema` confirms the
actual fields but does not create production contracts.

## Released GWTC-3 population products

The two archives are executable analysis products rather than generic tables.
After extraction, run:

```bash
make discover
```

The discovery report only enumerates safe candidate files. Codex must prefer
released executable model definitions and metadata over manually transcribing
paper equations. Arbitrary pickle files must not be loaded until their source
and class dependencies are understood.

## Gate rule

The field inventory above reduces ambiguity. It does not replace:

1. one frozen event-label policy;
2. exact PE-prior reconstruction and Jacobian tests;
3. O4a/O4b selection normalization derivation;
4. fixed-hyperparameter comparison with an independent implementation;
5. released-model normalization and reproduction tests.

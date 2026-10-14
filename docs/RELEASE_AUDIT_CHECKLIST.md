> Inherited v0.4 release-reference notes. Verify against the actual pinned release; follow the v0.5 SCIENCE_CHARTER and REAL_DATA_WORKFLOW for current scope.

# Release-audit checklist

## Event PE files

- [ ] Enumerate every PESummary analysis label.
- [ ] Identify the release-recommended mixed/default label from official files.
- [ ] Record waveform family and sampling coordinates.
- [ ] Confirm source-frame and detector-frame mass fields.
- [ ] Identify luminosity-distance/redshift conversion and cosmology.
- [ ] Reconstruct the exact PE prior in population coordinates.
- [ ] Unit-test every Jacobian using numerical transformations.
- [ ] Compare direct prior evaluation with released prior samples/configuration.
- [ ] Freeze the label and adapter in `config/pe_mapping.toml`.
- [ ] Write a processed event contract with source checksum.

## O4 injections

- [ ] Identify the main injection table and all mixture components.
- [ ] Separate O4a and O4b with documented masks.
- [ ] Freeze the search threshold/found definition.
- [ ] Identify generated counts and any clipping correction.
- [ ] Evaluate the injection draw density in the population coordinates.
- [ ] Derive `log_base_weight` from release definitions, not guesswork.
- [ ] Compare \(\xi_r(\Lambda)\) with GWPopulation/release code at fixed points.
- [ ] Bootstrap injections and report Monte Carlo uncertainty.
- [ ] Freeze mappings in `config/injection_mapping.toml`.
- [ ] Write one processed selection contract per run.

## Released GWTC-3 models

- [ ] Locate the actual posterior result files without loading arbitrary pickle.
- [ ] Record equal/unequal posterior weights.
- [ ] Recover all mass, mass-ratio, redshift, and spin nuisance definitions.
- [ ] Use released executable model code where possible.
- [ ] Test normalization at fixed hyperparameters.
- [ ] Reproduce one released mass-spectrum panel or numerical table.
- [ ] Freeze adapters in `config/released_model_mapping.toml`.

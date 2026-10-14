SHELL := /bin/bash
ENV_NAME := gwtc_forecast
RUN := ./scripts/run_in_env.sh

.PHONY: help setup bootstrap status plan download verify extract prepare inventory \
        deep-inventory pe-index selection-schema discover mapping-status first-look smoke science-smoke \
        readiness power-gate test lint audit lock codex-preflight jupyter clean-pyc

help:
	@printf '%s\n' \
	  'student-setup    Minimal local learning environment (recommended first)' \
	  'feature-demo     Full synthetic train/freeze/predict run; set OUTPUT=/tmp/new-attempt' \
	  'feature-calibration  Repeated synthetic training and SBC reference' \
	  'study-audit      Explain deliberately missing real-study inputs' \
	  'setup            Optional full inherited science environment' \
	  'bootstrap        Create the guarded external data tree' \
	  'status           Check mount, paths, free space, and repository size' \
	  'plan             Resolve the pinned Zenodo pilot without downloading' \
	  'download         Download only the pilot files' \
	  'verify           Verify sizes, MD5 checksums, and HDF5 signatures' \
	  'extract          Safely extract marked archives on the external disk' \
	  'prepare          verify + extract + inventory' \
	  'inventory        Inspect downloaded releases and HDF5 structure' \
	  'deep-inventory   Inventory plus PESummary analysis-label discovery' \
	  'pe-index         Index candidate PE labels from lightweight summary tables' \
	  'selection-schema Audit documented O4 injection fields and unresolved normalization' \
	  'discover         Find candidate released hyperposterior files' \
	  'mapping-status   Report unresolved production mappings' \
	  'first-look       Inventory + PE/selection audits + mock validation + readiness' \
	  'science-smoke    Run deterministic predictive-statistics validation' \
	  'readiness        Write the machine-readable production-readiness report' \
		  'power-gate       Evaluate completed detected-space mock score files' \
	  'test             Run offline tests' \
	  'lint             Run Ruff checks' \
	  'audit            Reject data/large artifacts in the repository' \
	  'lock             Record exact Conda/Pip runtime state' \
	  'codex-preflight  Run all safe gates before Codex development' \
	  'jupyter          Launch JupyterLab with external caches and temporary files'

setup:
	./scripts/setup_conda.sh

bootstrap:
	$(RUN) gwtc-forecast bootstrap

status:
	$(RUN) gwtc-forecast status

plan:
	$(RUN) gwtc-forecast plan

download:
	$(RUN) gwtc-forecast download

verify:
	$(RUN) gwtc-forecast verify --offline

extract:
	$(RUN) gwtc-forecast extract --offline

prepare: verify extract inventory

inventory:
	$(RUN) gwtc-forecast inventory

deep-inventory:
	$(RUN) gwtc-forecast inventory --deep-pe

pe-index:
	$(RUN) gwtc-forecast pe-index

selection-schema:
	$(RUN) gwtc-forecast inspect-selection

discover:
	$(RUN) gwtc-forecast discover-hyperposteriors

mapping-status:
	$(RUN) gwtc-forecast mapping-status

first-look:
	./scripts/first_scientific_look.sh

science-smoke smoke:
	$(RUN) gwtc-forecast science-smoke

readiness:
	$(RUN) gwtc-forecast readiness

power-gate:
	@test -n "$(SCORES)" || (echo 'Usage: make power-gate SCORES=/path/to/scores.json' >&2; exit 2)
	$(RUN) gwtc-forecast power-gate "$(SCORES)"

test:
	$(RUN) pytest -q

lint:
	$(RUN) ruff check src tests

audit:
	$(RUN) gwtc-forecast audit-repo

lock:
	./scripts/lock_environment.sh

codex-preflight: status test lint audit science-smoke mapping-status readiness
	@echo 'Codex preflight complete.'

jupyter:
	./scripts/launch_jupyter.sh

clean-pyc:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

.PHONY: student-setup feature-demo feature-calibration study-audit
student-setup:
	./scripts/setup_student.sh

feature-demo:
	$(RUN) gwtc-forecast feature-demo $(if $(OUTPUT),--output $(OUTPUT),)

feature-calibration:
	$(RUN) gwtc-forecast feature-calibration $(if $(OUTPUT),--output $(OUTPUT),)

study-audit:
	$(RUN) gwtc-forecast study-audit

PYTHON ?= python3
MPLCONFIGDIR ?= $(CURDIR)/work/mpl
XDG_CACHE_HOME ?= $(CURDIR)/work/cache
IQM_RESULT ?= results/iqm/static_blindspot_5000/blindspot_minimal.json
IQM_SHOTS ?= 5000
export MPLCONFIGDIR XDG_CACHE_HOME

.PHONY: runtime-dirs check-algebra ideal noisy analyze plots periodic-dynamics periodic-mitigation periodic-iqm-plot demo reproduce-all test iqm-dry-run iqm-freeze iqm-approve iqm-periodic-audit-offline iqm-periodic-audit iqm-periodic-freeze iqm-periodic-approve iqm-periodic-dry-run bundle

runtime-dirs:
	mkdir -p $(MPLCONFIGDIR) $(XDG_CACHE_HOME)

check-algebra:
	$(PYTHON) scripts/check_algebra.py

ideal:
	$(PYTHON) scripts/run_ideal.py --shots 20000

noisy:
	$(PYTHON) scripts/run_noisy.py --shots 20000

analyze:
	$(PYTHON) scripts/analyze_results.py --iqm $(IQM_RESULT)

plots: runtime-dirs
	$(PYTHON) scripts/make_blindspot_plots.py

periodic-dynamics: runtime-dirs
	$(PYTHON) scripts/run_periodic_ideal.py
	$(PYTHON) scripts/make_periodic_dynamics_plot.py

periodic-mitigation: runtime-dirs
	$(PYTHON) scripts/run_periodic_exact_mitigation.py
	$(PYTHON) scripts/make_periodic_mitigation_plot.py

periodic-iqm-plot: runtime-dirs
	$(PYTHON) scripts/make_periodic_iqm_hardware_plot.py \
		--input results/processed/periodic_iqm_joint_readout_5000_seed1.csv \
		--job-id 019f750b-2c82-7371-a66a-eaf4263c222a \
		--output-stem fig08_periodic_iqm_hardware_readout_5000_seed1 \
		--title "IQM Emerald periodic readout: 5000-shot hardware repeat"

demo: check-algebra ideal noisy analyze plots

reproduce-all: test demo periodic-dynamics periodic-mitigation periodic-iqm-plot

bundle:
	$(PYTHON) scripts/create_github_bundle.py

test: runtime-dirs
	$(PYTHON) -m pytest -q

iqm-dry-run:
	$(PYTHON) scripts/run_iqm.py --shots $(IQM_SHOTS) --batch blindspot-minimal

iqm-freeze:
	$(PYTHON) scripts/freeze_iqm_blindspot_candidate.py --shots $(IQM_SHOTS) \
		--outdir results/iqm/emerald_blindspot_candidate_$(IQM_SHOTS)

iqm-approve:
	$(PYTHON) scripts/approve_iqm_candidate.py

iqm-periodic-audit-offline:
	$(PYTHON) scripts/audit_periodic_iqm_candidate.py --offline

iqm-periodic-audit:
	$(PYTHON) scripts/audit_periodic_iqm_candidate.py

iqm-periodic-freeze:
	$(PYTHON) scripts/freeze_iqm_periodic_candidate.py --shots 1000

iqm-periodic-approve:
	$(PYTHON) scripts/approve_iqm_candidate.py results/iqm/emerald_periodic_candidate/readiness_manifest.json

iqm-periodic-dry-run:
	$(PYTHON) scripts/run_iqm_periodic.py

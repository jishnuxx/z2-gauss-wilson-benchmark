PYTHON ?= python3
MPLCONFIGDIR ?= $(CURDIR)/work/mpl
XDG_CACHE_HOME ?= $(CURDIR)/work/cache
IQM_RESULT ?= results/iqm/static_blindspot_5000/blindspot_minimal.json
IQM_SHOTS ?= 5000
export MPLCONFIGDIR XDG_CACHE_HOME

.PHONY: runtime-dirs check-algebra ideal noisy analyze plots periodic-dynamics periodic-depth-reduction periodic-mitigation periodic-iqm-plot iqm-mitigate-offline iqm-periodic-matter-mitigate iqm-device-comparison demo reproduce-all test iqm-dry-run iqm-freeze iqm-approve iqm-response-freeze iqm-response-approve iqm-response-dry-run iqm-periodic-audit-offline iqm-periodic-audit iqm-periodic-freeze iqm-periodic-approve iqm-periodic-dry-run iqm-periodic-matter-freeze iqm-periodic-matter-approve iqm-periodic-matter-dry-run iqm-sirius-periodic-matter-freeze iqm-sirius-periodic-matter-approve iqm-sirius-periodic-matter-dry-run iqm-emerald-periodic-matter-scan-freeze iqm-emerald-periodic-matter-scan-approve iqm-emerald-periodic-matter-scan-dry-run iqm-emerald-periodic-matter-repeat-freeze iqm-sirius-periodic-matter-repeat-freeze iqm-emerald-periodic-matter-repeat-approve iqm-emerald-periodic-matter-repeat-dry-run iqm-sirius-periodic-matter-repeat-approve iqm-sirius-periodic-matter-repeat-dry-run bundle

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

periodic-depth-reduction: runtime-dirs
	$(PYTHON) scripts/run_periodic_depth_reduction_audit.py
	$(PYTHON) scripts/make_periodic_depth_reduction_plot.py

periodic-mitigation: runtime-dirs
	$(PYTHON) scripts/run_periodic_exact_mitigation.py
	$(PYTHON) scripts/make_periodic_mitigation_plot.py

periodic-iqm-plot: runtime-dirs
	$(PYTHON) scripts/make_periodic_iqm_hardware_plot.py \
		--input results/processed/periodic_iqm_joint_readout_5000_seed1.csv \
		--job-id 019f750b-2c82-7371-a66a-eaf4263c222a \
		--output-stem fig08_periodic_iqm_hardware_readout_5000_seed1 \
		--title "IQM Emerald periodic readout: 5000-shot hardware repeat"

iqm-mitigate-offline: runtime-dirs
	$(PYTHON) scripts/mitigate_iqm_readout.py
	$(PYTHON) scripts/make_iqm_mitigation_plot.py

iqm-periodic-matter-mitigate: runtime-dirs
	$(PYTHON) scripts/mitigate_iqm_periodic_matter_readout.py
	$(PYTHON) scripts/make_periodic_matter_hardware_plot.py

iqm-device-comparison: runtime-dirs
	$(PYTHON) scripts/analyze_iqm_device_comparison.py
	$(PYTHON) scripts/make_iqm_device_comparison_plot.py

demo: check-algebra ideal noisy analyze plots

reproduce-all: test demo periodic-dynamics periodic-depth-reduction periodic-mitigation periodic-iqm-plot iqm-mitigate-offline iqm-periodic-matter-mitigate iqm-device-comparison

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

iqm-response-freeze:
	$(PYTHON) scripts/freeze_iqm_blindspot_response_candidate.py --shots $(IQM_SHOTS)

iqm-response-approve:
	$(PYTHON) scripts/approve_iqm_candidate.py \
		results/iqm/emerald_blindspot_response_candidate_$(IQM_SHOTS)/readiness_manifest.json

iqm-response-dry-run:
	$(PYTHON) scripts/run_iqm_blindspot_response.py --shots $(IQM_SHOTS) \
		--manifest results/iqm/emerald_blindspot_response_candidate_$(IQM_SHOTS)/readiness_manifest.json

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

iqm-periodic-matter-freeze:
	$(PYTHON) scripts/freeze_iqm_periodic_matter_candidate.py --shots $(IQM_SHOTS)

iqm-periodic-matter-approve:
	$(PYTHON) scripts/approve_iqm_candidate.py \
		results/iqm/emerald_periodic_matter_candidate_$(IQM_SHOTS)/readiness_manifest.json

iqm-periodic-matter-dry-run:
	$(PYTHON) scripts/run_iqm_periodic_matter.py --shots $(IQM_SHOTS) \
		--manifest results/iqm/emerald_periodic_matter_candidate_$(IQM_SHOTS)/readiness_manifest.json

iqm-sirius-periodic-matter-freeze:
	$(PYTHON) scripts/freeze_iqm_sirius_periodic_matter_scan.py --shots $(IQM_SHOTS) \
		--outdir results/iqm/sirius_periodic_matter_scan_candidate_$(IQM_SHOTS)

iqm-sirius-periodic-matter-approve:
	$(PYTHON) scripts/approve_iqm_sirius_periodic_matter_scan.py \
		results/iqm/sirius_periodic_matter_scan_candidate_$(IQM_SHOTS)/readiness_manifest.json

iqm-sirius-periodic-matter-dry-run:
	$(PYTHON) scripts/run_iqm_sirius_periodic_matter_scan.py --shots $(IQM_SHOTS) \
		--manifest results/iqm/sirius_periodic_matter_scan_candidate_$(IQM_SHOTS)/readiness_manifest.json

iqm-emerald-periodic-matter-scan-freeze:
	$(PYTHON) scripts/freeze_iqm_emerald_periodic_matter_scan.py --shots $(IQM_SHOTS) \
		--outdir results/iqm/emerald_periodic_matter_scan_candidate_$(IQM_SHOTS)

iqm-emerald-periodic-matter-scan-approve:
	$(PYTHON) scripts/approve_iqm_emerald_periodic_matter_scan.py \
		results/iqm/emerald_periodic_matter_scan_candidate_$(IQM_SHOTS)/readiness_manifest.json

iqm-emerald-periodic-matter-scan-dry-run:
	$(PYTHON) scripts/run_iqm_emerald_periodic_matter_scan.py --shots $(IQM_SHOTS) \
		--manifest results/iqm/emerald_periodic_matter_scan_candidate_$(IQM_SHOTS)/readiness_manifest.json

iqm-emerald-periodic-matter-repeat-freeze:
	$(PYTHON) scripts/freeze_iqm_emerald_periodic_matter_scan.py --shots $(IQM_SHOTS) \
		--fixed-layout 17,24,16,10,8,7,9,3 --replicate-label repeat2 \
		--outdir results/iqm/emerald_periodic_matter_scan_repeat2_$(IQM_SHOTS)

iqm-sirius-periodic-matter-repeat-freeze:
	$(PYTHON) scripts/freeze_iqm_sirius_periodic_matter_scan.py --shots $(IQM_SHOTS) \
		--replicate-label repeat2 \
		--outdir results/iqm/sirius_periodic_matter_scan_repeat2_$(IQM_SHOTS)

iqm-emerald-periodic-matter-repeat-approve:
	$(PYTHON) scripts/approve_iqm_emerald_periodic_matter_scan.py \
		--replicate-label repeat2 \
		results/iqm/emerald_periodic_matter_scan_repeat2_$(IQM_SHOTS)/readiness_manifest.json

iqm-emerald-periodic-matter-repeat-dry-run:
	$(PYTHON) scripts/run_iqm_emerald_periodic_matter_scan.py --shots $(IQM_SHOTS) \
		--replicate-label repeat2 \
		--manifest results/iqm/emerald_periodic_matter_scan_repeat2_$(IQM_SHOTS)/readiness_manifest.json \
		--output-json results/iqm/emerald_periodic_matter_hardware/emerald_periodic_matter_scan_repeat2_$(IQM_SHOTS).json \
		--output-csv results/processed/emerald_periodic_matter_hardware_scan_repeat2_$(IQM_SHOTS).csv

iqm-sirius-periodic-matter-repeat-approve:
	$(PYTHON) scripts/approve_iqm_sirius_periodic_matter_scan.py \
		--replicate-label repeat2 \
		results/iqm/sirius_periodic_matter_scan_repeat2_$(IQM_SHOTS)/readiness_manifest.json

iqm-sirius-periodic-matter-repeat-dry-run:
	$(PYTHON) scripts/run_iqm_sirius_periodic_matter_scan.py --shots $(IQM_SHOTS) \
		--replicate-label repeat2 \
		--manifest results/iqm/sirius_periodic_matter_scan_repeat2_$(IQM_SHOTS)/readiness_manifest.json \
		--output-json results/iqm/sirius_periodic_matter_hardware/sirius_periodic_matter_scan_repeat2_$(IQM_SHOTS).json \
		--output-csv results/processed/sirius_periodic_matter_hardware_scan_repeat2_$(IQM_SHOTS).csv

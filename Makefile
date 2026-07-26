SHELL := bash

.PHONY: convert
convert:
	@echo "Converting rules..."
	./scripts/convert_rules.py && prettier --write ./Clash

.PHONY: resample
resample:
	@echo "Resampling icons..."
	./scripts/resample.sh

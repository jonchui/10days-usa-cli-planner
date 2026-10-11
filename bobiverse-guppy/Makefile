.PHONY: test tag testset eval eval-prompt sft all

test:
	python -m pytest -q tests

tag:
	python scripts/categorize.py

testset:
	python scripts/select_testset.py

eval:            ## rules baseline, no API key needed
	python scripts/run_eval.py --backend rules

eval-prompt:     ## prompt-based Guppy, needs ANTHROPIC_API_KEY
	python scripts/run_eval.py --backend prompt:guppy/prompts/$(VERSION).md --judge

sft:
	python training/build_sft.py

all: tag testset test eval

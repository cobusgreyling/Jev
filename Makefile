.PHONY: demo-offline demo examples test lint secret-scan

demo-offline: demo

demo:
	./run.sh

examples:
	python3 examples/01_noul.py
	python3 examples/02_choice.py
	python3 examples/03_score.py
	python3 examples/04_parallel_fanout.py
	python3 examples/05_confidence_routing.py
	python3 examples/06_composite_scoring.py
	python3 examples/07_guardrails.py

test:
	python3 -m pytest -q

secret-scan:
	python3 scripts/secret_scan.py

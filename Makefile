.PHONY: setup test lint format run-test-discovery

setup:
	bash setup_jules.sh

test:
	python3 -m unittest discover tests

lint:
	flake8 src tests

format:
	black src tests

run-test-discovery:
	python3 main.py discover --no-telegram

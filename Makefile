.PHONY: test lint

test:
	PYTHONPATH=src:tests python3 -m unittest discover -s tests -v

lint:
	uvx ruff check src tests

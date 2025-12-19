
.PHONY: lint-check

lint-check:
	/home/aleksandr/.local/bin/ruff check .
	/home/aleksandr/.local/bin/mypy .

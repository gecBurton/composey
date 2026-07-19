format:
	uv run ruff format .
	uv run ruff check . --fix --extend-select I

test:
	uv run pytest
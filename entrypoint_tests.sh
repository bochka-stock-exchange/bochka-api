#!/bin/sh
exec uv run pytest -v --durations=0 --cov --cov-report=xml "$@"

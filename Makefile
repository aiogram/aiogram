.DEFAULT_GOAL := help

base_python := python3.7
py := poetry run
python := $(py) python

.PHONY: help
help:
	@echo "======================================================================================="
	@echo "                                  aiogram build tools                                  "
	@echo "======================================================================================="
	@echo "Environment:"
	@echo "    install: Install development dependencies"
	@echo ""
	@echo "Code quality:"
	@echo "    isort: Run isort tool"
	@echo "    black: Run black tool"
	@echo "    flake8: Run flake8 tool"
	@echo "    mypy: Run mypy tool"
	@echo "    lint: Run isort, black, flake8 and mypy tools"
	@echo ""
	@echo "Tests:"
	@echo "    test: Run tests"
	@echo ""
	@echo "Documentation:"
	@echo "	   docs: Build docs"
	@echo "	   docs-serve: Serve docs for local development"
	@echo ""
	@echo ""

# =================================================================================================
# Environment
# =================================================================================================

.PHONY: install
install:
	$(base_python) -m pip install --user -U poetry
	poetry install

.PHONY: clean
clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -rf *.egg-info
	rm -f .coverage
	rm -f .coverage.*
	rm -rf {build,dist,site,.cache,.pytest_cache,.mypy_cache}


# =================================================================================================
# Code quality
# =================================================================================================

.PHONY: isort
isort:
	$(py) isort -rc aiogram tests

.PHONY: black
black:
	$(py) black aiogram tests

.PHONY: flake8
flake8:
	$(py) flake8 aiogram tests

.PHONY: mypy
mypy:
	$(py) mypy aiogram tests

.PHONY: lint
lint: isort black flake8 mypy


# =================================================================================================
# Tests
# =================================================================================================

.PHONY: test
test:
	$(py) pytest --cov=aiogram --cov-config .coveragerc tests/


# =================================================================================================
# Docs
# =================================================================================================

.PHONY: docs
docs:
	$(py) mkdocs build

.PHONY: docs-serve
docs-serve:
	$(py) mkdocs serve

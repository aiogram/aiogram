.DEFAULT_GOAL := help

python := python3.7

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

.PHONY: install
install:
	$(python) -m pip install --user -U poetry
	poetry install

.PHONY: isort
isort:
	poetry run isort -rc aiogram tests

.PHONY: black
black:
	poetry run black aiogram tests

.PHONY: flake8
flake8:
	poetry run flake8 aiogram tests

.PHONY: mypy
mypy:
	poetry run mypy aiogram tests

.PHONY: lint
lint: isort black flake8 mypy


.PHONY: test
test:
	poetry run pytest --cov=aiogram --cov-config .coveragerc tests/ -sq

.PHONY: docs
docs:
	mkdocs build

.PHONY: docs-serve
docs-serve:
	mkdocs serve

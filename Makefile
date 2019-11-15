.DEFAULT_GOAL := help

python := python3.7

.PHONY: help
help:
	@echo "======================================================================================="
	@echo "                                  aiogram build tools                                  "
	@echo "======================================================================================="
	@echo "Commands list:"
	@echo "    install: Install development dependencies"
	@echo "    isort: Run isort tool"
	@echo "    black: Run black tool"
	@echo "    flake8: Run flake8 tool"
	@echo "    mypy: Run mypy tool"
	@echo "    lint: Run isort, black, flake8 and mypy tools"
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

.DEFAULT_GOAL := help

base_python := python3
py := poetry run
python := $(py) python

package_dir := aiogram
tests_dir := tests
scripts_dir := scripts
examples_dir := examples
code_dir := $(package_dir) $(tests_dir) $(scripts_dir) $(examples_dir)
reports_dir := reports

redis_connection := redis://localhost:6379

.PHONY: help
help:
	@echo "======================================================================================="
	@echo "                                  aiogram build tools                                  "
	@echo "======================================================================================="
	@echo "Environment:"
	@echo "    help: Show this message"
	@echo "    install: Install development dependencies"
	@echo "    clean: Delete temporary files"
	@echo ""
	@echo "Code quality:"
	@echo "    lint: Lint code by isort, black, flake8 and mypy tools"
	@echo "    reformat: Reformat code by isort and black tools"
	@echo ""
	@echo "Tests:"
	@echo "    test: Run tests"
	@echo "    test-coverage: Run tests with HTML reporting (results + coverage)"
	@echo "    test-coverage-report: Open coverage report in default system web browser"
	@echo ""
	@echo "Documentation:"
	@echo "    docs: Build docs"
	@echo "    docs-serve: Serve docs for local development"
	@echo "    docs-prepare-reports: Move all HTML reports to docs dir"
	@echo ""
	@echo "Project"
	@echo "    build: Run tests build package and docs"
	@echo ""

# =================================================================================================
# Environment
# =================================================================================================

.PHONY: install
install:
	poetry install -E fast -E redis -E proxy -E i18n -E docs --remove-untracked
	$(py) pre-commit install

.PHONY: clean
clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -rf `find . -name .pytest_cache`
	rm -rf *.egg-info
	rm -f report.html
	rm -f .coverage
	rm -rf {build,dist,site,.cache,.mypy_cache,reports}

# =================================================================================================
# Code quality
# =================================================================================================

.PHONY: lint
lint:
	$(py) isort --check-only $(code_dir)
	$(py) black --check --diff $(code_dir)
	$(py) flake8 $(code_dir)
	$(py) mypy $(package_dir)
	# TODO: wemake-python-styleguide

.PHONY: reformat
reformat:
	$(py) black $(code_dir)
	$(py) isort $(code_dir)

# =================================================================================================
# Tests
# =================================================================================================
.PHONY: test-run-services
test-run-services:
	@#docker-compose -f tests/docker-compose.yml -p aiogram3-dev up -d

.PHONY: test
test: test-run-services
	$(py) pytest --cov=aiogram --cov-config .coveragerc tests/ --redis $(redis_connection)

.PHONY: test-coverage
test-coverage: test-run-services
	mkdir -p $(reports_dir)/tests/
	$(py) pytest --cov=aiogram --cov-config .coveragerc --html=$(reports_dir)/tests/index.html tests/ --redis $(redis_connection)
	$(py) coverage html -d $(reports_dir)/coverage

.PHONY: test-coverage-view
test-coverage-view:
	$(py) coverage html -d $(reports_dir)/coverage
	python -c "import webbrowser; webbrowser.open('file://$(shell pwd)/reports/coverage/index.html')"

# =================================================================================================
# Docs
# =================================================================================================

.PHONY: docs-serve
docs-serve:
	rm -rf docs/_build
	$(py) sphinx-autobuild --watch aiogram/ docs/ docs/_build/

# =================================================================================================
# Project
# =================================================================================================

.PHONY: build
build: clean flake8-report mypy-report test-coverage
	mkdir -p site/simple
	poetry build
	mv dist site/simple/aiogram

.PHONY: bump
bump:
	poetry version $(args)
	$(python) scripts/bump_versions.py

.PHONY: towncrier-build
towncrier-build:
	towncrier build --yes

.PHONY: towncrier-draft
towncrier-draft:
	towncrier build --draft

.PHONY: towncrier-draft-github
towncrier-draft-github:
	mkdir -p dist
	towncrier build --draft | pandoc - -o dist/release.md

.PHONY: prepare-release
prepare-release: bump towncrier-build

.PHONY: release
release:
	git add .
	git commit -m "Release $(shell poetry version -s)"
	git tag v$(shell poetry version -s)

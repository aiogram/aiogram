.DEFAULT_GOAL := lint

package_dir := aiogram
tests_dir := tests
scripts_dir := scripts
examples_dir := examples
code_dir := $(package_dir) $(tests_dir) $(scripts_dir) $(examples_dir)
reports_dir := reports

redis_connection := redis://localhost:6379

# =================================================================================================
# Environment
# =================================================================================================

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
	rm -rf {build,dist,site,.cache,.mypy_cache,.ruff_cache,reports}

# =================================================================================================
# Code quality
# =================================================================================================

.PHONY: lint
lint:
	isort --check-only $(code_dir)
	black --check --diff $(code_dir)
	ruff $(package_dir)
	mypy $(package_dir)

.PHONY: reformat
reformat:
	black $(code_dir)
	isort $(code_dir)

# =================================================================================================
# Tests
# =================================================================================================
.PHONY: test-run-services
test-run-services:
	@#docker-compose -f tests/docker-compose.yml -p aiogram3-dev up -d

.PHONY: test
test: test-run-services
	pytest --cov=aiogram --cov-config .coveragerc tests/ --redis $(redis_connection)

.PHONY: test-coverage
test-coverage: test-run-services
	mkdir -p $(reports_dir)/tests/
	pytest --cov=aiogram --cov-config .coveragerc --html=$(reports_dir)/tests/index.html tests/ --redis $(redis_connection)
	coverage html -d $(reports_dir)/coverage

.PHONY: test-coverage-view
test-coverage-view:
	coverage html -d $(reports_dir)/coverage
	python -c "import webbrowser; webbrowser.open('file://$(shell pwd)/reports/coverage/index.html')"

# =================================================================================================
# Docs
# =================================================================================================

locales := uk_UA
locale_targets := $(addprefix docs-serve-, $(locales))
locales_pot := _build/gettext
docs_dir := docs

docs-gettext:
	hatch run docs:bash -c 'cd $(docs_dir) && make gettext'
	hatch run docs:bash -c 'cd $(docs_dir) && sphinx-intl update -p $(locales_pot) $(addprefix -l , $(locales))'
.PHONY: docs-gettext

docs-serve:
	hatch run docs:sphinx-autobuild --watch aiogram/ --watch CHANGELOG.rst --watch README.rst docs/ docs/_build/ $(OPTS)
.PHONY: docs-serve

$(locale_targets): docs-serve-%:
	$(MAKE) docs-serve OPTS="-D language=$(subst docs-serve-,,$@)"
.PHONY: $(locale_targets)

# =================================================================================================
# Project
# =================================================================================================

.PHONY: build
build: clean
	hatch build

.PHONY: bump
bump:
	hatch version $(args)
	python scripts/bump_versions.py

.PHONY: towncrier-build
towncrier-build:
	hatch run docs:towncrier build --yes

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
	git tag v$(shell hatch version -s)


butcher_version := 0.1.23

butcher-install:
	pip install -U git+ssh://git@github.com/aiogram/butcher.git@v$(butcher_version)
.PHONY: butcher-install

butcher:
	butcher parse
	butcher refresh
	butcher apply all
.PHONY: butcher

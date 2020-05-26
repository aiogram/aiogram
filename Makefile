.DEFAULT_GOAL := help

base_python := python3
py := poetry run
python := $(py) python

reports_dir := reports

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
	@echo "    isort: Run isort tool"
	@echo "    black: Run black tool"
	@echo "    flake8: Run flake8 tool"
	@echo "    flake8-report: Run flake8 with HTML reporting"
	@echo "    mypy: Run mypy tool"
	@echo "    mypy-report: Run mypy tool with HTML reporting"
	@echo "    lint: Run isort, black, flake8 and mypy tools"
	@echo ""
	@echo "Tests:"
	@echo "    test: Run tests"
	@echo "    test-coverage: Run tests with HTML reporting (results + coverage)"
	@echo "    test-coverage-report: Open coverage report in default system web browser"
	@echo ""
	@echo "Documentation:"
	@echo "	   docs: Build docs"
	@echo "	   docs-serve: Serve docs for local development"
	@echo "    docs-prepare-reports: Move all HTML reports to docs dir"
	@echo ""
	@echo "Project"
	@echo "    build: Run tests build package and docs"
	@echo ""



# =================================================================================================
# Environment
# =================================================================================================

install:
	$(base_python) -m pip install --user -U poetry
	poetry install

clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -rf `find . -name .pytest_cache`
	rm -rf *.egg-info
	rm -f .coverage
	rm -f report.html
	rm -f .coverage.*
	rm -rf {build,dist,site,.cache,.mypy_cache,reports}


# =================================================================================================
# Code quality
# =================================================================================================

isort:
	$(py) isort -rc aiogram tests

black:
	$(py) black aiogram tests

flake8:
	$(py) flake8 aiogram test

flake8-report:
	mkdir -p $(reports_dir)/flake8
	$(py) flake8 --format=html --htmldir=$(reports_dir)/flake8 aiogram test

mypy:
	$(py) mypy aiogram

mypy-report:
	$(py) mypy aiogram --html-report $(reports_dir)/typechecking

lint: isort black flake8 mypy

# =================================================================================================
# Tests
# =================================================================================================

test:
	$(py) pytest --cov=aiogram --cov-config .coveragerc tests/

test-coverage:
	mkdir -p $(reports_dir)/tests/
	$(py) pytest --cov=aiogram --cov-config .coveragerc --html=$(reports_dir)/tests/index.html tests/


test-coverage-report:
	$(py) coverage html -d $(reports_dir)/coverage

test-coverage-view:
	$(py) coverage html -d $(reports_dir)/coverage
	python -c "import webbrowser; webbrowser.open('file://$(shell pwd)/reports/coverage/index.html')"

# =================================================================================================
# Docs
# =================================================================================================

docs:
	$(py) mkdocs build

docs-serve:
	$(py) mkdocs serve

docs-copy-reports:
	mv $(reports_dir)/* site/reports

# =================================================================================================
# Project
# =================================================================================================

build: clean flake8-report mypy-report test-coverage docs docs-copy-reports
	mkdir -p site/simple
	poetry build
	mv dist site/simple/aiogram

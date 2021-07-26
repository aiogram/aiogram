VENV_NAME := venv
PYTHON := $(VENV_NAME)/bin/python
AIOGRAM_VERSION := $(shell $(PYTHON) -c "import aiogram;print(aiogram.__version__)")

RM := rm -rf

mkvenv:
	virtualenv $(VENV_NAME)
	$(PYTHON) -m pip install -r requirements.txt

clean:
	find . -name '*.pyc' -exec $(RM) {} +
	find . -name '*.pyo' -exec $(RM) {} +
	find . -name '*~' -exec $(RM)  {} +
	find . -name '__pycache__' -exec $(RM) {} +
	$(RM) build/ dist/ docs/build/ .tox/ .cache/ .pytest_cache/ *.egg-info

tag:
	@echo "Add tag: '$(AIOGRAM_VERSION)'"
	git tag v$(AIOGRAM_VERSION)

build:
	$(PYTHON) setup.py sdist bdist_wheel

upload:
	twine upload dist/*

release:
	make clean
	make test
	make build
	make tag
	@echo "Released aiogram $(AIOGRAM_VERSION)"

full-release:
	make release
	make upload

install:
	$(PYTHON) setup.py install

test:
	tox

summary:
	cloc aiogram/ tests/ examples/ docs/ setup.py

docs: docs/source/*
	cd docs && $(MAKE) html

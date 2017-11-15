VENV_NAME := venv
PYTHON := $(VENV_NAME)/bin/python

mkvenv:
	virtualenv $(VENV_NAME)
	$(PYTHON) -m pip install -r requirements.txt

clean:
	find . -name '*.pyc' -exec rm --force {} +
	find . -name '*.pyo' -exec rm --force {} +
	find . -name '*~' -exec rm --force  {} +
	rm --force --recursive build/
	rm --force --recursive dist/
	rm --force --recursive *.egg-info

tag:
	AIOGRAM_VERSION := $(shell $(PYTHON) -c "import aiogram;print(aiogram.__version__)")
	@echo "Add tag: '$(AIOGRAM_VERSION)'"
	git tag v$(AIOGRAM_VERSION)

build:
	$(PYTHON) setup.py sdist bdist_wheel

upload:
	twine upload dist/*

release:
	AIOGRAM_VERSION := $(shell $(PYTHON) -c "import aiogram;print(aiogram.__version__)")
	make clean
	make tag
	make build
	@echo "Released aiogram $(AIOGRAM_VERSION)"

full-release:
	make release
	make upload


make install:
	$(PYTHON) setup.py install

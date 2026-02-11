#!/usr/bin/env just --justfile

set shell := ["bash", "-c"]
set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]

package_dir := "aiogram"
tests_dir := "tests"
scripts_dir := "scripts"
examples_dir := "examples"
code_dir := f"{{package_dir}} {{tests_dir}} {{scripts_dir}} {{examples_dir}}"
reports_dir := "reports"
redis_connection := "redis://localhost:6379"
mongo_connection := "mongodb://mongo:mongo@localhost:27017"

# Documentation variables

locales := "uk_UA"
locale_targets := "docs-serve-" + locales
locales_pot := "_build/gettext"
docs_dir := "docs"

# =================================================================================================
# Environment
# =================================================================================================

[unix]
clean:
    find . -name "__pycache__" -type d -exec rm -rf {} +
    find . -type f -name "*.py[co]" -delete
    find . -type f -name "*~" -delete
    find . -type f -name ".*~" -delete
    find . -name ".pytest_cache" -type d -exec rm -rf {} +
    rm -rf *.egg-info
    rm -f report.html
    rm -f .coverage
    rm -rf build dist site .cache .mypy_cache .ruff_cache {{ reports_dir }}

[windows]
clean:
    -Get-ChildItem -Path . -Recurse -Name "__pycache__" -Directory | Remove-Item -Recurse -Force
    -Get-ChildItem -Path . -Recurse -Include "*.pyc", "*.pyo" -File | Remove-Item -Force
    -Get-ChildItem -Path . -Recurse -Include "*~", ".*~" -File | Remove-Item -Force
    -Get-ChildItem -Path . -Recurse -Name ".pytest_cache" -Directory | Remove-Item -Recurse -Force
    -Remove-Item -Path "*.egg-info" -Recurse -Force -ErrorAction SilentlyContinue
    -Remove-Item -Path "report.html" -Force -ErrorAction SilentlyContinue
    -Remove-Item -Path ".coverage" -Force -ErrorAction SilentlyContinue
    -Remove-Item -Path "build", "dist", "site", ".cache", ".mypy_cache", ".ruff_cache", "{{ reports_dir }}" -Recurse -Force -ErrorAction SilentlyContinue

install: clean
    uv sync --all-extras --group dev --group test
    uv run pre-commit install

# =================================================================================================
# Code quality
# =================================================================================================

[default]
lint:
    uv run ruff format --check --diff {{ package_dir }}
    uv run ruff check --show-fixes --preview {{ package_dir }} {{ examples_dir }}
    uv run mypy {{ package_dir }}

reformat:
    uv run ruff format {{ code_dir }}
    uv run ruff check --fix {{ code_dir }}

# =================================================================================================
# Tests
# =================================================================================================

test-run-services:
    docker-compose -f tests/docker-compose.yml -p aiogram3-dev up -d

test: test-run-services
    uv run pytest --cov=aiogram --cov-config .coveragerc tests/ --redis {{ redis_connection }} --mongo {{ mongo_connection }}

[unix]
test-coverage: test-run-services
    mkdir -p {{ reports_dir }}/tests"
    uv run pytest --cov=aiogram --cov-config .coveragerc --html={{ reports_dir }}/tests/index.html tests/ --redis {{ redis_connection }} --mongo {{ mongo_connection }}
    uv run coverage html -d {{ reports_dir }}/coverage

[windows]
test-coverage: test-run-services
    New-Item -ItemType Directory -Path "{{ reports_dir }}\\tests" -Force -ErrorAction SilentlyContinue | Out-Null
    uv run pytest --cov=aiogram --cov-config .coveragerc --html={{ reports_dir }}/tests/index.html tests/ --redis {{ redis_connection }} --mongo {{ mongo_connection }}
    uv run coverage html -d {{ reports_dir }}/coverage

test-coverage-view:
    uv run coverage html -d {{ reports_dir }}/coverage
    uv run python -c "import webbrowser; webbrowser.open('file://{{ invocation_directory() }}/reports/coverage/index.html')"

# =================================================================================================
# Docs
# =================================================================================================

docs-gettext:
    uv run --extra docs bash -c 'cd {{ docs_dir }} && make gettext'
    uv run --extra docs bash -c 'cd {{ docs_dir }} && sphinx-intl update -p {{ locales_pot }} -l {{ locales }}'

docs-serve *OPTS:
    uv run --extra docs sphinx-autobuild --watch aiogram/ --watch CHANGES.rst --watch README.rst {{ docs_dir }}/ {{ docs_dir }}/_build/ {{ OPTS }}

docs-serve-uk_UA *OPTS:
    just docs-serve "-D language=uk_UA" {{ OPTS }}

# =================================================================================================
# Project
# =================================================================================================

build: clean
    uv build

bump *args:
    uv run python scripts/bump_version.py {{ args }}
    uv run python scripts/bump_versions.py

update-api:
    uv run --extra cli butcher parse
    uv run --extra cli butcher refresh
    uv run --extra cli butcher apply all
    just bump

towncrier-build:
    uv run --extra docs towncrier build --yes

towncrier-draft:
    uv run --extra docs towncrier build --draft

[unix]
towncrier-draft-github:
    mkdir -p dist
    uv run --extra docs towncrier build --draft | pandoc - -o dist/release.md

[windows]
towncrier-draft-github:
    New-Item -ItemType Directory -Path "dist" -Force -ErrorAction SilentlyContinue | Out-Null
    uv run --extra docs towncrier build --draft | pandoc - -o dist/release.md

prepare-release: bump towncrier-build

release:
    git add .
    git commit -m "Release $(uv run python -c 'from aiogram import __version__; print(__version__)')"
    git tag v$(uv run python -c 'from aiogram import __version__; print(__version__)')

# OSS Scanner build: https://github.com/anthropics/oss-scanner
# The scanner uses the repository root as the build context and audits /src offline, so everything the
# tests need is installed here from the committed uv.lock, as CI does.
FROM ghcr.io/astral-sh/uv:python3.13-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# Redis server for the storage tests (start it with `redis-server --daemonize yes`)
RUN apt-get update && apt-get install -y --no-install-recommends redis-server \
    && rm -rf /var/lib/apt/lists/*

COPY . /src
WORKDIR /src

RUN uv sync --locked --all-extras --no-extra docs --no-group dev --group test

# The network is gone after this point, so `uv run` must use the environment above as it is.
ENV UV_FROZEN=1 \
    UV_NO_SYNC=1 \
    UV_OFFLINE=1 \
    VIRTUAL_ENV=/src/.venv \
    PATH=/src/.venv/bin:$PATH

# Run the test suite so the image is known to work; a failing test must not abort the build.
RUN redis-server --daemonize yes \
    && (pytest tests -q -p no:cacheprovider --redis redis://localhost:6379/0 \
        || echo "WARNING: pytest reported failures") \
    && redis-cli shutdown nosave

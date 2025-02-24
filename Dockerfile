FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /bot

ENV UV_FROZEN=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --no-editable

ENTRYPOINT ["uv", "run", "--no-dev", "-m", "app"]

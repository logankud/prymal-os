#!/bin/bash
set -e

# Install / sync all Python dependencies via uv
uv sync --frozen

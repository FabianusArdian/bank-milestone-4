FROM python:3.12-slim AS base
# Install Poetry
RUN pip install --no-cache-dir poetry
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1
ENV PATH="$PATH:$POETRY_HOME/bin"

FROM base AS build
WORKDIR /app
# Install dependency from pyproject.toml
COPY pyproject.toml poetry.lock .  # Ensure poetry.lock is present
RUN poetry install --only=main --no-root
COPY . .

# Runtime stage
FROM base AS runtime
WORKDIR /app
COPY --from=build /app /app
ENV PATH="/app/.venv/bin:$PATH"
RUN echo "source /app/.venv/bin/activate" >> /etc/profile.d/venv.sh
EXPOSE 5000

CMD ["flask", "--app", "app", "run", "--host", "0.0.0.0"]
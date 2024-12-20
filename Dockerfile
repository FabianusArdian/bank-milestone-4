FROM python:3.12-slim-bookworm AS base
# Install Poetry
RUN pip install poetry
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1
ENV PATH="$PATH:$POETRY_HOME/bin"

FROM base AS build
WORKDIR /app
# Install dependency from pyproject.toml
COPY pyproject.toml .
RUN  poetry lock --no-update && poetry install --only=main
COPY . .

# Runtime stage
FROM base AS runtime
WORKDIR /app
COPY --from=build /app /app
ENV PATH="/app/.venv/bin:$PATH"
RUN echo "source /app/.venv/bin/activate" >> /etc/profile.d/venv.sh
EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
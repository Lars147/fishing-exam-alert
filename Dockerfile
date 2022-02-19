FROM python:3

ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_VERSION=1.1.13

USER root
RUN apt-get update \
    && apt-get --yes install apt-utils \
    && apt-get --yes install curl

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH "/root/.local/bin:$PATH"

# install dependencies
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-ansi --no-dev

COPY . .
ENV PYTHONPATH /

ENTRYPOINT ["/entrypoint.sh"]
RUN chmod 755 /entrypoint.sh

CMD ["python3", "-u", "/fishing_exam_alert/main.py"]
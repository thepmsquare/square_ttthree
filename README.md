# square_ttthree

> 📌 versioning: see [CHANGELOG.md](./CHANGELOG.md).
> 📌 coding standards: see [CODING_STANDARDS.md](./CODING_STANDARDS.md).

## about

api and training scripts for my ttthree (tic-tac-toe game).

## installation

```shell
pip install square_ttthree[all]
```

## usage

### configuration

update the settings in `config.ini` and `config.testing.ini` to match your environment (database url, logging, etc).

### running the service

```shell
python square_ttthree/main.py
```

## testing

to run test cases with execution and coverage reports:

```shell
uv run pytest --cov=square_ttthree --cov-report=term-missing
```

## code quality

to check linting errors and format code using ruff:

```shell
uv run ruff check .
uv run ruff format .
```

## env

- python>=3.12.0

> feedback is appreciated. thank you!

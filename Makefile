.RECIPEPREFIX := >
.DEFAULT_GOAL := help

help:  ## show targets
>@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

guard:  ## fail fast if venv is not active
>@test -n "$$VIRTUAL_ENV" || { echo "ERROR: venv not active — run: source .venv/Scripts/activate"; exit 1; }

check: guard  ## syntax-check all python — run before every docker build
>python -m compileall -q src data tests && echo "syntax OK"

up:  ## start full stack
>docker compose up -d --build
>@until docker compose exec -T postgres pg_isready -U insureai >/dev/null 2>&1; do sleep 1; done
>@echo "API ready: http://localhost:8000/docs"

down:  ## stop and drop volumes (resets DB)
>docker compose down -v

build:  ## rebuild images
>docker compose build

seed: guard  ## generate synthetic data -> postgres
>python -m data.synthetic.generate --policies 20000 --fraud-rate 0.08 --load-db

seed-small: guard
>python -m data.synthetic.generate --policies 2000 --fraud-rate 0.10 --load-db

demo: up seed  ## full demo stack
>@echo "Stack up. Run: make token — then open http://localhost:3000"

test: guard  ## unit + integration
>python -m pytest tests -q

lint: guard
>ruff check src tests data

token: guard  ## mint a dev JWT (officer role)
>@curl -s -X POST localhost:8000/auth/dev-token -H 'Content-Type: application/json' -d '{"sub":"demo-officer","roles":["officer"]}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])"

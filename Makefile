.DEFAULT_GOAL := help
.PHONY: help up down seed seed-small demo test lint

help:  ## show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

up:  ## start postgres + redpanda + api
	docker compose up -d --build
	@until docker compose exec -T postgres pg_isready -U insureai >/dev/null 2>&1; do sleep 1; done
	@echo "API ready: http://localhost:8000/docs"

down:  ## stop and remove volumes (resets DB)
	docker compose down -v

seed:  ## generate synthetic data + load into postgres
	python -m data.synthetic.generate --policies 20000 --fraud-rate 0.08 --load-db

seed-small:  ## fast seed for tests/CI
	python -m data.synthetic.generate --policies 2000 --fraud-rate 0.10 --load-db

demo: up seed  ## full demo stack
	@echo "Try: curl localhost:8000/claims/CLM-2026-000100"

test:  ## unit + integration
	python -m pytest tests -q

lint:
	ruff check src tests data

token:  ## mint a dev JWT (officer role) for API calls
	@curl -s -X POST localhost:8000/auth/dev-token -H "Content-Type: application/json" \
	  -d '{"sub":"demo-officer","roles":["officer"]}' \
	  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])"

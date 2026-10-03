.PHONY: up seed train eval demo test lint

up:
	docker compose up -d

seed:
	python -m data.synthetic.generate

train:
	python -m insureai.ml.train_fraud

eval:
	python evals/run.py

demo:
	@echo "See docs/demo-script.md"

test:
	pytest tests -q

lint:
	ruff check src tests evals data

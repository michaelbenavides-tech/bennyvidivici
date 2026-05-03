.PHONY: dev test lint down

dev:
	docker compose up --build

down:
	docker compose down

test:
	docker compose run --rm backend pytest
	docker compose run --rm frontend npm test -- --run

lint:
	docker compose run --rm backend sh -c "black --check app tests && isort --check-only app tests && mypy app"
	docker compose run --rm frontend npm run lint

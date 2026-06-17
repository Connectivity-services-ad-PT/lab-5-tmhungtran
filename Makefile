.PHONY: compose-up compose-down logs

compose-up:
	docker compose up -d --build

compose-down:
	docker compose down

logs:
	docker compose logs -f

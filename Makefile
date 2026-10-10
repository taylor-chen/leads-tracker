.DEFAULT_GOAL := help
.PHONY: help up down reset logs ps create-user test test-backend test-frontend lint lint-backend

NODE_RUN = docker run --rm -v "$(CURDIR)/frontend:/app" -v /app/node_modules -w /app node:22-alpine

help:  ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

up:  ## Build and start the full stack in the background
	docker compose up --build -d

down:  ## Stop the stack (keeps data)
	docker compose down

reset:  ## Stop the stack and delete all data (database + uploaded resumes)
	docker compose down -v

logs:  ## Tail logs (all services, or one with SERVICE=backend)
	docker compose logs -f $(SERVICE)

ps:  ## Show service status
	docker compose ps

create-user:  ## Add an attorney: make create-user EMAIL=... PASSWORD=... NAME="..."
	@test -n "$(EMAIL)" -a -n "$(PASSWORD)" -a -n "$(NAME)" || \
		(echo 'Usage: make create-user EMAIL=jane@example.com PASSWORD=secret123 NAME="Jane Doe"' && exit 1)
	docker compose exec backend python -m app.cli create-user \
		--email "$(EMAIL)" --password "$(PASSWORD)" --name "$(NAME)"

test: test-backend test-frontend  ## Run all tests and checks

test-backend:  ## Run backend tests (pytest) in a container
	docker compose build backend
	docker compose run --rm --no-deps backend pytest

test-frontend:  ## Type-check and lint the frontend in a throwaway Node container
	$(NODE_RUN) sh -c "npm install --no-audit --no-fund && npm run typecheck && npm run lint"

lint: lint-backend  ## Lint backend and frontend
	$(NODE_RUN) sh -c "npm install --no-audit --no-fund && npm run lint"

lint-backend:  ## Lint the backend (ruff)
	docker compose build backend
	docker compose run --rm --no-deps backend ruff check .

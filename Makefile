.PHONY: up down reset logs test test-backend lint-backend typecheck-frontend lint-frontend

up:            ## Build and start the full stack
	docker compose up --build -d

down:          ## Stop the stack (keeps data)
	docker compose down

reset:         ## Stop the stack and delete all data (DB + uploaded resumes)
	docker compose down -v

logs:          ## Tail logs from all services
	docker compose logs -f

test: test-backend typecheck-frontend  ## Run all automated checks

test-backend:  ## Run backend tests (pytest) in a container
	docker compose build backend
	docker compose run --rm --no-deps backend pytest

lint-backend:
	docker compose run --rm --no-deps backend ruff check .

typecheck-frontend:  ## Type-check and lint the frontend in a throwaway Node container
	docker run --rm -v "$(CURDIR)/frontend:/app" -v /app/node_modules -w /app node:22-alpine \
		sh -c "npm install --no-audit --no-fund && npm run typecheck && npm run lint"

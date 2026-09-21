.PHONY: install migrate seed backend frontend

install:
	cd backend && poetry install
	cd frontend && pnpm install

migrate:
	cd backend && poetry run python manage.py migrate

seed:
	cd backend && poetry run python manage.py seed

backend:
	cd backend && poetry run python manage.py runserver 127.0.0.1:8000

frontend:
	cd frontend && pnpm dev

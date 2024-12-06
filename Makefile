all: up

up:
		@docker-compose -f ./docker-compose.yml up --build

down:
		@docker-compose -f ./docker-compose.yml down

re: down up

logs:
		@docker-compose logs -f

.PHONY: up down re logs

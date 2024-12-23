all: up

up:
		@hostname | tr -d "\n" > back/.hostname.txt
		@hostname | tr -d "\n" > nginx/.hostname.txt
		@docker-compose -f ./docker-compose.yml up --build

down:
		@docker-compose -f ./docker-compose.yml down

re: down up

logs:
		@docker-compose logs -f

.PHONY: up down re logs

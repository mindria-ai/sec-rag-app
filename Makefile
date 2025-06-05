APP_NAME=sec-rag-app
PORT=8501

# Use local Docker or docker-compose depending on preference

build:
	docker build -t $(APP_NAME) .

run:
	docker run --env-file .env -p $(PORT):$(PORT) $(APP_NAME)

up:
	docker-compose up --build

down:
	docker-compose down

shell:
	docker exec -it $$(docker ps -qf "ancestor=$(APP_NAME)") /bin/bash

logs:
	docker logs $$(docker ps -qf "ancestor=$(APP_NAME)")

clean:
	docker system prune -f

WEB_CONTAINER=docker-compose -f local.yml run --rm django

# Containers
web:
	$(WEB_CONTAINER) $(c)

# Docker
docker-compose:
	docker-compose $(foreach file, $($(COMPOSE_FILES)), -f $(file)) $(command)

up:
	@make docker-compose command="up -d --build"

down:
	@make docker-compose command="down --remove-orphans"

# Django
manage:
	@make web c="python manage.py $(c)"

### Migrations
mm:
	@make manage c=makemigrations
migrate:
	@make manage c=migrate

### Fixtures
_load_fixture:
	@make manage c="loaddata $(fixture)"
load_fixtures:
	@make _load_fixture fixture="version_control_services.json"

# Code quality
flake8:
	$(WEB_CONTAINER) flake8

black:
	$(WEB_CONTAINER) black .

black_check:
	$(WEB_CONTAINER) black --check .

tests:
	$(WEB_CONTAINER) pytest --cov-config=.coveragerc --cov=./

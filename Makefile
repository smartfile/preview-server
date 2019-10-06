all: test

.PHONY: build
build:
	docker build -f Dockerfile -t btimby/preview-base .
	docker build -f Dockerfile.soffice -t btimby/preview-soffice .
	docker build -f Dockerfile.preview -t btimby/preview-server .

.PHONY: build-cache
build-cache:
	docker pull btimby/preview-base || true
	docker pull btimby/preview-soffice || true
	docker pull btimby/preview-server || true
	docker build --cache-from btimby/preview-base -f Dockerfile -t btimby/preview-base .
	docker build --cache-from btimby/preview-soffice -f Dockerfile.soffice -t btimby/preview-soffice .
	docker build --cache-from btimby/preview-server -f Dockerfile.preview -t btimby/preview-server .

Pipfile: Pipfile.lock
	pipenv install --dev
	touch Pipfile

.PHONY: test
test: Pipfile
	pipenv run python3 test.py

.PHONY: small
small: build
	docker-compose -f small.yml -p preview-small up


.PHONY: medium
medium: build
	docker-compose -f medium.yml -p preview-medium up --scale soffice-server=3


.PHONY: large
large: build
	docker-compose -f large.yml -p preview-large up \
		--scale soffice-server=5 --scale preview-server=2

.PHONY: dev
dev: build
	docker-compose -f dev.yml -p preview-dev up --scale soffice-server=3


.PHONY: shell
shell:
	docker run -ti btimby/preview-server bash

.PHONY: login
login:
	echo "${DOCKER_PASSWORD}" | docker login -u "${DOCKER_USERNAME}" --password-stdin

.PHONY: tag
tag:
	docker tag btimby/preview-base btimby/preview-base:latest
	docker tag btimby/preview-server btimby/preview-server:latest
	docker tag btimby/preview-soffice btimby/preview-soffice:latest

.PHONY: tag
tag-travis: tag
	docker tag btimby/preview-base btimby/preview-base:${TRAVIS_COMMIT}
	docker tag btimby/preview-server btimby/preview-server:${TRAVIS_COMMIT}
	docker tag btimby/preview-soffice btimby/preview-soffice:${TRAVIS_COMMIT}

.PHONY: push
push: login
	docker push btimby/preview-base:latest
	docker push btimby/preview-server:latest
	docker push btimby/preview-soffice:latest

.PHONY: push-travis
push-travis: push
	docker push btimby/preview-base:${TRAVIS_COMMIT}
	docker push btimby/preview-server:${TRAVIS_COMMIT}
	docker push btimby/preview-soffice:${TRAVIS_COMMIT}

PYTHON ?= python3

.PHONY: test check build preview publish hugo-preflight
hugo-preflight:
	./scripts/check-hugo

test: hugo-preflight
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v

check:
	./scripts/check-site

build: hugo-preflight
	hugo --gc --minify --cleanDestinationDir

preview: hugo-preflight
	hugo server --disableFastRender

publish: hugo-preflight
	./scripts/publish-site

# Base image to use for constructing environment
V_BASE ?= 3.3.0
BUILDER_IMG ?= opendatacube/geobase-builder:$(V_BASE)

# Docker we are building
DKR_IMG ?= opendatacube/odc-test-runner:latest

# Absolute path for this directory
WK := $(shell pwd)

# Absolute path to code
CODE := $(shell readlink -f ..)
TTY := $(shell bash -c "tty -s && echo '-t' || true")

dkr := docker run --rm -i $(TTY) \
        -v $(CODE):/code \
        -v $(WK):/wk \
        -e TZ=Australia/Sydney \
        $(BUILDER_IMG)

all: dkr

download: .build/download.info.txt
compile: .build/compile.info.txt

.build/prepared.txt:
	@mkdir -p .cache/pip .build
	@date > $@

.build/download.info.txt: requirements.txt constraints.txt nobinary.txt .build/prepared.txt
	@$(dkr) env-build-tool download requirements.txt constraints.txt ./wheels --find-links ./wheels
	@date > $@

.build/compile.info.txt: .build/download.info.txt
	@$(dkr) env-build-tool compile ./wheels
	@date > $@

bash: .build/prepared.txt
	@$(dkr) bash

bash-runner:
	@docker run --rm -ti \
    -v $(CODE):/code \
    -v $(WK):/wk \
    $(DKR_IMG) bash

dbg: .build/prepared.txt
	@echo "dkr: " $(dkr)
	@$(dkr) python3 --version

dkr: .build/compile.info.txt Dockerfile
	DOCKER_BUILDKIT=1 docker build \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  --build-arg V_BASE=$(V_BASE) \
  --cache-from $(DKR_IMG) \
  -t $(DKR_IMG) \
  -f Dockerfile ..

dkr-no-deps:
	DOCKER_BUILDKIT=1 docker build \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  --build-arg V_BASE=$(V_BASE) \
  --cache-from $(DKR_IMG) \
  -t $(DKR_IMG) \
  -f Dockerfile ..

run-test:
	@docker run --rm \
    -v $(CODE):/code \
    $(DKR_IMG) pytest --timeout=30 .

clean:
	rm -f .build/download.info.txt .build/compile.info.txt
	@echo "Keeping wheels and pip cache"

.PHONY: dbg all clean download compile dkr run-test dkr dkr-no-deps bash bash-runner

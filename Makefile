# Variables
PACKAGE_NAME = cs6457_milestone_packaging
DIST_DIR = dist
WHEEL_FILE = $(shell ls $(DIST_DIR)/*.whl 2>/dev/null | head -n 1)

install:
	poetry update

build:
	poetry build

clean:
	rm -rf $(DIST_DIR)

package-install: clean build
	@if [ -z "$(WHEEL_FILE)" ]; then \
		echo "No wheel file found. Run 'make build' first."; \
	else \
		pip uninstall -y $(PACKAGE_NAME) || true; \
		pip install --force-reinstall $(WHEEL_FILE); \
	fi

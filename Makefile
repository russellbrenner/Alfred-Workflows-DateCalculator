# Alfred Date Calculator — Makefile

.PHONY: test lint format build pack clean install-dev

install-dev:
	pip install -e ".[dev]"

test:
	pytest tests/ --cov=src --cov-report=term-missing -v

lint:
	ruff check src/ tests/
	ruff format --check src/ tests/

format:
	ruff format src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf build/ dist/ .coverage htmlcov/ *.egg-info

build: clean
	@echo "Building workflow bundle..."
	mkdir -p build/DateCalculator
	@# Copy entry points to root
	cp src/dcalc.py build/DateCalculator/
	cp src/anniversary_list.py build/DateCalculator/
	cp src/set_anniversary.py build/DateCalculator/
	cp src/date_format_list.py build/DateCalculator/
	cp src/set_date_format.py build/DateCalculator/
	cp src/time_format_list.py build/DateCalculator/
	cp src/set_time_format.py build/DateCalculator/
	cp src/date_time_format_list.py build/DateCalculator/
	cp src/set_date_time_format.py build/DateCalculator/
	cp src/show_date_format.py build/DateCalculator/
	cp src/show_time_format.py build/DateCalculator/
	@# Copy source package exactly as imported by entry points
	cp -r src build/DateCalculator/src
	@# Copy static assets
	cp info.plist build/DateCalculator/
	cp icon.png build/DateCalculator/
	cp README.md build/DateCalculator/
	@# Install dependencies
	pip install -t build/DateCalculator python-dateutil arrow pypeg2
	@# Clean up
	find build/DateCalculator -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find build/DateCalculator -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf build/DateCalculator/bin/ build/DateCalculator/*.dist-info/ build/DateCalculator/*.egg-info/
	rm -rf build/DateCalculator/pypeg2/test/ build/DateCalculator/pypeg2/*.egg-info/
	rm -rf build/DateCalculator/pip/
	@echo "Build complete: build/DateCalculator/"

pack: build
	cd build/DateCalculator && zip -r ../../DateCalculator.alfredworkflow .
	@echo "Package created: DateCalculator.alfredworkflow"

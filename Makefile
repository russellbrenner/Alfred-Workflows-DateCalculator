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
	@# Copy source packages
	cp -r src/core build/DateCalculator/core
	cp -r src/alfred build/DateCalculator/alfred
	@# Copy static assets
	cp info.plist build/DateCalculator/
	cp icon.png build/DateCalculator/
	cp README.md build/DateCalculator/
	@# Install dependencies
	pip install -t build/DateCalculator python-dateutil arrow pypeg2
	@# Clean up
	find build/DateCalculator -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find build/DateCalculator -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf build/DateCalculator/bin/ build/DateCalculator/*.dist-info/
	@echo "Build complete: build/DateCalculator/"

pack: build
	cd build && zip -r ../DateCalculator.alfredworkflow DateCalculator/
	@echo "Package created: DateCalculator.alfredworkflow"

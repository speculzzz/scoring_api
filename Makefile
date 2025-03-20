all: pytest coverage

.PHONY: utest
utest:
	@echo "==================="
	@echo "= Start unittests ="
	@echo "==================="
	@python -m unittest -vv

.PHONY: start
start:
	@echo "===================="
	@echo "= Start the server ="
	@echo "===================="
	@python api.py

.PHONY: pytest
pytest:
	@echo "================"
	@echo "= Start pytest ="
	@echo "================"
	@pytest -vv tests/

.PHONY: coverage
coverage:
	@echo "=================="
	@echo "= Tests coverage ="
	@echo "=================="
	@pytest -s --cov --cov-report html --cov-fail-under 75

all: utest

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

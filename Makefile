
.PHONY: bootstrap-venv
bootstrap-venv:
	python3 -m venv .venv
	.venv/bin/pip install build-harness
	.venv/bin/build-harness install


.PHONY: install-pre-commit-hooks
install-pre-commit-hooks:
	pre-commit \
	  install \
	    --install-hooks

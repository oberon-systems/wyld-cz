# Temporary files location for .bashrc
TEMP := $(shell mktemp /tmp/oberon-systems-bashrc.XXXXXX)

# UV Binaries location
UV = $(HOME)/.local/bin/uv

# UV Environment Params
UV_VENV_CLEAR=1
VIRTUAL_ENV=venv

# Pre-commit configs
PRE_COMMIT_HOME = $(PWD)/.pre-commit
export PRE_COMMIT_HOME

# Export env params
export UV_VENV_CLEAR
export VIRTUAL_ENV

.install-uv:
	@curl -LsSf https://astral.sh/uv/install.sh | sh
	@$(UV) venv --relocatable --python python3.12
	@$(UV) pip install -r requirements.txt

enable:
	@if [ ! -f $(UV) ] || [ ! -f ".venv/bin/python" ]; then \
  		echo "WARNING: nor uv binaries or installed virtual env found!"; \
  		echo "Installing uv and creating virtual env..."; \
  		$(MAKE) .install-uv; \
  	fi
	@echo "Starting Oberon Systems Developing Environment..."
	@cat $(HOME)/.bashrc $(HOME)/.local/bin/env > $(TEMP)
	@echo "source $(PWD)/.venv/bin/activate" >> $(TEMP)
	@echo 'export PRE_COMMIT_HOME="$(PWD)/.pre-commit"' >> $(TEMP)
	@echo '' >> $(TEMP)
	@echo '# Auto-install pre-commit hooks' >> $(TEMP)
	@echo 'if [ ! -d .pre-commit ]; then' >> $(TEMP)
	@echo '  echo "Pre-commit not found, installing..."' >> $(TEMP)
	@echo '  pre-commit install-hooks' >> $(TEMP)
	@echo '  pre-commit install' >> $(TEMP)
	@echo 'fi' >> $(TEMP)
	@cat motd
	@/usr/bin/env bash --init-file $(TEMP)
	@rm -v $(TEMP)

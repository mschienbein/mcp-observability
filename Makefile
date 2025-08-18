# Root conveniences

# Ensure Node deps once
.PHONY: ui-install
ui-install:
	npm --prefix ui install

# Run Vite dev server from repo root
.PHONY: ui-dev
ui-dev: ui-install
	npm --prefix ui run dev

# Build UI
.PHONY: ui-build
ui-build: ui-install
	npm --prefix ui run build

# Preview built UI
.PHONY: ui-preview
ui-preview: ui-install
	npm --prefix ui run preview

# Python MCP clients (requires `uv` or fallback to python)
.PHONY: mcp-tools-client mcp-feedback-client langfuse-test
mcp-tools-client:
	uv run clients/mcp_client.py tools || python3 clients/mcp_client.py tools

mcp-feedback-client:
	uv run clients/mcp_client.py feedback || python3 clients/mcp_client.py feedback

# Test Langfuse integration
langfuse-test:
	uv run python clients/langfuse_test.py || python3 clients/langfuse_test.py

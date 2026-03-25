.PHONY: server kill-server tunnel server-local test lint logs

server:
	PYTHONUNBUFFERED=1 uv run python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload --log-level debug 2>&1 | tee /tmp/opsiq.log

kill-server:
	@lsof -ti :8000 | xargs kill -9 2>/dev/null && echo "Killed server on :8000" || echo "No server running on :8000"

logs:
	tail -f /tmp/opsiq.log

tunnel:
	ngrok http 8000

server-local:
	@ngrok http 8000 & \
	sleep 2 && \
	NGROK_URL=$$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys,json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])") && \
	echo "" && \
	echo "Ngrok URL:      $$NGROK_URL" && \
	echo "Slack endpoint: $$NGROK_URL/integrations/slack/events" && \
	echo "" && \
	uv run python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload; \
	kill $$(lsof -ti:4040) 2>/dev/null || true

test:
	uv run pytest

lint:
	uv run ruff check .

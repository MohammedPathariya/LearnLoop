# LearnLoop load tests

The Locust scenario exercises the deterministic study-history path so the local
result measures LearnLoop and SQLite rather than OpenAI latency:

- read-heavy: history, search, and all dashboard analytics endpoints
- write-heavy: `POST /quiz_results`, followed by `GET /quiz_results/:id`

Generation endpoints are intentionally excluded. They require an external
OpenAI key and would measure provider availability and model latency as well as
the application. They need a separate, explicitly configured provider test.

## Run locally

From the repository root, install the pinned load-test dependency:

```bash
python3.11 -m pip install -r load_tests/requirements.txt
```

Start the backend in another terminal with a load-test database and the
production-style local server:

```bash
SUPABASE_DB_URI=sqlite:////tmp/learnloop-load-test.db \
  gunicorn --chdir backend --bind 127.0.0.1:5050 \
  --workers 4 --threads 2 --timeout 30 wsgi:app
```

Run 500 users with a short ramp and a bounded duration:

```bash
locust -f load_tests/locustfile.py --headless \
  --host http://127.0.0.1:5050 \
  --users 500 --spawn-rate 50 --run-time 2m \
  --csv docs/load-tests/locust-500-users-gunicorn \
  --html docs/load-tests/locust-500-users-gunicorn.html \
  --only-summary
```

The CSV and HTML files are the raw report artifacts. Save each run under a
unique prefix. The Markdown report must record total requests, failures and
failure rate, requests per second, p50, p95, the exact command, server
configuration, and observed SQLite lock errors. Do not replace a failed run
with a successful rerun in the same report.

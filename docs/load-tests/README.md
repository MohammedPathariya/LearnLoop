# Load-test catalog

These reports are the durable Day 5 load-test evidence set. Raw Locust CSV and
HTML files remain beside each Markdown interpretation. Failed runs are retained
and are not replaced by later runs.

## Active comparison

| Test ID | Report | Server | Requests | Failure rate | Throughput | p50 | p95 | Status |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `local-flask-500-users` | `locust-500-users.md` | Flask development server, single process | 79,093 | 21.52% | 669.15 req/s | 320 ms | 1,500 ms | Failed transport capacity check |
| `local-gunicorn-500-users-schema-failure` | `locust-500-users-gunicorn.html` | Gunicorn, 4 workers, 2 threads | 147,098 | 100.00% | 1,226.57 req/s | 210 ms | 680 ms | Retained deployment failure |
| `local-gunicorn-500-users-fixed` | `locust-500-users-gunicorn-fixed.md` | Gunicorn, 4 workers, 2 threads | 128,917 | 0.00% | 1,078.47 req/s | 260 ms | 580 ms | Passed locally |

The fixed run is the current local baseline. It is not a hosted capacity claim:
Locust and the backend shared one Mac, and Locust reported CPU usage above 90%.

## Scenario contract

The same Locust scenario is used for every row and is defined in
`load_tests/locustfile.py`:

- read history and analytics endpoints
- search conversation history
- write a quiz result
- fetch the newly created quiz result

LLM generation endpoints are excluded because they require an external provider
and would measure provider latency and availability in addition to LearnLoop.

## Reproduction

See [`load_tests/README.md`](../../load_tests/README.md) for dependency setup,
the Gunicorn command, and the exact 500-user Locust command. Use a new report
prefix for every run.

# LearnLoop 500-user load test

Date: 2026-07-28

## Result

The 500-user target was exercised locally for two minutes against an isolated
SQLite database. The run is **not a clean pass**.

| Metric | Measured value |
| --- | ---: |
| Users | 500 |
| Ramp | 50 users/second |
| Duration | 2 minutes |
| Requests | 79,093 |
| Failures | 17,094 |
| Failure rate | 21.52% |
| Throughput | 669.15 requests/second |
| Aggregate p50 | 320 ms |
| Aggregate p95 | 1,500 ms |
| Aggregate maximum | 8,024 ms |

The per-endpoint values are in `locust-500-users_stats.csv`. The raw HTML
report, failure list, exceptions list, and time-series data are in this
directory.

## Scenario

Each simulated user used the non-LLM study-history flow:

- read `/history`, `/quiz_history`, `/flashcards_history`, and all three
  analytics endpoints
- search `/search`
- write a valid quiz result through `POST /quiz_results`
- fetch the created record through `GET /quiz_results/:id`

LLM-backed chat, quiz generation, and flashcard generation were excluded. They
require an OpenAI key and would add external provider availability and model
latency to this result.

Command:

```bash
locust -f load_tests/locustfile.py --headless \
  --host http://127.0.0.1:5050 \
  --users 500 --spawn-rate 50 --run-time 2m \
  --csv docs/load-tests/locust-500-users \
  --html docs/load-tests/locust-500-users.html \
  --only-summary
```

The backend used the Flask development server in a single process on the same
Mac that ran Locust. Locust reported CPU usage above 90% during the run.

## Failure analysis

The failure CSV contains client-side transport failures:

- `OSError(49): Can't assign requested address`
- `ConnectTimeoutError` to `127.0.0.1:5050`

No response failure contained `database is locked`, `SQLITE_BUSY`, or another
SQLite lock error. The server log showed successful `200` reads and `201`
quiz-result writes for requests that reached the backend. This means the run
demonstrates that the current single-process local setup cannot sustain the
test harness at this target, but it does not isolate an application-side 21.52%
HTTP error rate.

## SQLite WAL validation

The backend sets `PRAGMA journal_mode=WAL` and `PRAGMA busy_timeout=5000` on
SQLite connections. After the run:

```text
PRAGMA journal_mode: wal
PRAGMA integrity_check: ok
quiz_session rows: 3363
```

WAL allowed concurrent reads while quiz-result writes committed. No lock
errors were observed during this run. WAL still permits only one SQLite writer
at a time, so it is not a substitute for a production database when write
concurrency or multiple backend workers grows.

## Smallest next fix

Do not claim that LearnLoop has passed 500 users from this run. The smallest
measurement fix is to run Locust from a separate process or host and run the
backend behind a production WSGI server with multiple workers. Repeat the
same scenario there. If that run produces SQLite lock errors, move the write
path to the configured Postgres/Supabase database instead of increasing local
SQLite timeouts.

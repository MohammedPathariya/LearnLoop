# LearnLoop 500-user load test after WSGI upgrade

Date: 2026-07-28

## Result

The same 500-user scenario was rerun against four Gunicorn workers with two
threads per worker and a fresh SQLite database. This run passed its HTTP
success criterion locally.

| Metric | Initial Flask run | Fixed Gunicorn run |
| --- | ---: | ---: |
| Users | 500 | 500 |
| Duration | 2 minutes | 2 minutes |
| Requests | 79,093 | 128,917 |
| Failures | 17,094 (21.52%) | 0 (0.00%) |
| Throughput | 669.15 req/s | 1,078.47 req/s |
| Aggregate p50 | 320 ms | 260 ms |
| Aggregate p95 | 1,500 ms | 580 ms |
| Aggregate maximum | 8,024 ms | 1,020 ms |

The durable per-endpoint metrics are in
`locust-500-users-gunicorn-fixed_stats.csv`. The raw HTML, failures, exception,
and time-series files use the same `locust-500-users-gunicorn-fixed` prefix.

## Upgrade applied

- Added Gunicorn 23.0.0 to the backend dependencies.
- Docker now serves `wsgi:app` with four workers and two threads per worker.
- Added `backend/wsgi.py`, which creates the database schema before serving.
- Changed SQLite startup to set `busy_timeout` first and only switch to WAL
  when the connection is not already in WAL mode.

## Failure history retained

The first Gunicorn attempt is preserved under the
`locust-500-users-gunicorn_*` files. It returned 100% HTTP 500 responses. The
server log showed two separate startup defects: Gunicorn did not run the
schema creation guarded by `if __name__ == "__main__"`, and concurrent worker
startup attempted `PRAGMA journal_mode=WAL`, producing `database is locked`.

Those failures were fixed rather than excluded from the evidence.

## SQLite validation

The fixed run completed with:

```text
PRAGMA journal_mode: wal
PRAGMA integrity_check: ok
quiz_session rows: 7017
SQLite lock errors: none observed
```

The run is still local-only. Locust reported CPU usage above 90% on the Mac
running both the client and server, so this is evidence for the upgraded local
deployment path, not a hosted capacity guarantee.

## Next iteration

Repeat the same report from a separate load-generator host or distributed
Locust workers. For sustained multi-worker writes, validate the configured
Postgres/Supabase path before making a production 500-user claim.

# Sprint E (crawl-6) — Reliability

Tasks:
1. Atomic write for `resume.py` state_save (use temp+rename like json_writer.py)
2. File locking for `state.json` (use `fcntl` on POSIX / `msvcrt` on Windows)
3. Retry `httpx.ConnectError` and `httpx.ReadError` in `supabase_ops.run_with_retry`
4. Add circuit breaker for DDG rate-limit (cap 90s × 4 = 6min) — check `crawl4ai_client._throttle_before_search`

Reference: full audit in crawl-1 commit 27d319d (SPRINT_MEMORY.md)

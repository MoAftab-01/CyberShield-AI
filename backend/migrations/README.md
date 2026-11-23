# Threat-search ownership migration

`001_threat_search_ownership.sql` is an additive, one-time PostgreSQL migration
for databases that already have `threat_searches` without `user_id`.
It is never run by application startup or the test suite.

The new nullable owner references `users.id`. Existing records keep `NULL`
ownership; there is no backfill, guessed owner, deletion, or password change.
History and statistics include only records belonging to the authenticated user.
New application searches require a positive integer owner. If a user is deleted,
the database retains their searches with unknown ownership through `SET NULL`.

## Review and rollout

1. Obtain explicit approval for the target database and migration. Do not apply
   this file to production as part of development or testing.
2. Confirm the intended schema/search path, that `users.id` is an integer key,
   and that `threat_searches.user_id` and the named constraint/index do not exist.
   Fresh databases created with the updated SQLAlchemy models already have them
   and must not run this migration.
3. Test the migration and preservation of pre-existing rows on a disposable
   PostgreSQL database containing synthetic data. Arrange the target database's
   normal backup/snapshot before a separately approved application.
4. Coordinate the migration before running the owner-aware application code
   against an existing schema. `Base.metadata.create_all()` does not add columns
   to an existing table. Without migration, threat endpoints will fail rather
   than fall back to unscoped queries. Coordinate any mixed-version writers so
   older instances cannot continue creating ownerless activity.
5. Apply the reviewed SQL with the approved database tool. It runs in a
   transaction with bounded lock/statement waits. Inspect failure and rollback
   before retrying; the script intentionally fails on an already-migrated schema.
6. Verify existing row counts and contents are preserved, legacy owners remain
   `NULL`, and two synthetic users see only their own new history and counts.

No destructive down migration is supplied. Keep the additive column if rolling
back application code; dropping it would discard newly recorded ownership.

RAG visibility hardening does not rewrite indexes. Explicit public
`knowledge_base` chunks remain visible unless they contradict private ownership
or upload markers. Legacy private chunks without an owner and ambiguous scopes
are hidden; recovering their ownership requires a separately reviewed process.

-- PostgreSQL only. Apply once to an existing database after explicit approval.
-- No ownership backfill: existing rows remain NULL and are hidden from users.
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '60s';

ALTER TABLE threat_searches
    ADD COLUMN user_id INTEGER;

ALTER TABLE threat_searches
    ADD CONSTRAINT fk_threat_searches_user_id
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL;

CREATE INDEX ix_threat_searches_user_id ON threat_searches (user_id);

COMMIT;

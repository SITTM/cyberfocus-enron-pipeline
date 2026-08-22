-- Insider Language Index — pipeline schema.
-- person.split intentionally omitted: evaluation uses repeated stratified
-- group k-fold generated at analysis time from role labels, not a stored flag.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS person (
    person_id       INTEGER PRIMARY KEY,
    canonical_email TEXT NOT NULL UNIQUE,
    display_name    TEXT,
    domain          TEXT NOT NULL,
    is_enron        INTEGER NOT NULL CHECK (is_enron IN (0,1)),
    is_automated    INTEGER NOT NULL DEFAULT 0 CHECK (is_automated IN (0,1)),
    role            TEXT NOT NULL DEFAULT 'unassigned'
                        CHECK (role IN ('Convicted','Employee','Whistleblower','Other','unassigned')),
    role_source     TEXT NOT NULL DEFAULT 'unassigned'
                        CHECK (role_source IN ('manual','domain_rule','unassigned')),
    evidence_tier   TEXT CHECK (evidence_tier IN ('court_record','regulatory','major_press','corpus_internal','none')),
    evidence_url    TEXT,
    evidence_quote  TEXT,
    confidence      TEXT CHECK (confidence IN ('high','medium','low')),
    needs_review    INTEGER NOT NULL DEFAULT 1 CHECK (needs_review IN (0,1))
);

CREATE TABLE IF NOT EXISTS address_alias (
    email_address TEXT PRIMARY KEY,
    person_id     INTEGER NOT NULL REFERENCES person(person_id)
);

CREATE TABLE IF NOT EXISTS email (
    email_id        INTEGER PRIMARY KEY,
    message_id      TEXT NOT NULL UNIQUE,
    date_utc        TEXT,               -- ISO 8601; NULL if unparseable
    from_address    TEXT NOT NULL,
    from_person_id  INTEGER REFERENCES person(person_id),
    subject_hash    TEXT,               -- sha256 of subject; avoids storing subject verbatim
    custodian       TEXT NOT NULL,      -- maildir top-level folder this copy was first seen under
    folder          TEXT NOT NULL,      -- sub-folder path within custodian mailbox
    source_path     TEXT NOT NULL,      -- relative path of the first-seen file
    copy_count      INTEGER NOT NULL DEFAULT 1,
    is_duplicate_of INTEGER REFERENCES email(email_id)
);

CREATE INDEX IF NOT EXISTS idx_email_from_person ON email(from_person_id);
CREATE INDEX IF NOT EXISTS idx_email_date ON email(date_utc);

CREATE TABLE IF NOT EXISTS recipient (
    email_id  INTEGER NOT NULL REFERENCES email(email_id),
    person_id INTEGER REFERENCES person(person_id),
    address   TEXT NOT NULL,            -- raw address, in case person resolution is incomplete
    kind      TEXT NOT NULL CHECK (kind IN ('to','cc','bcc')),
    PRIMARY KEY (email_id, address, kind)
);

CREATE INDEX IF NOT EXISTS idx_recipient_person ON recipient(person_id);

CREATE TABLE IF NOT EXISTS body (
    email_id       INTEGER PRIMARY KEY REFERENCES email(email_id),
    authored_text  TEXT,                -- text attributed to from_address only
    quoted_text    TEXT,                -- everything the extractor identified as quoted/forwarded
    char_count     INTEGER,
    extractor_version TEXT NOT NULL
);

-- Long format: new features are new rows, never a schema migration.
CREATE TABLE IF NOT EXISTS feature (
    email_id           INTEGER NOT NULL REFERENCES email(email_id),
    feature_set_version TEXT NOT NULL,
    feature_name       TEXT NOT NULL,
    value              REAL,
    PRIMARY KEY (email_id, feature_set_version, feature_name)
);

-- Keyed on (stage, version): bumping analysis version re-queues analysis
-- without touching parsing/body status.
CREATE TABLE IF NOT EXISTS stage_status (
    email_id     INTEGER NOT NULL REFERENCES email(email_id),
    stage        TEXT NOT NULL CHECK (stage IN ('parsed','bodied','analysed')),
    version      TEXT NOT NULL,
    status       TEXT NOT NULL CHECK (status IN ('pending','done','error')),
    error        TEXT,
    updated_utc  TEXT NOT NULL,
    PRIMARY KEY (email_id, stage, version)
);

CREATE INDEX IF NOT EXISTS idx_stage_status_lookup ON stage_status(stage, version, status);

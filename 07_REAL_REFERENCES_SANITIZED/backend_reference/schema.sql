PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  enabled INTEGER NOT NULL DEFAULT 1,
  expires_at TEXT,
  created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
  token TEXT PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  device_id TEXT NOT NULL,
  device_fingerprint TEXT NOT NULL,
  signing_key TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  revoked INTEGER NOT NULL DEFAULT 0,
  created_at INTEGER NOT NULL,
  last_verify_at INTEGER
);

CREATE TABLE IF NOT EXISTS relay_credentials (
  id INTEGER PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  user_id INTEGER REFERENCES users(id),
  enabled INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS relay_tokens (
  relay_key TEXT PRIMARY KEY,
  credential_id INTEGER NOT NULL REFERENCES relay_credentials(id),
  revoked INTEGER NOT NULL DEFAULT 0,
  created_at INTEGER NOT NULL,
  last_refresh_at INTEGER
);

CREATE TABLE IF NOT EXISTS pairing_codes (
  id INTEGER PRIMARY KEY,
  code_hash TEXT NOT NULL UNIQUE,
  session_token TEXT NOT NULL REFERENCES sessions(token) ON DELETE CASCADE,
  expires_at INTEGER NOT NULL,
  created_at INTEGER NOT NULL,
  claimed_at INTEGER
);

CREATE TABLE IF NOT EXISTS relay_pairings (
  relay_key TEXT PRIMARY KEY REFERENCES relay_tokens(relay_key) ON DELETE CASCADE,
  session_token TEXT NOT NULL REFERENCES sessions(token) ON DELETE CASCADE,
  paired_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS request_nonces (
  fingerprint TEXT NOT NULL,
  path TEXT NOT NULL,
  nonce TEXT NOT NULL,
  timestamp INTEGER NOT NULL,
  created_at INTEGER NOT NULL,
  PRIMARY KEY (fingerprint, path, nonce)
);

CREATE INDEX IF NOT EXISTS sessions_device_idx ON sessions(device_id);
CREATE INDEX IF NOT EXISTS sessions_user_idx ON sessions(user_id);
CREATE INDEX IF NOT EXISTS pairing_codes_expiry_idx ON pairing_codes(expires_at);
CREATE INDEX IF NOT EXISTS relay_pairings_session_idx ON relay_pairings(session_token);
CREATE INDEX IF NOT EXISTS request_nonces_created_idx ON request_nonces(created_at);

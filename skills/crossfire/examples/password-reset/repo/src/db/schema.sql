-- users: about 2.1 million rows in production (counted 2026-10-01)
CREATE TABLE users (
  id            BIGINT PRIMARY KEY AUTO_INCREMENT,
  email         VARCHAR(320) NOT NULL UNIQUE,
  password_hash VARCHAR(100) NOT NULL,
  created_at    DATETIME NOT NULL,
  deleted_at    DATETIME NULL
);

CREATE TABLE sessions (
  id         CHAR(64) PRIMARY KEY,
  user_id    BIGINT NOT NULL,
  created_at DATETIME NOT NULL,
  deleted_at DATETIME NULL
);

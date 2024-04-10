-- This file should contain table definitions for the database.

CREATE TABLE IF NOT EXISTS availabilities(
    available SMALLINT,
    time TIMESTAMP PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS requests(
    email VARCHAR(300),
    time TIMESTAMP
);
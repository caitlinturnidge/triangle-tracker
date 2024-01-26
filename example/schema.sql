-- This file should contain table definitions for the database.

DROP TABLE IF EXISTS availabilities;
DROP TABLE IF EXISTS requests;

CREATE TABLE availabilities(
    available SMALLINT,
    time DATETIME PRIMARY KEY
);

CREATE TABLE requests(
    email VARCHAR(300),
    time DATETIME
);
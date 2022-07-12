CREATE TABLE tweets (id text unique, text text, author text, timestamp text, image_url text, likes int, rts int, sent integer);
CREATE TABLE users (email text unique, hash text);
CREATE TABLE following(username text, id text unique, last_checked text, followers text);
CREATE TABLE digests (email text, encoded_text text, timestamp int);

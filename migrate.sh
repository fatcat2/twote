#!/bin/bash

cat create-tables.sql | sqlite3 data.sqlite

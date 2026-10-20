"""Mirage audit agent: explains club shelf gaps from floor, backroom and system counts.

Reads a read-only DuckDB copy of the Mirage tables in data/ (agent/build_db.py) and writes only to its
own proposals and audit-log tables (agent/state.py). It never changes a Mirage record.
"""

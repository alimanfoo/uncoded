# tests/test_refs.py

import io
import json
import subprocess
from unittest import mock
import pytest
from uncoded.refs import Reference, _find_root, _read_message, _read_response, _run_exchange, _terminate, query_references

def _lsp_stream(*msgs: dict) -> io.BytesIO:
    ...

def _init_response() -> dict:
    ...

def _shutdown_response() -> dict:
    ...

class TestQueryReferences:
    def test_finds_call_sites(self, tmp_path):
        ...

    def test_returns_empty_list_when_no_references(self, tmp_path):
        ...

class TestRunExchange:
    def test_lsp_error_raises(self, tmp_path):
        ...

    def test_empty_result_list_returns_empty(self, tmp_path):
        ...

class TestFindRoot:
    def test_returns_pyproject_parent_when_found(self, tmp_path):
        ...

    def test_returns_in_path_parent_when_not_found(self, tmp_path):
        ...

class TestTerminate:
    def test_kills_on_timeout(self):
        ...

class TestReadMessage:
    def test_raises_on_closed_stream(self):
        ...

    def test_parses_framed_message(self):
        ...

class TestReadResponse:
    def test_skips_notifications_until_matching_id(self):
        ...

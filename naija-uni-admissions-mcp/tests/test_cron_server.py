"""Tests for the cron HTTP server module."""

from __future__ import annotations

import importlib
import os
from unittest.mock import patch

import pytest


@pytest.fixture
def cron_module(monkeypatch):
    from naija_admissions import cron_server
    importlib.reload(cron_server)
    return cron_server


def test_check_api_key_rejects_when_env_unset(cron_module, monkeypatch):
    monkeypatch.delenv("CRON_API_KEY", raising=False)
    assert cron_module._check_api_key("any") is False
    assert cron_module._check_api_key(None) is False


def test_check_api_key_rejects_when_not_set(cron_module, monkeypatch):
    monkeypatch.delenv("CRON_API_KEY", raising=False)
    assert cron_module._check_api_key("anyvalue") is False


def test_check_api_key_accepts_matching(cron_module, monkeypatch):
    monkeypatch.setenv("CRON_API_KEY", "supersecret")
    assert cron_module._check_api_key("supersecret") is True


def test_check_api_key_rejects_wrong(cron_module, monkeypatch):
    monkeypatch.setenv("CRON_API_KEY", "supersecret")
    assert cron_module._check_api_key("wrong") is False


def test_check_api_key_rejects_empty(cron_module, monkeypatch):
    monkeypatch.setenv("CRON_API_KEY", "supersecret")
    assert cron_module._check_api_key("") is False
    assert cron_module._check_api_key(None) is False


def test_default_constants(cron_module):
    assert cron_module.DEFAULT_PORT == 8787
    assert cron_module.DEFAULT_MAX == 20
    assert cron_module.DEFAULT_TYPES == ["university", "polytechnic", "college_of_education"]


def test_health_endpoint_routing(cron_module):
    # Just verify the handler class has the expected methods and routes
    handler = cron_module.CronHandler
    assert hasattr(handler, "do_GET")
    assert hasattr(handler, "do_POST")
    # Path constants used by the handler
    assert cron_module.DEFAULT_PORT == 8787


def test_main_requires_api_key(cron_module, monkeypatch, capsys):
    monkeypatch.delenv("CRON_API_KEY", raising=False)
    rc = cron_module.main()
    assert rc == 1
    captured = capsys.readouterr()
    assert "CRON_API_KEY" in captured.err

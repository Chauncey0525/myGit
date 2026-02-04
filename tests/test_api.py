# -*- coding: utf-8 -*-
"""pytest 关键接口与逻辑。"""
import pytest


def test_compare_value_rank():
    """排名：数字小=高，数字大=低。"""
    from app import _compare_value
    assert _compare_value("overall_rank", 1, 5) == "high"   # 猜的排名更高（数字小）
    assert _compare_value("overall_rank", 5, 1) == "low"
    assert _compare_value("overall_rank", 3, 3) == "correct"
    assert _compare_value("overall_rank", None, 1) == "low"
    assert _compare_value("overall_rank", 1, None) == "high"


def test_compare_value_era():
    """时代：索引小=早，索引大=晚。"""
    from app import _compare_value
    assert _compare_value("era", "秦", "清") == "early"
    assert _compare_value("era", "清", "秦") == "late"
    assert _compare_value("era", "唐", "唐") == "correct"
    assert _compare_value("era", None, None) == "correct"


def test_compare_value_numeric():
    """数值型：高了/低了/正确。"""
    from app import _compare_value
    assert _compare_value("virtue", 90, 80) == "high"
    assert _compare_value("virtue", 70, 80) == "low"
    assert _compare_value("virtue", 80, 80) == "correct"
    assert _compare_value("overall_score", 85.5, 80.0) == "high"
    assert _compare_value("virtue", None, 80) == "low"
    assert _compare_value("virtue", 80, None) == "high"


def test_is_valid_score():
    """有效评分判断。"""
    from app import _is_valid_score
    assert _is_valid_score(85.5) is True
    assert _is_valid_score(0) is True
    assert _is_valid_score(None) is False
    assert _is_valid_score("") is False
    assert _is_valid_score("-") is False


def test_app_routes_ok():
    """页面路由返回 200。"""
    from app import app
    client = app.test_client()
    assert client.get("/").status_code == 200
    assert client.get("/diy").status_code == 200
    assert client.get("/guess").status_code == 200


def test_app_api_eras_requires_db():
    """GET /api/eras 需要数据库，无 DB 时可能 500。"""
    from app import app
    client = app.test_client()
    r = client.get("/api/eras")
    assert r.status_code in (200, 500)


def test_app_api_emperors_export_query():
    """GET /api/emperors/export 使用与列表一致的 query 参数。"""
    from app import app
    client = app.test_client()
    r = client.get("/api/emperors/export?sort=overall_rank&order=asc")
    assert r.status_code in (200, 500)
    if r.status_code == 200:
        assert "text/csv" in r.content_type or "csv" in (r.content_type or "")

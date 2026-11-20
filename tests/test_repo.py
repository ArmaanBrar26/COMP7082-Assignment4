"""Unit tests for StoreRepository (repository.py)."""
import sqlite3

import pytest

from models import CartLine
from repository import StoreRepository
from setup_db import initialize


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "test.db"
    initialize(str(path))
    return str(path)


@pytest.fixture
def repo(db_path):
    return StoreRepository(db_path)


def stock_in_db(db_path, sku):
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute("SELECT stock FROM products WHERE sku = ?", (sku,)).fetchone()[0]
    finally:
        conn.close()

def test_get_product_returns_seeded_product(repo):
    product = repo.get_product("MOU-01")
    assert product.name == "Wireless mouse"
    assert product.price == 29.95
    assert product.stock == 20


@pytest.mark.parametrize("malicious_sku", [
    "x' OR '1'='1",
    "' OR 1=1 --",
    "MOU-01' OR sku LIKE '%",
])
def test_get_product_is_not_vulnerable_to_sql_injection(repo, malicious_sku):
    assert repo.get_product(malicious_sku) is None


def test_get_saved_cart_is_not_vulnerable_to_sql_injection(repo):
    repo.save_cart("alice", [CartLine("MOU-01", "Wireless mouse", 29.95, 2)])
    assert repo.get_saved_cart("alice") == [("MOU-01", 2)]
    assert repo.get_saved_cart("x' OR '1'='1") == []


def test_update_stock_decrements_when_enough_stock(repo, db_path):
    assert repo.update_stock("LAP-01", 2) is True
    assert stock_in_db(db_path, "LAP-01") == 3


def test_update_stock_can_take_all_remaining_stock(repo, db_path):
    assert repo.update_stock("LAP-01", 5) is True
    assert stock_in_db(db_path, "LAP-01") == 0


def test_update_stock_rejects_more_than_available(repo, db_path):
    assert repo.update_stock("LAP-01", 6) is False
    assert stock_in_db(db_path, "LAP-01") == 5
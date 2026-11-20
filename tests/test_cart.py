"""Unit tests for ShoppingCart (cart.py)."""


import pytest

from cart import ShoppingCart
from repository import StoreRepository
from setup_db import initialize


@pytest.fixture
def repo(tmp_path):
    db = tmp_path / "test.db"
    initialize(str(db))
    return StoreRepository(str(db))


@pytest.fixture
def cart(repo):
    return ShoppingCart("student", repo)


def quantity_of(cart, sku):
    return sum(line.quantity for line in cart.lines if line.sku == sku)


def test_add_valid_item_creates_line(cart):
    assert cart.add_item("USB-01", 2) is True
    assert len(cart.lines) == 1
    assert quantity_of(cart, "USB-01") == 2


@pytest.mark.parametrize("bad_quantity", [0, -5, "2", 1.5, None, True])
def test_add_item_rejects_invalid_quantity(cart, bad_quantity):
    assert cart.add_item("USB-01", bad_quantity) is False
    assert cart.lines == []


def test_adding_same_sku_merges_into_one_line(cart):
    cart.add_item("MOU-01", 2)
    cart.add_item("MOU-01", 3)
    assert len(cart.lines) == 1
    assert quantity_of(cart, "MOU-01") == 5


def test_repeated_adds_cannot_exceed_stock(cart):
    assert cart.add_item("LAP-01", 3) is True
    assert cart.add_item("LAP-01", 3) is False
    assert quantity_of(cart, "LAP-01") == 3


def test_remove_partial_and_full_quantity(cart):
    cart.add_item("USB-01", 5)
    assert cart.remove_item("USB-01", 2) is True
    assert quantity_of(cart, "USB-01") == 3
    assert cart.remove_item("USB-01") is True  
    assert cart.lines == []


@pytest.mark.parametrize("bad_quantity", [0, -1, "a"])
def test_remove_rejects_invalid_quantity(cart, bad_quantity):
    cart.add_item("USB-01", 3)
    assert cart.remove_item("USB-01", bad_quantity) is False
    assert quantity_of(cart, "USB-01") == 3

def test_subtotal_is_rounded_to_cents(cart):
    cart.add_item("LAP-01", 3)
    assert cart.subtotal() == 2999.97


def test_discounted_total_is_rounded_to_cents(cart):
    cart.add_item("LAP-01", 1)
    cart.apply_discount("WELCOME10")
    assert cart.total() == 899.99


def test_discounts_do_not_stack(cart):
    cart.add_item("MOU-01", 2)  
    cart.apply_discount("WELCOME10")
    cart.apply_discount("STUDENT20")
    assert cart.total() == 47.92  


def test_discount_updates_when_cart_is_edited(cart):
    cart.add_item("MOU-01", 1)
    cart.apply_discount("STUDENT20")
    assert cart.total() == 23.96
    cart.add_item("MOU-01", 1)
    assert cart.total() == 47.92
    cart.remove_item("MOU-01", 1)
    assert cart.total() == 23.96


def test_save15_never_goes_negative(cart):
    cart.add_item("USB-01", 1)
    assert cart.apply_discount("SAVE15") is True
    assert cart.total() == 0


def test_save15_boundary_just_above_15(cart):
    cart.add_item("USB-01", 2) 
    cart.apply_discount("SAVE15")
    assert cart.total() == 4.98


def test_invalid_coupon_is_rejected_and_changes_nothing(cart):
    cart.add_item("MOU-01", 2)
    assert cart.apply_discount("BOGUS") is False
    assert cart.discount_code is None
    assert cart.total() == 59.9

def test_save_then_load_restores_cart(repo):
    first = ShoppingCart("alice", repo)
    first.add_item("MOU-01", 2)
    first.add_item("USB-01", 4)
    first.save()

    second = ShoppingCart("alice", repo)
    second.load()
    assert quantity_of(second, "MOU-01") == 2
    assert quantity_of(second, "USB-01") == 4


def test_repeated_load_does_not_duplicate_items(repo):
    saved = ShoppingCart("alice", repo)
    saved.add_item("MOU-01", 2)
    saved.save()

    cart = ShoppingCart("alice", repo)
    cart.load()
    cart.load()
    cart.load()
    assert len(cart.lines) == 1
    assert quantity_of(cart, "MOU-01") == 2
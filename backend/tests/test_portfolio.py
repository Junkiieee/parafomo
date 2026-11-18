"""Portföy: IDOR, sayı doğrulama (NaN/inf/negatif/taşma), sembol doğrulama, kullanıcı sınırları."""
from __future__ import annotations

import pytest
from conftest import bearer, register
from sqlalchemy import func, select

from app.db import SessionLocal
from app.models import AssetType, Holding, Transaction
from app.routers import portfolio as portfolio_router


@pytest.fixture
def two_users(client):
    a = bearer(register(client, email="a@example.com"))
    b = bearer(register(client, email="b@example.com"))
    return a, b


def _raw(client, method, path, body: str, headers):
    return client.request(method, path, content=body, headers={**headers, "Content-Type": "application/json"})


def test_idor_other_users_rows_are_invisible(client, two_users):
    a, b = two_users
    hid = client.post("/portfolio/holdings", headers=a, json={
        "asset_type": "gold", "symbol": "x", "quantity": 10, "cost_price": 2500}).json()["id"]
    gid = client.post("/portfolio/goals", headers=a, json={"kind": "try", "target": 1000}).json()["id"]
    wid = client.post("/portfolio/watchlist", headers=a, json={"asset_type": "cash", "symbol": "x"}).json()["id"]
    aid = client.post("/portfolio/alerts", headers=a, json={
        "asset_type": "cash", "symbol": "x", "direction": "above", "threshold": 2}).json()["id"]

    assert client.patch(f"/portfolio/holdings/{hid}", headers=b, json={"quantity": 1}).status_code == 404
    assert client.delete(f"/portfolio/holdings/{hid}", headers=b).status_code == 404
    assert client.delete(f"/portfolio/goals/{gid}", headers=b).status_code == 404
    assert client.delete(f"/portfolio/watchlist/{wid}", headers=b).status_code == 404
    assert client.delete(f"/portfolio/alerts/{aid}", headers=b).status_code == 404
    for path in ("/portfolio/holdings", "/portfolio/goals", "/portfolio/watchlist", "/portfolio/alerts",
                 "/portfolio/transactions", "/portfolio/history"):
        assert client.get(path, headers=b).json() == [], path
    assert client.get("/portfolio/summary", headers=b).json()["holdings"] == []
    # B'nin satışı A'nın pozisyonuna dokunamaz
    r = client.post("/portfolio/transactions", headers=b, json={
        "asset_type": "gold", "symbol": "gold", "side": "sell", "quantity": 1, "price": 1})
    assert r.status_code == 400
    assert client.get("/portfolio/holdings", headers=a).json()[0]["quantity"] == 10


def test_requires_auth(client):
    for method, path in (("GET", "/portfolio/holdings"), ("GET", "/portfolio/summary"),
                         ("POST", "/portfolio/holdings"), ("DELETE", "/portfolio/holdings/1"),
                         ("DELETE", "/auth/me")):
        assert client.request(method, path).status_code in (401, 403), path


@pytest.mark.parametrize("body", [
    '{"asset_type":"cash","symbol":"x","quantity":Infinity,"cost_price":1}',
    '{"asset_type":"cash","symbol":"x","quantity":NaN,"cost_price":1}',
    '{"asset_type":"cash","symbol":"x","quantity":1,"cost_price":-Infinity}',
    '{"asset_type":"silver","symbol":"x","quantity":1e308,"cost_price":1e308}',
    '{"asset_type":"gold","symbol":"x","quantity":-1,"cost_price":1}',
    '{"asset_type":"gold","symbol":"x","quantity":0,"cost_price":1}',
])
def test_non_finite_negative_or_huge_amounts_rejected(client, two_users, body):
    a, _ = two_users
    r = _raw(client, "POST", "/portfolio/holdings", body, a)
    assert r.status_code == 422, r.text  # 500 değil, gövde JSON
    assert isinstance(r.json()["detail"], list)
    # kullanıcının uçları bozulmadı
    assert client.get("/portfolio/holdings", headers=a).status_code == 200
    assert client.get("/portfolio/summary", headers=a).status_code == 200


@pytest.mark.parametrize("path,body", [
    ("/portfolio/transactions", '{"asset_type":"cash","symbol":"x","side":"buy","quantity":1,"price":Infinity}'),
    ("/portfolio/alerts", '{"asset_type":"cash","symbol":"x","direction":"above","threshold":NaN}'),
    ("/portfolio/goals", '{"kind":"try","target":Infinity}'),
    ("/portfolio/goals", '{"kind":"try","target":1e13}'),
])
def test_non_finite_rejected_everywhere(client, two_users, path, body):
    a, _ = two_users
    assert _raw(client, "POST", path, body, a).status_code == 422


def test_patch_null_or_nonfinite_is_422_not_500(client, two_users):
    a, _ = two_users
    hid = client.post("/portfolio/holdings", headers=a, json={
        "asset_type": "gold", "symbol": "x", "quantity": 10, "cost_price": 2500}).json()["id"]
    r = client.patch(f"/portfolio/holdings/{hid}", headers=a, json={"quantity": None})
    assert r.status_code == 422 and isinstance(r.json()["detail"], str)
    assert _raw(client, "PATCH", f"/portfolio/holdings/{hid}", '{"cost_price":Infinity}', a).status_code == 422
    # uygulamanın gönderdiği biçim (tarih/not null) çalışır
    r = client.patch(f"/portfolio/holdings/{hid}", headers=a, json={
        "quantity": 12, "cost_price": 2400, "purchase_date": None, "note": None})
    assert r.status_code == 200 and r.json()["quantity"] == 12


def test_huge_path_ids_are_422_not_500(client, two_users):
    a, _ = two_users
    big = "99999999999999999999999"
    assert client.patch(f"/portfolio/holdings/{big}", headers=a, json={"quantity": 1}).status_code == 422
    for path in ("holdings", "alerts", "watchlist", "goals"):
        assert client.delete(f"/portfolio/{path}/{big}", headers=a).status_code == 422
        assert client.delete(f"/portfolio/{path}/0", headers=a).status_code == 422


@pytest.mark.parametrize("symbol", ["../../v7/finance/quote?symbols=X#", "THY AO", "A?range=max", "ŞOK", "THYAO.IS", "A" * 13])
def test_invalid_bist_symbols_rejected_without_outbound_request(client, two_users, no_network, symbol):
    a, _ = two_users
    for path, body in (
        ("/portfolio/holdings", {"asset_type": "bist", "symbol": symbol, "quantity": 1, "cost_price": 1}),
        ("/portfolio/transactions", {"asset_type": "bist", "symbol": symbol, "side": "buy", "quantity": 1, "price": 1}),
        ("/portfolio/watchlist", {"asset_type": "bist", "symbol": symbol}),
        ("/portfolio/alerts", {"asset_type": "bist", "symbol": symbol, "direction": "above", "threshold": 1}),
    ):
        r = client.post(path, headers=a, json=body)
        assert r.status_code in (400, 422), (path, r.status_code)
    assert not [u for u in no_network if "yahoo" in u]


def test_valid_bist_symbol_accepted_and_normalized(client, two_users):
    a, _ = two_users
    r = client.post("/portfolio/transactions", headers=a, json={
        "asset_type": "bist", "symbol": " thyao ", "side": "buy", "quantity": 5, "price": 300})
    assert r.status_code == 201 and r.json()["symbol"] == "THYAO"
    # fiyat kaynağı yokken özet yine 200 döner (fiyat None)
    s = client.get("/portfolio/summary", headers=a).json()
    assert s["holdings"][0]["current_price"] is None and s["total_cost"] == 1500


def test_legacy_symbol_can_still_be_sold(client, two_users):
    """Eski sürümün yazdığı biçimsiz sembol kilitlenmesin: satış doğrulamasız eşleşir."""
    a, _ = two_users
    with SessionLocal() as db:
        db.add(Holding(user_id=1, asset_type=AssetType.BIST, symbol="THYAO.IS", quantity=2, cost_price=10))
        db.commit()
    r = client.post("/portfolio/transactions", headers=a, json={
        "asset_type": "bist", "symbol": "THYAO.IS", "side": "sell", "quantity": 2, "price": 12})
    assert r.status_code == 201 and r.json()["realized_pl"] == 4


def test_holding_and_transaction_caps(client, two_users, monkeypatch):
    a, _ = two_users
    monkeypatch.setattr(portfolio_router, "_MAX_HOLDINGS", 2)
    monkeypatch.setattr(portfolio_router, "_MAX_TRANSACTIONS", 4)
    for sym in ("AKBNK", "GARAN"):
        assert client.post("/portfolio/holdings", headers=a, json={
            "asset_type": "bist", "symbol": sym, "quantity": 1, "cost_price": 1}).status_code == 201
    r = client.post("/portfolio/holdings", headers=a, json={
        "asset_type": "bist", "symbol": "THYAO", "quantity": 1, "cost_price": 1})
    assert r.status_code == 400
    # mevcut pozisyona ekleme sınırdan etkilenmez (yeni satır yok)
    assert client.post("/portfolio/transactions", headers=a, json={
        "asset_type": "bist", "symbol": "AKBNK", "side": "buy", "quantity": 1, "price": 2}).status_code == 201
    assert client.post("/portfolio/transactions", headers=a, json={
        "asset_type": "bist", "symbol": "AKBNK", "side": "sell", "quantity": 1, "price": 2}).status_code == 201
    r = client.post("/portfolio/transactions", headers=a, json={
        "asset_type": "bist", "symbol": "AKBNK", "side": "sell", "quantity": 1, "price": 2})
    assert r.status_code == 400  # defter dolu
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Transaction)) == 4


def test_body_size_limit(client, two_users):
    a, _ = two_users
    big = '{"asset_type":"gold","symbol":"x","quantity":1,"cost_price":1,"note":"' + "x" * 70_000 + '"}'
    r = _raw(client, "POST", "/portfolio/holdings", big, a)
    assert r.status_code == 413

    def chunks():  # Content-Length'siz (chunked) gövde de sayılır
        yield b'{"email":"a@example.com","password":"'
        for _ in range(100):
            yield b"x" * 1024
        yield b'"}'

    r = client.post("/auth/login", content=chunks(), headers={"Content-Type": "application/json"})
    assert r.status_code == 413


def test_sell_more_than_held_rejected(client, two_users):
    a, _ = two_users
    client.post("/portfolio/transactions", headers=a, json={
        "asset_type": "cash", "symbol": "cash", "side": "buy", "quantity": 100, "price": 1})
    r = client.post("/portfolio/transactions", headers=a, json={
        "asset_type": "cash", "symbol": "cash", "side": "sell", "quantity": 101, "price": 1})
    assert r.status_code == 400

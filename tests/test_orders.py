# tests/test_orders.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.database.models import Order, OrderItem, Merchandise, User
from app.schemas.order import OrderCreate, OrderItemCreate, OrderUpdate
from app.utils.order_service import OrderService
from datetime import datetime


def create_test_merchandise(
    db: Session, name: str, price: float, stock: int, admin_user: User
):
    merchandise = Merchandise(
        name=name,
        description=f"Test {name}",
        price=price,
        stock=stock,
        created_by_id=admin_user.id,
        updated_by_id=admin_user.id,
    )
    db.add(merchandise)
    db.commit()
    db.refresh(merchandise)
    return merchandise


@pytest.fixture
def test_merchandise(db_session, admin_user):
    items = [
        create_test_merchandise(db_session, "T-Shirt", 20.0, 50, admin_user),
        create_test_merchandise(db_session, "Cap", 15.0, 30, admin_user),
    ]
    return items


def test_create_order(client, user_token, test_merchandise, db_session, regular_user):
    order_data = OrderCreate(
        items=[
            OrderItemCreate(merchandise_id=test_merchandise[0].id, quantity=2),
            OrderItemCreate(merchandise_id=test_merchandise[1].id, quantity=1),
        ]
    )

    response = client.post(
        "/api/v1/orders/",
        headers={"Authorization": f"Bearer {user_token}"},
        json=order_data.model_dump(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_amount"] == 55.0  # 2 * 20.0 + 1 * 15.0
    assert data["status"] == "pending"
    assert data["user_id"] == regular_user.id

    # Check stock was updated
    db_merchandise = db_session.query(Merchandise).get(test_merchandise[0].id)
    assert db_merchandise.stock == 48  # 50 - 2


def test_create_order_insufficient_stock(client, user_token, test_merchandise):
    order_data = OrderCreate(
        items=[OrderItemCreate(merchandise_id=test_merchandise[0].id, quantity=51)]
    )

    response = client.post(
        "/api/v1/orders/",
        headers={"Authorization": f"Bearer {user_token}"},
        json=order_data.model_dump(),
    )

    assert response.status_code == 400
    assert "Insufficient stock" in response.json()["detail"]


def test_get_user_orders(
    client, user_token, test_merchandise, db_session, regular_user
):
    # Create some orders
    order_data = OrderCreate(
        items=[OrderItemCreate(merchandise_id=test_merchandise[0].id, quantity=1)]
    )

    # Create 3 orders
    for _ in range(3):
        client.post(
            "/api/v1/orders/",
            headers={"Authorization": f"Bearer {user_token}"},
            json=order_data.model_dump(),
        )

    response = client.get(
        "/api/v1/orders/my-orders", headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all(order["user_id"] == regular_user.id for order in data)


def test_update_order_status(
    client, admin_token, test_merchandise, admin_user, db_session
):
    # First create an order
    order_data = OrderCreate(
        items=[OrderItemCreate(merchandise_id=test_merchandise[0].id, quantity=1)]
    )

    order_response = client.post(
        "/api/v1/orders/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=order_data.model_dump(),
    )
    order_id = order_response.json()["id"]

    # Update order status using schema
    update_data = OrderUpdate(status="shipped")
    response = client.patch(
        f"/api/v1/orders/{order_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data.model_dump(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "shipped"
    assert data["updated_by_id"] == admin_user.id


def test_invalid_order_status(client, admin_token, test_merchandise):
    # First create an order
    order_data = OrderCreate(
        items=[OrderItemCreate(merchandise_id=test_merchandise[0].id, quantity=1)]
    )

    order_response = client.post(
        "/api/v1/orders/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=order_data.model_dump(),
    )
    order_id = order_response.json()["id"]

    # Try to update with invalid status
    response = client.patch(
        f"/api/v1/orders/{order_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "invalid_status"},
    )

    assert response.status_code == 422  # Validation error


def test_cancel_order_restores_stock(
    client, admin_token, test_merchandise, admin_user, db_session
):
    initial_stock = test_merchandise[0].stock

    # Create order
    order_data = OrderCreate(
        items=[OrderItemCreate(merchandise_id=test_merchandise[0].id, quantity=2)]
    )

    order_response = client.post(
        "/api/v1/orders/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=order_data.model_dump(),
    )
    order_id = order_response.json()["id"]

    # Verify stock was reduced
    db_merchandise = db_session.query(Merchandise).get(test_merchandise[0].id)
    assert db_merchandise.stock == initial_stock - 2

    # Cancel order using schema
    update_data = OrderUpdate(status="cancelled")
    response = client.patch(
        f"/api/v1/orders/{order_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data.model_dump(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["updated_by_id"] == admin_user.id

    # Verify stock was restored
    db_merchandise = db_session.query(Merchandise).get(test_merchandise[0].id)
    assert db_merchandise.stock == initial_stock


def test_get_order_summary(client, user_token, test_merchandise, regular_user):
    # Create an order
    order_data = OrderCreate(
        items=[
            OrderItemCreate(merchandise_id=test_merchandise[0].id, quantity=2),
            OrderItemCreate(merchandise_id=test_merchandise[1].id, quantity=1),
        ]
    )

    client.post(
        "/api/v1/orders/",
        headers={"Authorization": f"Bearer {user_token}"},
        json=order_data.model_dump(),
    )

    response = client.get(
        "/api/v1/orders/my-orders/summary",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    summary = data[0]
    assert summary["item_count"] == 2  # Number of different items
    assert summary["total_amount"] == 55.0  # 2 * 20.0 + 1 * 15.0


def test_get_order_statistics(client, admin_token, test_merchandise, admin_user):
    # Create some test orders first
    order_data = OrderCreate(
        items=[OrderItemCreate(merchandise_id=test_merchandise[0].id, quantity=1)]
    )

    client.post(
        "/api/v1/orders/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=order_data.model_dump(),
    )

    response = client.get(
        "/api/v1/orders/stats", headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    stats = response.json()
    assert "total_orders" in stats
    assert "total_revenue" in stats
    assert "average_order_value" in stats
    assert "orders_by_status" in stats
    assert isinstance(stats["orders_by_status"], dict)


def test_non_admin_cannot_access_stats(client, user_token):
    response = client.get(
        "/api/v1/orders/stats", headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 403
    assert "Only administrators" in response.json()["detail"]


def test_user_cannot_access_other_users_order(
    client, user_token, test_merchandise, admin_token
):
    # Create order as admin
    order_data = OrderCreate(
        items=[OrderItemCreate(merchandise_id=test_merchandise[0].id, quantity=1)]
    )

    admin_order = client.post(
        "/api/v1/orders/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=order_data.model_dump(),
    )
    admin_order_id = admin_order.json()["id"]

    # Try to access admin's order as regular user
    response = client.get(
        f"/api/v1/orders/{admin_order_id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 404
    assert "Order not found" in response.json()["detail"]


import React, { useEffect, useState, useContext } from 'react';
import { getUserOrders, cancelOrder } from '../api/apiClient';
import { AuthContext } from '../context/AuthContext';
import { Link } from 'react-router-dom';

function Orders() {
  const { user } = useContext(AuthContext);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }

    getUserOrders(user.id)
      .then(response => setOrders(response.data))
      .catch(() => setError('Unable to load your orders. Please try again.'))
      .finally(() => setLoading(false));
  }, [user]);

  const handleCancel = async (orderId) => {
    const confirmed = window.confirm(
      `Are you sure you want to cancel order #${orderId}?`
    );

    if (!confirmed) return;

    try {
      await cancelOrder(orderId);

      setOrders(previousOrders =>
        previousOrders.map(order =>
          order.id === orderId
            ? { ...order, status: 'CANCELLED' }
            : order
        )
      );
    } catch (err) {
      setError('Failed to cancel order. Please try again.');
    }
  };

  const formatPrice = price =>
    `₹${Number(price).toLocaleString('en-IN')}`;

  if (loading) {
    return <main className="page"><p>Loading your orders...</p></main>;
  }

  if (!user) {
    return (
      <main className="page">
        <h1>My Orders</h1>
        <p>Please log in to view your orders.</p>
        <Link className="primary-link" to="/login">Login</Link>
      </main>
    );
  }

  return (
    <main className="page orders-page">
      <div className="orders-heading">
        <span className="checkout-eyebrow">YOUR ACCOUNT</span>
        <h1>My Orders</h1>
        <p>View and manage your recent purchases.</p>
      </div>

      {error && <p className="error">{error}</p>}

      {orders.length === 0 ? (
        <section className="empty-cart">
          <div className="empty-cart-icon">📦</div>
          <h2>No orders yet</h2>
          <p>Your placed orders will appear here.</p>
          <Link className="primary-link" to="/">Start Shopping</Link>
        </section>
      ) : (
        <div className="orders-list">
          {orders.map(order => (
            <article className="order-card" key={order.id}>
              <div className="order-card-top">
                <div>
                  <span className="order-label">ORDER</span>
                  <h2>#{order.id}</h2>
                </div>

                <span
                  className={`order-status status-${String(order.status).toLowerCase()}`}
                >
                  {order.status}
                </span>
              </div>

              <div className="order-card-bottom">
                <div>
                  <span className="order-label">TOTAL AMOUNT</span>
                  <strong className="order-amount">
                    {formatPrice(order.totalAmount)}
                  </strong>
                </div>

                {order.status === 'PENDING' && (
                  <button
                    className="cancel-order-btn"
                    onClick={() => handleCancel(order.id)}
                  >
                    Cancel Order
                  </button>
                )}
              </div>
            </article>
          ))}
        </div>
      )}
    </main>
  );
}

export default Orders;
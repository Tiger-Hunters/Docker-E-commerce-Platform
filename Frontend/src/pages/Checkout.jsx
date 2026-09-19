
import React, { useState, useContext } from 'react';
import { createOrder } from '../api/apiClient';
import { AuthContext } from '../context/AuthContext';
import { CartContext } from '../context/CartContext';
import { Link, useNavigate } from 'react-router-dom';

function Checkout() {
  const { user } = useContext(AuthContext);
  const { cartItems, removeFromCart, clearCart } = useContext(CartContext);
  const navigate = useNavigate();

  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const total = cartItems.reduce(
    (sum, item) => sum + Number(item.price) * item.quantity,
    0
  );

  const formatPrice = price =>
    `₹${Number(price).toLocaleString('en-IN')}`;

  const handleCheckout = async () => {
    if (!user) {
      setMessage('Please login first!');
      return;
    }

    if (cartItems.length === 0) {
      setMessage('Your cart is empty.');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const orderData = {
        userId: user.id,
        items: cartItems.map(item => ({
          productId: item.productId,
          quantity: item.quantity,
        })),
      };

      const response = await createOrder(orderData);
      clearCart();

      setMessage(`Order created successfully! ID: ${response.data.id}`);
      setTimeout(() => navigate('/orders'), 2000);
    } catch (err) {
      setMessage(
        err.response?.data?.error || 'Failed to create order.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="page checkout-page">
      <div className="checkout-heading">
        <span className="checkout-eyebrow">YOUR SHOPPING BAG</span>
        <h1>Checkout</h1>
        <p>Review your items before placing your order.</p>
      </div>

      {cartItems.length === 0 ? (
        <section className="empty-cart">
          <div className="empty-cart-icon">🛒</div>
          <h2>Your cart is empty</h2>
          <p>Looks like you haven't added anything yet.</p>
          <Link className="primary-link" to="/">
            Continue Shopping
          </Link>
        </section>
      ) : (
        <div className="checkout-layout">
          <section className="checkout-items">
            <div className="checkout-section-heading">
              <h2>Your Items</h2>
              <span>{cartItems.length} product(s)</span>
            </div>

            {cartItems.map(item => (
              <article className="checkout-item" key={item.productId}>
                <div className="checkout-item-icon">📦</div>

                <div className="checkout-item-details">
                  <h3>{item.name}</h3>
                  <p>{formatPrice(item.price)} each</p>
                  <span className="item-quantity">
                    Quantity: {item.quantity}
                  </span>
                </div>

                <div className="checkout-item-right">
                  <strong>
                    {formatPrice(item.price * item.quantity)}
                  </strong>
                  <button
                    className="remove-btn"
                    onClick={() => removeFromCart(item.productId)}
                  >
                    Remove
                  </button>
                </div>
              </article>
            ))}

            <Link className="continue-link" to="/">
              ← Continue Shopping
            </Link>
          </section>

          <aside className="order-summary">
            <h2>Order Summary</h2>

            <div className="summary-row">
              <span>Items</span>
              <span>
                {cartItems.reduce((sum, item) => sum + item.quantity, 0)}
              </span>
            </div>

            <div className="summary-row">
              <span>Subtotal</span>
              <span>{formatPrice(total)}</span>
            </div>

            <div className="summary-row">
              <span>Shipping</span>
              <span className="free-shipping">Free</span>
            </div>

            <div className="summary-total">
              <span>Total</span>
              <strong>{formatPrice(total)}</strong>
            </div>

            <button
              className="place-order-btn"
              onClick={handleCheckout}
              disabled={loading}
            >
              {loading ? 'Placing Order...' : 'Place Order →'}
            </button>

            <p className="secure-note">🔒 Secure checkout</p>
          </aside>
        </div>
      )}

      {message && (
        <p className="checkout-message" role="status">
          {message}
        </p>
      )}
    </main>
  );
}

export default Checkout;
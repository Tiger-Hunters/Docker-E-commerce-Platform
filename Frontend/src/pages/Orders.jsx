import React, { useEffect, useState, useContext } from 'react';
import { getUserOrders, cancelOrder } from '../api/apiClient';
import { AuthContext } from '../context/AuthContext';

const Orders = () => {
  const { user } = useContext(AuthContext);
  const [orders, setOrders] = useState([]);

  useEffect(() => {
    if (user) {
      getUserOrders(user.id)
        .then(response => setOrders(response.data))
        .catch(err => console.error(err));
    }
  }, [user]);

  const handleCancel = async (orderId) => {
    try {
      await cancelOrder(orderId);
      // Update local state to reflect cancellation
      setOrders(orders.map(o => o.id === orderId ? { ...o, status: 'CANCELLED' } : o));
    } catch (err) {
      console.error('Failed to cancel order');
    }
  };

  return (
    <div>
      <h2>My Orders</h2>
      {orders.map(order => (
        <div key={order.id} style={{ borderBottom: '1px solid #ccc', padding: '10px' }}>
          <p>Order ID: {order.id}</p>
          <p>Status: {order.status}</p>
          <p>Total Amount: ₹{order.totalAmount}</p>
          {order.status === 'PENDING' && (
            <button onClick={() => handleCancel(order.id)}>Cancel Order</button>
          )}
        </div>
      ))}
    </div>
  );
};
export default Orders;
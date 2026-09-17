import React, { useState, useContext } from 'react';
import { createOrder } from '../api/apiClient';
import { AuthContext } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const Checkout = ({ cartItems }) => { 
  // Assume cartItems is passed in or fetched from a CartContext
  // Example shape: [{ productId: 101, quantity: 2 }]
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();
  const [message, setMessage] = useState('');

  const handleCheckout = async () => {
    if (!user) {
      setMessage('Please login first!');
      return;
    }
    try {
      const orderData = {
        userId: user.id,
        items: cartItems 
      };
      const response = await createOrder(orderData);
      setMessage(`Order created successfully! ID: ${response.data.id}`);
      setTimeout(() => navigate('/orders'), 2000);
    } catch (err) {
      setMessage(err.response?.data?.error || 'Failed to create order');
    }
  };

  return (
    <div>
      <h2>Checkout</h2>
      <button onClick={handleCheckout}>Place Order</button>
      {message && <p>{message}</p>}
    </div>
  );
};
export default Checkout;
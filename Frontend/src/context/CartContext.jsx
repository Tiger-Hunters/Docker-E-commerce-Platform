
import React, { createContext, useState } from 'react';

export const CartContext = createContext();

export const CartProvider = ({ children }) => {
  const [cartItems, setCartItems] = useState([]);

  const addToCart = (product, quantity = 1) => {
    setCartItems((currentItems) => {
      const existing = currentItems.find(
        (item) => item.productId === product.id
      );

      if (existing) {
        return currentItems.map((item) =>
          item.productId === product.id
            ? { ...item, quantity: item.quantity + quantity }
            : item
        );
      }

      return [
        ...currentItems,
        {
          productId: product.id,
          name: product.name,
          price: Number(product.price),
          quantity,
        },
      ];
    });
  };

  const removeFromCart = (productId) => {
    setCartItems((items) =>
      items.filter((item) => item.productId !== productId)
    );
  };

  const clearCart = () => setCartItems([]);

  return (
    <CartContext.Provider
      value={{ cartItems, addToCart, removeFromCart, clearCart }}
    >
      {children}
    </CartContext.Provider>
  );
};
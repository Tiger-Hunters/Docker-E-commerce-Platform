import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';

import Login from './pages/Login';
import Products from './pages/Products';
import Orders from './pages/Orders';
// Import other pages...

function App() {
  return (
    <AuthProvider>
      <Router>
        <div>
          {/* Include a simple Navbar component here */}
          <Routes>
            <Route path="/" element={<Products />} />
            <Route path="/login" element={<Login />} />
            <Route path="/orders" element={<Orders />} />
            {/* Add routes for Register, Checkout, Product Details */}
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
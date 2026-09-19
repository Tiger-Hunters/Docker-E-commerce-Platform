
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { registerUser } from '../api/apiClient';

const Register = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();

  const handleRegister = async (event) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      await registerUser({ name, email, password });

      navigate('/login', {
        state: { message: 'Account created. Please log in.' },
      });
    } catch (err) {
      setError(err.response?.data?.error || 'Registration failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="page auth-page">
      <div className="auth-card">
        <div className="auth-heading">
          <h2>Create your account</h2>
          <p>Join ShopSphere and start shopping</p>
        </div>

        {error && <p className="error auth-error">{error}</p>}

        <form className="auth-form" onSubmit={handleRegister}>
          <label htmlFor="name">Full name</label>
          <input
            id="name"
            type="text"
            placeholder="Enter your full name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            autoComplete="name"
            required
          />

          <label htmlFor="email">Email address</label>
          <input
            id="email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            autoComplete="email"
            required
          />

          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            placeholder="Create a password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="new-password"
            required
          />

          <button type="submit" disabled={loading}>
            {loading ? 'Creating account...' : 'Create account'}
          </button>
        </form>

        <p className="auth-footer">
          Already registered? <Link to="/login">Login</Link>
        </p>
      </div>
    </main>
  );
};

export default Register;
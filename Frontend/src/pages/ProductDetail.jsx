
import React, { useEffect, useState, useContext } from 'react';
import { Link, useParams } from 'react-router-dom';
import { getProductById } from '../api/apiClient';
import { CartContext } from '../context/CartContext';

function ProductDetail() {
  const { id } = useParams();
  const { addToCart } = useContext(CartContext);

  const [product, setProduct] = useState(null);
  const [quantity, setQuantity] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const fetchProduct = async () => {
      try {
        const response = await getProductById(id);
        setProduct(response.data);
      } catch (err) {
        setError('Failed to load product.');
      } finally {
        setLoading(false);
      }
    };

    fetchProduct();
  }, [id]);

  if (loading) return <main className="page"><p>Loading product...</p></main>;
  if (error) return <main className="page"><p className="error">{error}</p></main>;
  if (!product || !product.isActive) {
    return <main className="page"><p>Product not found.</p></main>;
  }

  const stock = Number(product.stockQuantity) || 0;

  const handleAddToCart = () => {
    if (stock <= 0) return;

    addToCart(product, quantity);
    setMessage(`Added ${quantity} item(s) to cart!`);
  };

  return (
    <main className="page">
      <Link className="back-link" to="/">
        ← Back to Products
      </Link>

      <section className="detail-card">
        <div className="detail-visual">
          <span className="detail-icon">🛍️</span>
        </div>

        <div className="detail-info">
          <span className="product-category">{product.category}</span>
          <h1>{product.name}</h1>
          <p className="detail-description">{product.description}</p>

          <p className="detail-price">
            ₹{Number(product.price).toLocaleString('en-IN')}
          </p>

          <p className={stock > 0 ? 'stock-available' : 'stock-empty'}>
            {stock > 0 ? `${stock} in stock` : 'Out of stock'}
          </p>

          {stock > 0 && (
            <div className="quantity-control">
              <label htmlFor="quantity">Quantity</label>
              <div className="quantity-buttons">
                <button
                  type="button"
                  className="quantity-btn"
                  onClick={() => setQuantity(q => Math.max(1, q - 1))}
                  disabled={quantity <= 1}
                >
                  −
                </button>

                <span>{quantity}</span>

                <button
                  type="button"
                  className="quantity-btn"
                  onClick={() => setQuantity(q => Math.min(stock, q + 1))}
                  disabled={quantity >= stock}
                >
                  +
                </button>
              </div>
            </div>
          )}

          <button
            className="add-cart-btn"
            onClick={handleAddToCart}
            disabled={stock <= 0}
          >
            {stock > 0 ? 'Add to Cart' : 'Out of Stock'}
          </button>

          {message && <p className="success-message">{message}</p>}
        </div>
      </section>
    </main>
  );
}

export default ProductDetail;
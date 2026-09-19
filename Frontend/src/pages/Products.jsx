
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getProducts } from '../api/apiClient';

const Products = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const response = await getProducts();
        setProducts(response.data.filter((product) => product.isActive));
      } catch (err) {
        setError(
          err.response?.data?.error ||
          'Unable to load products. Please try again.'
        );
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, []);

  if (loading) {
    return <main className="page"><p>Loading products...</p></main>;
  }

  if (error) {
    return <main className="page"><p className="error">{error}</p></main>;
  }

  return (
    <main className="page">
      <h1>Product Catalog</h1>

      {products.length === 0 ? (
        <p>No products are available right now.</p>
      ) : (
        <div className="product-grid">
          {products.map((product) => (
            <article className="product-card" key={product.id}>
              <span className="product-category">{product.category}</span>
              <h2>{product.name}</h2>
              <p>{product.description}</p>
              <p className="product-price">
                ₹{Number(product.price).toLocaleString('en-IN')}
              </p>
              <p>
                {product.stockQuantity > 0
                  ? `${product.stockQuantity} in stock`
                  : 'Out of stock'}
              </p>
              <Link
                className="primary-link"
                to={`/products/${product.id}`}
              >
                View Details
              </Link>
            </article>
          ))}
        </div>
      )}
    </main>
  );
};

export default Products;
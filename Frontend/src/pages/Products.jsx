import React, { useEffect, useState } from 'react';
import { getProducts } from '../api/apiClient';
import { Link } from 'react-router-dom';

const Products = () => {
  const [products, setProducts] = useState([]);

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const response = await getProducts();
        setProducts(response.data);
      } catch (err) {
        console.error(err);
      }
    };
    fetchProducts();
  }, []);

  return (
    <div>
      <h2>Product Catalog</h2>
      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
        {products.map(product => product.isActive && (
          <div key={product.id} style={{ border: '1px solid gray', padding: '1rem' }}>
            <h3>{product.name}</h3>
            <p>{product.description}</p>
            <p>₹{product.price}</p>
            <Link to={`/products/${product.id}`}>View Details</Link>
          </div>
        ))}
      </div>
    </div>
  );
};
export default Products;
import { useState } from 'react';
import './Login.css';
import { loginUser } from '../api/api';
import { deriveAESKey } from '../Encryption/CryptoUtils';
import { setAESKey } from '../Encryption/AesKeyStore';
import { useNavigate } from 'react-router-dom';
import passmanLogo from '../../assets/passmanLogo.png'

const Login = () => {
  const [credentials, setCredentials] = useState({
    email: '',
    password: ''
  });
  
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setCredentials({
      ...credentials,
      [name]: value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    localStorage.removeItem('token');
    localStorage.removeItem('userId');
    
    try {
      if (credentials.email && credentials.password) {
        const response = await loginUser(credentials);
        const data = response.data;
        localStorage.setItem('token', data.token);
        localStorage.setItem('userId', data.userId);
        const encryptedSalt = data.encryptionSalt;
        const aesKey = await deriveAESKey(credentials.password, encryptedSalt);
        setAESKey(aesKey);
        
        navigate('/dashboard');         
      } else if (!credentials.email && !credentials.password) {
        setError('Please fill in all fields');
      } else {
        setError('Please fill in all fields');
      }
    } catch (e) {
      console.error('Login error:', e);
      
      if (e.response) {
        const errorResponse = e.response.data;
        const errorMessage = errorResponse?.message || 'Login failed';
        
        if (e.response.status === 401) {
          setError(errorMessage); 
        } else if (e.response.status === 400) {
          setError(errorMessage);
        } else {
          setError(`${errorMessage} (${e.response.status})`);
        }
      } else if (e.request) {
        setError('Server not responding. Please try again later.');
      } else {
        setError('Login failed. Please check your credentials.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-form-box">
      <div className="logo-container">
          <img src={passmanLogo} alt="PassMan Logo" />
        </div>
        <h2 className="login-subtitle">Login to your account</h2>
        
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={credentials.email}
              onChange={handleChange}
              placeholder="Enter your email"
              required
              className='form-input'
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={credentials.password}
              onChange={handleChange}
              placeholder="Enter your password"
              required
              className='form-input'
            />
          </div>
          
          <button type="submit" className="login-button">
            {loading ? (
              <div className="login-loading-spinner">
                <div className="login-spinner"></div>
                <span className="login-loading-text">Logging in...</span>
              </div>
            ) : 'Login'}
          </button>
        </form>
        
        <div className="login-footer">
          <p className='login-footer-text'>Don't have an account? <a href="/signup" className='login-footer-link'>Sign up</a></p>
          <p><a href="/forgot-password" className='login-footer-link'>Forgot password?</a></p>
        </div>
      </div>
    </div>
  );
};

export default Login;
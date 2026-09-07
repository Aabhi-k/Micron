import { useNavigate } from 'react-router-dom';
import './Home.css';
import passmanLogo from '../../assets/passmanLogo.png';
import secureAppImg from '../../assets/secureApp.png';
const Home = () => {
  const navigate = useNavigate();

  const handleNavigation = (path) => {
    navigate(path);
  };

  return (
    <div className="home-container">
      <header className="home-header">
        <div className="home-logo">
          <img src={passmanLogo} alt="PassMan Logo" />
        </div>
        <div className="home-nav-buttons">
          <button 
            className="nav-button"
            onClick={() => handleNavigation('/login')}
          >
            Log In
          </button>
          <button 
            className="nav-button primary"
            onClick={() => handleNavigation('/signup')}
          >
            Sign Up
          </button>
        </div>
      </header>

      <section className="home-hero">
        <div className="hero-content">
          <h1 className="hero-title">Secure Your Digital Life</h1>
          <p className="hero-subtitle">
            PassMan is the modern password manager that keeps your credentials safe with
            advanced encryption. Store, generate, and access your passwords securely from anywhere.
          </p>
          <div className="hero-buttons">
            <button 
              className="hero-button primary"
              onClick={() => handleNavigation('/signup')}
            >
              Get Started
            </button>
            <button 
              className="hero-button secondary"
              onClick={() => handleNavigation('/login')}
            >
              Learn More
            </button>
          </div>
        </div>
        <div className="hero-image">
          <img src={secureAppImg} alt="Secure Password Management" />
        </div>
      </section>

      <section className="features-section">
        <h2 className="section-title">Why Choose PassMan</h2>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">🔒</div>
            <h3 className="feature-title">End-to-End Encryption</h3>
            <p className="feature-description">
              Your passwords are safe with AES-256, ensuring that only you can access your sensitive data.
              We never store your master password on our servers.
            </p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">🔄</div>
            <h3 className="feature-title">Cross-Platform Access</h3>
            <p className="feature-description">
              Access your passwords securely from any device. Our responsive design ensures a seamless experience
              on desktop and mobile.
            </p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">🛡️</div>
            <h3 className="feature-title">Password Generator</h3>
            <p className="feature-description">
              Generate strong, unique passwords for all your accounts with our built-in password generator.
              No more reused or weak passwords.
            </p>
          </div>
        </div>
      </section>

      <section className="cta-section">
        <h2 className="cta-title">Ready to Take Control of Your Passwords?</h2>
        <p className="cta-subtitle">
          Join thousands of users who trust PassMan for their password security needs.
          Sign up today and experience peace of mind.
        </p>
        <button 
          className="hero-button primary"
          onClick={() => handleNavigation('/signup')}
        >
          Create Free Account
        </button>
      </section>

    
    </div>
  );
};

export default Home;
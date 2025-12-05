import React from 'react';
import { Link } from 'react-router-dom';
import './Landing.css';

const Landing: React.FC = () => {
  return (
    <div className="landing-container">
      <div className="landing-content">
        <header className="landing-header">
          <div className="logo-container">
            <svg className="ghost-icon" width="48" height="48" viewBox="0 0 48 48" fill="none">
              <path d="M24 4C15.163 4 8 11.163 8 20v18c0 1.1.9 2 2 2 1.1 0 2-.9 2-2v-2c0-1.1.9-2 2-2s2 .9 2 2v2c0 1.1.9 2 2 2s2-.9 2-2v-2c0-1.1.9-2 2-2s2 .9 2 2v2c0 1.1.9 2 2 2s2-.9 2-2v-2c0-1.1.9-2 2-2s2 .9 2 2v2c0 1.1.9 2 2 2s2-.9 2-2V20c0-8.837-7.163-16-16-16z" fill="#DD4B39" opacity="0.15"/>
              <circle cx="18" cy="20" r="2" fill="#333333"/>
              <circle cx="30" cy="20" r="2" fill="#333333"/>
              <path d="M20 26c0 2.21 1.79 4 4 4s4-1.79 4-4" stroke="#333333" strokeWidth="2" strokeLinecap="round"/>
            </svg>
            <h1>Watcher</h1>
          </div>
          <p className="tagline">Haunt the web. Stay informed.</p>
        </header>

        <section className="hero-section">
          <div className="hero-content">
            <div className="hero-text">
              <h2>Never miss a website change again</h2>
              <p className="hero-description">
                <strong>Haunt</strong> any website—track job postings, monitor prices, watch for updates. 
                Watcher follows sites like a ghost, alerting you only when something meaningful changes.
              </p>
              <div className="cta-buttons">
                <Link to="/signup" className="cta-primary">Start haunting</Link>
                <Link to="/login" className="cta-secondary">Sign in</Link>
              </div>
            </div>
            <div className="hero-visual">
              <svg width="280" height="200" viewBox="0 0 280 200" fill="none">
                {/* Browser window */}
                <rect x="20" y="20" width="240" height="160" rx="4" fill="white" stroke="#E5E5E5" strokeWidth="2"/>
                <rect x="20" y="20" width="240" height="24" fill="#FAFAFA" stroke="#E5E5E5" strokeWidth="2"/>
                <circle cx="32" cy="32" r="4" fill="#DD4B39"/>
                <circle cx="44" cy="32" r="4" fill="#E5E5E5"/>
                <circle cx="56" cy="32" r="4" fill="#E5E5E5"/>
                
                {/* Content lines */}
                <rect x="35" y="60" width="180" height="8" rx="2" fill="#3366CC" opacity="0.3"/>
                <rect x="35" y="75" width="140" height="6" rx="2" fill="#777777" opacity="0.2"/>
                <rect x="35" y="95" width="180" height="8" rx="2" fill="#3366CC" opacity="0.3"/>
                <rect x="35" y="110" width="160" height="6" rx="2" fill="#777777" opacity="0.2"/>
                <rect x="35" y="130" width="180" height="8" rx="2" fill="#3366CC" opacity="0.3"/>
                <rect x="35" y="145" width="120" height="6" rx="2" fill="#777777" opacity="0.2"/>
                
                {/* Floating ghost */}
                <g className="floating-ghost">
                  <path d="M220 80c-8 0-14 6-14 14v16c0 1 1 2 2 2s2-1 2-2v-2c0-1 1-2 2-2s2 1 2 2v2c0 1 1 2 2 2s2-1 2-2v-2c0-1 1-2 2-2s2 1 2 2v2c0 1 1 2 2 2s2-1 2-2V94c0-8-6-14-14-14z" fill="#DD4B39" opacity="0.2"/>
                  <circle cx="216" cy="92" r="1.5" fill="#333333"/>
                  <circle cx="224" cy="92" r="1.5" fill="#333333"/>
                </g>
              </svg>
            </div>
          </div>
        </section>

        <section className="what-is-haunting">
          <div className="haunting-explanation">
            <div className="haunting-icon">
              <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                <path d="M32 8C20.954 8 12 16.954 12 28v24c0 1.657 1.343 3 3 3s3-1.343 3-3v-3c0-1.657 1.343-3 3-3s3 1.343 3 3v3c0 1.657 1.343 3 3 3s3-1.343 3-3v-3c0-1.657 1.343-3 3-3s3 1.343 3 3v3c0 1.657 1.343 3 3 3s3-1.343 3-3v-3c0-1.657 1.343-3 3-3s3 1.343 3 3v3c0 1.657 1.343 3 3 3s3-1.343 3-3V28c0-11.046-8.954-20-20-20z" fill="#DD4B39" opacity="0.1"/>
                <circle cx="24" cy="28" r="3" fill="#333333"/>
                <circle cx="40" cy="28" r="3" fill="#333333"/>
                <path d="M26 36c0 3.314 2.686 6 6 6s6-2.686 6-6" stroke="#333333" strokeWidth="2.5" strokeLinecap="round"/>
              </svg>
            </div>
            <h3>What does it mean to "haunt" a website?</h3>
            <p className="haunting-description">
              When you <strong>haunt a website</strong>, Watcher becomes your invisible observer—silently 
              watching a page for the changes you care about. Like a friendly ghost, it monitors 24/7 
              without being seen, then alerts you the moment something important happens.
            </p>
            <div className="haunting-examples">
              <div className="example-card">
                <span className="example-icon">💼</span>
                <p><strong>Haunt a job board</strong> to catch new postings the second they appear</p>
              </div>
              <div className="example-card">
                <span className="example-icon">🎓</span>
                <p><strong>Haunt a course page</strong> to grab a spot when enrollment opens</p>
              </div>
              <div className="example-card">
                <span className="example-icon">🛍️</span>
                <p><strong>Haunt a product page</strong> to buy when it's back in stock</p>
              </div>
            </div>
          </div>
        </section>

        <section className="features-section">
          <h3>How Watcher works</h3>
          <div className="features-grid">
            <div className="feature">
              <svg className="feature-svg" width="48" height="48" viewBox="0 0 48 48" fill="none">
                <rect x="8" y="12" width="32" height="28" rx="2" stroke="#3366CC" strokeWidth="2" fill="none"/>
                <path d="M14 18h20M14 24h16M14 30h18" stroke="#777777" strokeWidth="2" strokeLinecap="round"/>
                <path d="M24 8l4 4h-8l4-4z" fill="#DD4B39"/>
              </svg>
              <h4>Just describe what you want</h4>
              <p>
                Say "monitor the price" or "watch for new posts" in plain English. 
                Our AI figures out the technical details and sets everything up for you.
              </p>
            </div>

            <div className="feature">
              <svg className="feature-svg" width="48" height="48" viewBox="0 0 48 48" fill="none">
                <circle cx="24" cy="24" r="16" stroke="#3366CC" strokeWidth="2" fill="none"/>
                <path d="M24 12v12l8 4" stroke="#DD4B39" strokeWidth="2" strokeLinecap="round"/>
                <circle cx="24" cy="24" r="2" fill="#DD4B39"/>
              </svg>
              <h4>Watcher haunts on schedule</h4>
              <p>
                Choose how often to check: every 15 minutes, hourly, or daily. 
                Watcher visits the site automatically, even while you sleep.
              </p>
            </div>

            <div className="feature">
              <svg className="feature-svg" width="48" height="48" viewBox="0 0 48 48" fill="none">
                <path d="M12 24c0-6.627 5.373-12 12-12s12 5.373 12 12" stroke="#3366CC" strokeWidth="2" strokeLinecap="round" fill="none"/>
                <circle cx="24" cy="24" r="4" fill="#DD4B39"/>
                <path d="M16 32l8-8 8 8" stroke="#777777" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <h4>AI spots real changes</h4>
              <p>
                Not every pixel change matters. AI understands your intent and only 
                alerts you to meaningful updates—no noise, just signal.
              </p>
            </div>

            <div className="feature">
              <svg className="feature-svg" width="48" height="48" viewBox="0 0 48 48" fill="none">
                <rect x="10" y="14" width="28" height="20" rx="2" stroke="#3366CC" strokeWidth="2" fill="none"/>
                <path d="M10 20l14 8 14-8" stroke="#DD4B39" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <circle cx="36" cy="16" r="6" fill="#DD4B39" opacity="0.2"/>
                <text x="36" y="19" fontSize="8" fill="#DD4B39" textAnchor="middle" fontWeight="bold">!</text>
              </svg>
              <h4>Get notified your way</h4>
              <p>
                Email alerts land in your inbox. Or check the Google Reader-style 
                interface with keyboard shortcuts (J/K to navigate, M to mark read).
              </p>
            </div>

            <div className="feature">
              <svg className="feature-svg" width="48" height="48" viewBox="0 0 48 48" fill="none">
                <rect x="12" y="8" width="24" height="32" rx="2" stroke="#3366CC" strokeWidth="2" fill="none"/>
                <rect x="16" y="12" width="16" height="2" rx="1" fill="#777777"/>
                <rect x="16" y="18" width="12" height="2" rx="1" fill="#777777"/>
                <rect x="16" y="24" width="14" height="2" rx="1" fill="#777777"/>
                <path d="M20 32l3 3 6-6" stroke="#DD4B39" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <h4>Works on modern sites</h4>
              <p>
                Uses real browser automation (Playwright) to handle JavaScript-heavy 
                sites that traditional scrapers can't touch.
              </p>
            </div>

            <div className="feature">
              <svg className="feature-svg" width="48" height="48" viewBox="0 0 48 48" fill="none">
                <rect x="8" y="12" width="32" height="24" rx="2" stroke="#3366CC" strokeWidth="2" fill="none"/>
                <path d="M14 20h8M14 26h6M26 20h8M26 26h6" stroke="#777777" strokeWidth="1.5" strokeLinecap="round"/>
                <line x1="24" y1="16" x2="24" y2="32" stroke="#E5E5E5" strokeWidth="2"/>
              </svg>
              <h4>Organize like Google Reader</h4>
              <p>
                Three-panel layout, folders for grouping, RSS feeds, and those beloved 
                keyboard shortcuts. It's the Reader experience for website monitoring.
              </p>
            </div>
          </div>
        </section>

        <section className="reader-section">
          <div className="reader-comparison">
            <div className="comparison-side">
              <h4>Google Reader was...</h4>
              <ul className="comparison-list">
                <li>
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M8 2L10 6h4l-3 3 1 4-4-2-4 2 1-4-3-3h4l2-4z" fill="#3366CC"/>
                  </svg>
                  Three-panel layout for efficiency
                </li>
                <li>
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M8 2L10 6h4l-3 3 1 4-4-2-4 2 1-4-3-3h4l2-4z" fill="#3366CC"/>
                  </svg>
                  Keyboard shortcuts (J/K/M/S)
                </li>
                <li>
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M8 2L10 6h4l-3 3 1 4-4-2-4 2 1-4-3-3h4l2-4z" fill="#3366CC"/>
                  </svg>
                  Clean, information-dense design
                </li>
                <li>
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M8 2L10 6h4l-3 3 1 4-4-2-4 2 1-4-3-3h4l2-4z" fill="#3366CC"/>
                  </svg>
                  RSS feed aggregation
                </li>
                <li>
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M8 2L10 6h4l-3 3 1 4-4-2-4 2 1-4-3-3h4l2-4z" fill="#3366CC"/>
                  </svg>
                  Folder organization
                </li>
              </ul>
            </div>
            <div className="comparison-divider">
              <svg width="40" height="120" viewBox="0 0 40 120">
                <line x1="20" y1="0" x2="20" y2="120" stroke="#E5E5E5" strokeWidth="2"/>
                <circle cx="20" cy="60" r="12" fill="white" stroke="#DD4B39" strokeWidth="2"/>
                <path d="M16 60l3 3 5-6" stroke="#DD4B39" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <div className="comparison-side">
              <h4>Watcher adds...</h4>
              <ul className="comparison-list">
                <li>
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <circle cx="8" cy="8" r="6" fill="#DD4B39" opacity="0.2"/>
                    <path d="M8 5v3l2 2" stroke="#DD4B39" strokeWidth="1.5" strokeLinecap="round"/>
                  </svg>
                  Automatic website monitoring
                </li>
                <li>
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <circle cx="8" cy="8" r="6" fill="#DD4B39" opacity="0.2"/>
                    <path d="M8 5v3l2 2" stroke="#DD4B39" strokeWidth="1.5" strokeLinecap="round"/>
                  </svg>
                  AI-powered setup & alerts
                </li>
                <li>
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <circle cx="8" cy="8" r="6" fill="#DD4B39" opacity="0.2"/>
                    <path d="M8 5v3l2 2" stroke="#DD4B39" strokeWidth="1.5" strokeLinecap="round"/>
                  </svg>
                  Email notifications
                </li>
                <li>
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <circle cx="8" cy="8" r="6" fill="#DD4B39" opacity="0.2"/>
                    <path d="M8 5v3l2 2" stroke="#DD4B39" strokeWidth="1.5" strokeLinecap="round"/>
                  </svg>
                  Modern SPA support
                </li>
                <li>
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <circle cx="8" cy="8" r="6" fill="#DD4B39" opacity="0.2"/>
                    <path d="M8 5v3l2 2" stroke="#DD4B39" strokeWidth="1.5" strokeLinecap="round"/>
                  </svg>
                  Change detection intelligence
                </li>
              </ul>
            </div>
          </div>
          <p className="reader-tagline">
            Same beloved interface. New superpower: haunting any website.
          </p>
        </section>

        <section className="ai-section">
          <h3>AI does the heavy lifting</h3>
          <div className="ai-features">
            <div className="ai-feature">
              <div className="ai-icon">
                <svg width="56" height="56" viewBox="0 0 56 56" fill="none">
                  <circle cx="28" cy="28" r="24" fill="#3366CC" opacity="0.1"/>
                  <path d="M28 12v32M12 28h32" stroke="#3366CC" strokeWidth="3" strokeLinecap="round"/>
                  <circle cx="28" cy="28" r="6" fill="#DD4B39" opacity="0.3"/>
                  <circle cx="20" cy="20" r="3" fill="#3366CC"/>
                  <circle cx="36" cy="20" r="3" fill="#3366CC"/>
                  <circle cx="20" cy="36" r="3" fill="#3366CC"/>
                  <circle cx="36" cy="36" r="3" fill="#3366CC"/>
                </svg>
              </div>
              <h4>Natural language to code</h4>
              <p>
                Say "watch the price in the product details" and AI generates the 
                CSS selectors, normalization rules, and detection logic. No coding required.
              </p>
            </div>
            <div className="ai-feature">
              <div className="ai-icon">
                <svg width="56" height="56" viewBox="0 0 56 56" fill="none">
                  <rect x="12" y="16" width="32" height="24" rx="2" stroke="#3366CC" strokeWidth="2" fill="none"/>
                  <path d="M18 24h8M18 30h6M30 24h8M30 30h6" stroke="#777777" strokeWidth="1.5" strokeLinecap="round"/>
                  <path d="M28 40l-4 4h8l-4-4z" fill="#DD4B39"/>
                </svg>
              </div>
              <h4>Smart change detection</h4>
              <p>
                AI understands context. It knows the difference between a meaningful 
                price drop and a timestamp update, so you only get alerts that matter.
              </p>
            </div>
            <div className="ai-feature">
              <div className="ai-icon">
                <svg width="56" height="56" viewBox="0 0 56 56" fill="none">
                  <rect x="14" y="12" width="28" height="32" rx="2" stroke="#3366CC" strokeWidth="2" fill="none"/>
                  <rect x="18" y="18" width="20" height="3" rx="1.5" fill="#777777" opacity="0.3"/>
                  <rect x="18" y="24" width="16" height="3" rx="1.5" fill="#777777" opacity="0.3"/>
                  <rect x="18" y="30" width="18" height="3" rx="1.5" fill="#777777" opacity="0.3"/>
                  <circle cx="42" cy="38" r="8" fill="#DD4B39" opacity="0.2"/>
                  <text x="42" y="42" fontSize="10" fill="#DD4B39" textAnchor="middle" fontWeight="bold">AI</text>
                </svg>
              </div>
              <h4>Contextual summaries</h4>
              <p>
                Each alert includes an AI-generated summary explaining what changed 
                and why it matters, so you can decide at a glance if action is needed.
              </p>
            </div>
          </div>
        </section>

        <section className="use-cases-section">
          <h3>Who haunts with Watcher?</h3>
          <div className="use-cases">
            <div className="use-case">
              <span className="use-case-icon">👨‍💻</span>
              <strong>Developers</strong> monitor deployment status, API docs, 
              and service health dashboards
            </div>
            <div className="use-case">
              <span className="use-case-icon">💼</span>
              <strong>Job seekers</strong> catch new postings seconds after 
              they're posted and track application statuses
            </div>
            <div className="use-case">
              <span className="use-case-icon">🎓</span>
              <strong>Students</strong> grab course spots when enrollment opens 
              and track grade updates
            </div>
            <div className="use-case">
              <span className="use-case-icon">🛍️</span>
              <strong>Shoppers</strong> get notified when sold-out items restock 
              or prices drop
            </div>
          </div>
        </section>

        <section className="cta-section">
          <div className="cta-ghost">
            <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
              <path d="M40 12C27.85 12 18 21.85 18 34v30c0 2.21 1.79 4 4 4s4-1.79 4-4v-4c0-2.21 1.79-4 4-4s4 1.79 4 4v4c0 2.21 1.79 4 4 4s4-1.79 4-4v-4c0-2.21 1.79-4 4-4s4 1.79 4 4v4c0 2.21 1.79 4 4 4s4-1.79 4-4v-4c0-2.21 1.79-4 4-4s4 1.79 4 4v4c0 2.21 1.79 4 4 4s4-1.79 4-4V34c0-12.15-9.85-22-22-22z" fill="#DD4B39" opacity="0.15"/>
              <circle cx="32" cy="34" r="3" fill="#333333"/>
              <circle cx="48" cy="34" r="3" fill="#333333"/>
              <path d="M34 44c0 3.31 2.69 6 6 6s6-2.69 6-6" stroke="#333333" strokeWidth="2.5" strokeLinecap="round"/>
            </svg>
          </div>
          <h3>Start haunting today</h3>
          <p>Set up your first haunt in under a minute—no credit card required</p>
          <div className="cta-buttons">
            <Link to="/signup" className="cta-primary">Create free account</Link>
          </div>
        </section>

        <footer className="landing-footer">
          <div className="footer-content">
            <p className="footer-tagline">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" style={{verticalAlign: 'middle', marginRight: '8px'}}>
                <path d="M10 2C6.69 2 4 4.69 4 8v9c0 .55.45 1 1 1s1-.45 1-1v-1c0-.55.45-1 1-1s1 .45 1 1v1c0 .55.45 1 1 1s1-.45 1-1v-1c0-.55.45-1 1-1s1 .45 1 1v1c0 .55.45 1 1 1s1-.45 1-1v-1c0-.55.45-1 1-1s1 .45 1 1v1c0 .55.45 1 1 1s1-.45 1-1V8c0-3.31-2.69-6-6-6z" fill="#DD4B39" opacity="0.3"/>
                <circle cx="8" cy="8" r="1" fill="#333333"/>
                <circle cx="12" cy="8" r="1" fill="#333333"/>
              </svg>
              Watcher — Haunt the web, stay informed
            </p>
            <p className="footer-note">
              Inspired by Google Reader. Built for the modern web.
            </p>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default Landing;

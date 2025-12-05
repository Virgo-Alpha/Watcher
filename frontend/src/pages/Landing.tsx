import React from 'react';
import { Link } from 'react-router-dom';
import './Landing.css';

const Landing: React.FC = () => {
  return (
    <div className="landing-container">
      <div className="landing-content">
        <header className="landing-header">
          <h1>Watcher</h1>
          <p className="tagline">Site change monitoring with a familiar interface</p>
        </header>

        <section className="hero-section">
          <h2>Never miss a website change again</h2>
          <p className="hero-description">
            Watcher monitors websites for changes you care about and delivers updates 
            through a clean, Google Reader-inspired interface.
          </p>
          <div className="cta-buttons">
            <Link to="/signup" className="cta-primary">Get started</Link>
            <Link to="/login" className="cta-secondary">Sign in</Link>
          </div>
        </section>

        <section className="features-section">
          <h3>What Watcher does</h3>
          <div className="features-grid">
            <div className="feature">
              <div className="feature-icon">🤖</div>
              <h4>Natural Language Setup</h4>
              <p>
                Describe what you want to monitor in plain English. 
                AI converts your description to technical selectors automatically.
              </p>
            </div>

            <div className="feature">
              <div className="feature-icon">⚡</div>
              <h4>Modern Web Compatible</h4>
              <p>
                Uses headless browser automation to monitor JavaScript-heavy 
                single-page applications that traditional scrapers can't handle.
              </p>
            </div>

            <div className="feature">
              <div className="feature-icon">📰</div>
              <h4>RSS Integration</h4>
              <p>
                Get changes as RSS feeds. Use Watcher's reader interface or 
                integrate with your favorite feed reader.
              </p>
            </div>

            <div className="feature">
              <div className="feature-icon">🎯</div>
              <h4>Smart Alerts</h4>
              <p>
                AI understands your intent and only alerts you to meaningful changes, 
                not every minor update.
              </p>
            </div>

            <div className="feature">
              <div className="feature-icon">📁</div>
              <h4>Organized Monitoring</h4>
              <p>
                Group related monitors in folders. Share public configurations 
                with the community.
              </p>
            </div>

            <div className="feature">
              <div className="feature-icon">⌨️</div>
              <h4>Keyboard Shortcuts</h4>
              <p>
                Navigate efficiently with J/K keys, mark items read with M, 
                star with S—just like the original.
              </p>
            </div>
          </div>
        </section>

        <section className="reader-section">
          <h3>The Google Reader connection</h3>
          <p>
            Remember Google Reader? That clean, efficient interface for consuming 
            information? We loved it too. When Google shut it down in 2013, 
            millions of users lost their favorite way to stay informed.
          </p>
          <p>
            Watcher brings back that familiar three-panel layout, keyboard shortcuts, 
            and information-dense design—but for monitoring website changes instead 
            of RSS feeds. It's the Reader experience applied to a new problem.
          </p>
        </section>

        <section className="use-cases-section">
          <h3>Who uses Watcher?</h3>
          <div className="use-cases">
            <div className="use-case">
              <strong>Developers</strong> monitor deployment status, API changes, 
              and service health dashboards
            </div>
            <div className="use-case">
              <strong>Job seekers</strong> track application statuses and new 
              job postings
            </div>
            <div className="use-case">
              <strong>Students</strong> watch for course enrollment openings, 
              grade updates, and academic deadlines
            </div>
            <div className="use-case">
              <strong>Everyone</strong> tracks product availability, price changes, 
              news updates, and more
            </div>
          </div>
        </section>

        <section className="cta-section">
          <h3>Start monitoring today</h3>
          <p>Set up your first monitor in under a minute</p>
          <div className="cta-buttons">
            <Link to="/signup" className="cta-primary">Create account</Link>
          </div>
        </section>

        <footer className="landing-footer">
          <p>Watcher — Haunt the web, stay informed</p>
        </footer>
      </div>
    </div>
  );
};

export default Landing;

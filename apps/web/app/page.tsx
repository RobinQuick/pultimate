"use client";

import Link from 'next/link';

export default function LandingPage() {
  return (
    <div className="landing-container">
      <header className="navbar">
        <div className="logo">⚡ Pultimate</div>
        <nav>
          <Link href="/login" className="nav-link">Sign In</Link>
          <Link href="/app/dashboard" className="btn-primary">Go to App</Link>
        </nav>
      </header>

      <main className="hero-section">
        <h1 className="hero-title">
          Perfect Decks,<br />
          <span className="highlight">Rebuilt Instantly.</span>
        </h1>
        <p className="hero-subtitle">
          Transform messy presentations into brand-compliant masterpieces.
          <br />No generative hallucinations. Just pure layout enforcement.
        </p>

        <div className="cta-group">
          <Link href="/demo" className="btn-demo">Start Live Demo</Link>
          <Link href="/app/dashboard" className="btn-secondary">Go to Dashboard</Link>
        </div>

        <div className="trust-badges">
          <span>🔒 NO-GEN Policy Enforced</span>
          <span>⚡ 100% Client-Side Private</span>
        </div>
      </main>

      <style jsx>{`
                .landing-container {
                    min-height: 100vh;
                    background: #fcfcfc;
                    display: flex;
                    flex-direction: column;
                    font-family: 'Inter', sans-serif;
                }
                .navbar {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 1.5rem 3rem;
                    max-width: 1200px;
                    margin: 0 auto;
                    width: 100%;
                }
                .logo { font-weight: 800; font-size: 1.5rem; letter-spacing: -0.02em; }
                .nav-link { color: #555; text-decoration: none; margin-right: 1.5rem; font-weight: 500; }
                .btn-primary { background: black; color: white; padding: 0.6rem 1.2rem; border-radius: 8px; text-decoration: none; font-weight: 500; }
                
                .hero-section {
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    text-align: center;
                    padding: 4rem 1rem;
                }
                .hero-title {
                    font-size: 4.5rem;
                    line-height: 1.1;
                    font-weight: 800;
                    margin-bottom: 1.5rem;
                    letter-spacing: -0.04em;
                }
                .highlight {
                    background: linear-gradient(90deg, #0070f3, #00c4ff);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }
                .hero-subtitle {
                    font-size: 1.25rem;
                    color: #666;
                    max-width: 600px;
                    line-height: 1.6;
                    margin-bottom: 3rem;
                }
                .cta-group {
                    display: flex;
                    gap: 1rem;
                    margin-bottom: 3rem;
                }
                .btn-demo {
                    background: linear-gradient(90deg, #0070f3, #00c4ff);
                    color: white;
                    padding: 1rem 2rem;
                    border-radius: 8px;
                    font-size: 1.1rem;
                    font-weight: 600;
                    text-decoration: none;
                    transition: transform 0.2s;
                }
                .btn-demo:hover { transform: scale(1.05); }
                .btn-secondary {
                    background: #f0f0f0;
                    color: #333;
                    padding: 1rem 2rem;
                    border-radius: 8px;
                    font-size: 1.1rem;
                    font-weight: 600;
                    text-decoration: none;
                }
                .trust-badges {
                    display: flex;
                    gap: 2rem;
                    color: #888;
                    font-size: 0.9rem;
                    font-weight: 500;
                }
            `}</style>
    </div>
  );
}

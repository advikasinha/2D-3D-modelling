// Home.tsx
import './Home.css';

function Home() {
  const navigateTo = (path: string) => {
    window.location.href = path;
  };

  return (
    <div className="home-container">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="logo-section">
            <div className="logo-icon">T</div>
            <h1 className="logo-text">TEB Project</h1>
          </div>
          <nav className="nav">
            <a href="#about" className="nav-link">About</a>
            <a href="#tools" className="nav-link">Tools</a>
            <a href="#team" className="nav-link">Team</a>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="hero">
        <div className="hero-content">
          <h2 className="hero-title">
            Advanced Engineering Design Platform
          </h2>
          <p className="hero-description">
            A comprehensive suite of tools for 3D modeling and computer-aided engineering analysis, 
            designed to streamline your engineering workflow.
          </p>
          <div className="hero-buttons">
            <a href="#tools" className="btn btn-primary">Explore Tools</a>
            <a href="#team" className="btn btn-secondary">Meet the Team</a>
          </div>
        </div>
      </section>

      {/* Tools Section */}
      <section id="tools" className="tools-section">
        <div className="section-content">
          <h3 className="section-title">Our Tools</h3>
          <div className="tools-grid">
            {/* 3D Modelling Tool */}
            <button onClick={() => navigateTo('/modelling')} className="tool-card">
              <div className="tool-icon">
                <svg className="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
              </div>
              <h4 className="tool-title">3D Modelling Tool</h4>
              <p className="tool-description">
                Create and manipulate complex 3D models with our intuitive modeling interface. 
                Perfect for rapid prototyping and detailed design work.
              </p>
              <div className="tool-link">
                Launch Tool
                <svg className="arrow-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </button>

            {/* CAE Analysis */}
            <button onClick={() => navigateTo('/cae')} className="tool-card">
              <div className="tool-icon">
                <svg className="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h4 className="tool-title">CAE Analysis</h4>
              <p className="tool-description">
                Perform comprehensive computer-aided engineering analysis. 
                Simulate real-world conditions and optimize your designs.
              </p>
              <div className="tool-link">
                Launch Tool
                <svg className="arrow-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </button>
          </div>
        </div>
      </section>

      {/* Team Section */}
      <section id="team" className="team-section">
        <div className="section-content">
          <h3 className="section-title">Development Team</h3>
          <p className="team-intro">
            This project was developed by a dedicated team of engineers committed to creating 
            powerful, accessible engineering tools.
          </p>
          <div className="team-grid">
            <div className="team-member">
              <div className="member-avatar">A</div>
              <h4 className="member-name">Advika</h4>
              <p className="member-role">Lead Developer</p>
            </div>
            <div className="team-member">
              <div className="member-avatar">A</div>
              <h4 className="member-name">Ayushi</h4>
              <p className="member-role">UI/UX Engineer</p>
            </div>
            <div className="team-member">
              <div className="member-avatar">A</div>
              <h4 className="member-name">Aaryan</h4>
              <p className="member-role">Systems Architect</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-content">
          <div className="footer-logo">
            <div className="footer-icon">T</div>
            <span className="footer-text">TEB Project</span>
          </div>
          <p className="footer-copyright">© 2024 TEB Project. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

export default Home;


/* Home.css */
import React, { useState, useEffect } from 'react';
import { collection, query, orderBy, onSnapshot, limit } from 'firebase/firestore';
import { db } from './firebase';
import { formatDistanceToNow } from 'date-fns';
import './index.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [password, setPassword] = useState('');
  const [jobs, setJobs] = useState([]);
  const [stats, setStats] = useState({ total: 0, applied: 0, skipped: 0 });

  // Extremely simple hardcoded auth as requested
  const handleLogin = (e) => {
    e.preventDefault();
    if (password === 'admin123') {
      setIsAuthenticated(true);
    } else {
      alert('Incorrect password');
    }
  };

  useEffect(() => {
    if (!isAuthenticated) return;

    // Listen to live Firestore data
    const q = query(
      collection(db, 'applications'),
      orderBy('timestamp', 'desc'),
      limit(100)
    );

    const unsubscribe = onSnapshot(q, (snapshot) => {
      const jobsData = [];
      let applied = 0;
      let skipped = 0;

      snapshot.forEach((doc) => {
        const data = doc.data();
        jobsData.push({ id: doc.id, ...data });

        if (data.status === 'Applied') applied++;
        else skipped++;
      });

      setJobs(jobsData);
      setStats({ total: jobsData.length, applied, skipped });
    });

    return () => unsubscribe();
  }, [isAuthenticated]);

  if (!isAuthenticated) {
    return (
      <div className="login-container">
        <div className="glass-panel login-panel">
          <h1>Automission</h1>
          <p className="subtitle">Bot Dashboard Login</p>
          <form onSubmit={handleLogin}>
            <input
              type="password"
              placeholder="Enter Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="password-input"
            />
            <button type="submit" className="login-btn">Access Dashboard</button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <header>
        <h1>LinkedIn Automission Live</h1>
        <p className="subtitle">Real-time bot execution monitoring</p>
      </header>

      <main>
        {/* Statistics Grid */}
        <section className="stats-grid">
          <div className="stat-card glass-panel">
            <h3>Total Processed</h3>
            <div className="value">{stats.total}</div>
          </div>
          <div className="stat-card glass-panel" style={{ borderColor: 'rgba(16, 185, 129, 0.3)' }}>
            <h3 style={{ color: 'var(--success)' }}>Applied</h3>
            <div className="value">{stats.applied}</div>
          </div>
          <div className="stat-card glass-panel" style={{ borderColor: 'rgba(245, 158, 11, 0.3)' }}>
            <h3 style={{ color: 'var(--skipped)' }}>Skipped/Failed</h3>
            <div className="value">{stats.skipped}</div>
          </div>
        </section>

        {/* Live Feed */}
        <section className="feed-container glass-panel">
          <div className="feed-header">
            <h2>Live Feed <span className="live-indicator"></span></h2>
            <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Showing last 100 actions</span>
          </div>

          <div className="job-list">
            {jobs.length === 0 ? (
              <div className="empty-state">
                <p>Waiting for bot signals...</p>
              </div>
            ) : (
              jobs.map((job) => (
                <div key={job.id} className="job-item">
                  <div className="job-info">
                    <div className="company">{job.company}</div>
                    <div className="title">
                      <a href={job.link} target="_blank" rel="noopener noreferrer">{job.job_title}</a>
                    </div>
                    <div className="time">
                      {job.timestamp ? formatDistanceToNow(job.timestamp.toDate(), { addSuffix: true }) : 'Just now'}
                    </div>
                  </div>
                  <div className={`status-badge ${job.status === 'Applied' ? 'status-applied' :
                      job.status.includes('Failed') ? 'status-failed' : 'status-skipped'
                    }`}>
                    {job.status}
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;

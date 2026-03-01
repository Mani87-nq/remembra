import { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { ApiKeyForm } from './components/ApiKeyForm';
import { Dashboard } from './pages/Dashboard';
import { api } from './lib/api';

function App() {
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    if (saved !== null) return saved === 'true';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    return !!api.getApiKey();
  });

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode);
    localStorage.setItem('darkMode', String(darkMode));
  }, [darkMode]);

  const handleToggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  const handleAuthenticated = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    api.clearApiKey();
    setIsAuthenticated(false);
  };

  if (!isAuthenticated) {
    return (
      <div className={darkMode ? 'dark' : ''}>
        <ApiKeyForm onAuthenticated={handleAuthenticated} />
      </div>
    );
  }

  return (
    <div className={darkMode ? 'dark' : ''}>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Header
          darkMode={darkMode}
          onToggleDarkMode={handleToggleDarkMode}
          isAuthenticated={isAuthenticated}
          onLogout={handleLogout}
        />
        <main>
          <Dashboard />
        </main>
      </div>
    </div>
  );
}

export default App;

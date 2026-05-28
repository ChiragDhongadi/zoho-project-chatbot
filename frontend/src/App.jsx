import React, { useState, useEffect } from 'react';
import LoginScreen from './components/LoginScreen';
import ChatWindow from './components/ChatWindow';

function App() {
  const [sessionId, setSessionId] = useState(localStorage.getItem('session_id') || null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 1. Check if the URL has an active session_id query parameter (from Zoho redirect!)
    const params = new URLSearchParams(window.location.search);
    const urlSession = params.get('session_id');

    if (urlSession) {
      localStorage.setItem('session_id', urlSession);
      setSessionId(urlSession);
      // Clean query parameter from address bar
      window.history.replaceState({}, document.title, window.location.pathname);
    }
    setLoading(false);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('session_id');
    setSessionId(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen text-indigo-400 font-medium">
        Loading Zoho Assistant...
      </div>
    );
  }

  return (
    <div className="relative w-full h-full flex items-center justify-center overflow-hidden">
      {/* Background Decorative Glowing Orbs */}
      <div className="glow-orb w-[400px] h-[400px] bg-indigo-600 top-[-100px] left-[-100px]"></div>
      <div className="glow-orb w-[500px] h-[500px] bg-purple-600 bottom-[-150px] right-[-100px]" style={{ animationDelay: '3s' }}></div>

      {sessionId ? (
        <ChatWindow sessionId={sessionId} onLogout={handleLogout} />
      ) : (
        <LoginScreen />
      )}
    </div>
  );
}

export default App;

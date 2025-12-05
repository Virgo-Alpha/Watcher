import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Landing from './pages/Landing';
import Login from './components/auth/Login';
import Signup from './components/auth/Signup';
import ProtectedRoute from './components/auth/ProtectedRoute';
import MainApp from './pages/MainApp';
import AuthErrorBoundary from './components/common/AuthErrorBoundary';
import './App.css';

function App() {
  return (
    <AuthErrorBoundary>
      <Routes>
        <Route path="/welcome" element={<div className="App"><Landing /></div>} />
        <Route path="/login" element={<div className="App"><Login /></div>} />
        <Route path="/signup" element={<div className="App"><Signup /></div>} />
        <Route
          path="/"
          element={
            <div className="App main-app">
              <ProtectedRoute>
                <MainApp />
              </ProtectedRoute>
            </div>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthErrorBoundary>
  );
}

export default App;
import React from 'react';
import ReactDOM from 'react-dom/client';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import './index.css';
import App from './App';
import { store } from './store';
import reportWebVitals from './reportWebVitals';
// Debug authentication issues
import './utils/authDebug';
import './tests/auth-flow.test';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

// Temporarily disable StrictMode to debug authentication issues
// StrictMode causes double-renders in development which might be clearing state
root.render(
  <Provider store={store}>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </Provider>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
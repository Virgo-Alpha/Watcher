import React, { useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../../hooks';
import { fetchCurrentUser } from '../../store/slices/authSlice';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const dispatch = useAppDispatch();
  const location = useLocation();
  const { isAuthenticated, loading, user } = useAppSelector((state) => state.auth);

  useEffect(() => {
    // If we have a token but no user data, fetch the current user
    if (isAuthenticated && !user && !loading) {
      console.log('[ProtectedRoute] Fetching current user...');
      console.log('[ProtectedRoute] Token in localStorage:', localStorage.getItem('accessToken') ? 'present' : 'missing');
      dispatch(fetchCurrentUser()).catch((error) => {
        console.error('[ProtectedRoute] Failed to fetch user:', error);
      });
    }
  }, [isAuthenticated, user, loading, dispatch]);

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh' 
      }}>
        <div>Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/welcome" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;

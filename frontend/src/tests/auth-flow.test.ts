/**
 * Manual test to verify authentication flow
 * Run this in browser console after logging in
 */

export const testAuthFlow = () => {
  console.log('=== Authentication Flow Test ===');
  
  // Check localStorage
  const accessToken = localStorage.getItem('accessToken');
  const refreshToken = localStorage.getItem('refreshToken');
  
  console.log('1. LocalStorage Check:');
  console.log('   accessToken:', accessToken ? `${accessToken.substring(0, 30)}...` : 'MISSING');
  console.log('   refreshToken:', refreshToken ? `${refreshToken.substring(0, 30)}...` : 'MISSING');
  
  // Check Redux state
  const state = (window as any).__REDUX_DEVTOOLS_EXTENSION__?.();
  console.log('2. Redux State:', state);
  
  // Try to make an authenticated request
  console.log('3. Testing API call...');
  fetch('http://localhost:8000/api/v1/auth/profile/', {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
  })
    .then(res => {
      console.log('   API Response Status:', res.status);
      return res.json();
    })
    .then(data => {
      console.log('   API Response Data:', data);
    })
    .catch(err => {
      console.error('   API Error:', err);
    });
  
  console.log('=== Test Complete ===');
};

// Make it available globally
(window as any).testAuthFlow = testAuthFlow;

console.log('Auth flow test loaded. Run testAuthFlow() in console to test.');

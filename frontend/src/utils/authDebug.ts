/**
 * Debug utility to track authentication state changes
 */

// Monitor localStorage changes
const originalSetItem = localStorage.setItem;
const originalRemoveItem = localStorage.removeItem;
const originalClear = localStorage.clear;

localStorage.setItem = function(key: string, value: string) {
  if (key === 'accessToken' || key === 'refreshToken') {
    console.log(`[localStorage] SET ${key}:`, value ? `${value.substring(0, 20)}...` : 'null');
    console.trace('[localStorage] Stack trace:');
  }
  return originalSetItem.apply(this, [key, value]);
};

localStorage.removeItem = function(key: string) {
  if (key === 'accessToken' || key === 'refreshToken') {
    console.warn(`[localStorage] REMOVE ${key}`);
    console.trace('[localStorage] Stack trace:');
  }
  return originalRemoveItem.apply(this, [key]);
};

localStorage.clear = function() {
  console.error('[localStorage] CLEAR ALL');
  console.trace('[localStorage] Stack trace:');
  return originalClear.apply(this);
};

// Log initial state
console.log('[authDebug] Initial localStorage state:');
console.log('[authDebug] accessToken:', localStorage.getItem('accessToken') ? 'present' : 'missing');
console.log('[authDebug] refreshToken:', localStorage.getItem('refreshToken') ? 'present' : 'missing');

export {};

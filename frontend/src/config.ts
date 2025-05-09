// API Configuration
export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:10000';

// Log the API URL in development
if (process.env.NODE_ENV === 'development') {
  console.log('API URL:', API_URL);
} 
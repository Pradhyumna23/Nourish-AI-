import axios from 'axios'
import { useAuthStore } from '../store/authStore'

// Create axios instance
const api = axios.create({
  // Use MongoDB production API with persistent storage
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8002/api/v1',  // MongoDB Production
  // baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8001/api/v1',  // Production with real data
  // baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',  // Demo with mock data
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const { token } = useAuthStore.getState()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const { logout } = useAuthStore.getState()
      logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  register: (userData) => api.post('/auth/register', userData),
  login: (credentials) => api.post('/auth/token', credentials),
  refreshToken: () => api.post('/auth/refresh'),
  getCurrentUser: () => api.get('/auth/me'),
}

// User API
export const userAPI = {
  getProfile: () => api.get('/users/profile'),
  updateProfile: (data) => api.put('/users/profile', data),
  addHealthCondition: (condition) => api.post('/users/health-conditions', condition),
  removeHealthCondition: (name) => api.delete(`/users/health-conditions/${name}`),
  addDietaryRestriction: (restriction) => api.post('/users/dietary-restrictions', restriction),
  removeDietaryRestriction: (type) => api.delete(`/users/dietary-restrictions/${type}`),
  addAllergy: (allergy) => api.post('/users/allergies', { allergy }),
  removeAllergy: (allergy) => api.delete(`/users/allergies/${allergy}`),
  deactivateAccount: () => api.delete('/users/profile'),
}

// Food API
export const foodAPI = {
  searchFoods: (query, pageSize = 20, pageNumber = 1) =>
    api.get('/foods/search', { params: { query, page_size: pageSize, page_number: pageNumber } }),
  getFoodDetails: (fdcId) => api.get(`/foods/${fdcId}`),
  logFood: (foodData) => api.post('/foods/log', foodData),
  getDailyNutrition: (date) => api.get('/foods/log/daily', { params: { target_date: date } }),
  getFoodHistory: (days = 7) => api.get('/foods/log/history', { params: { days } }),
  // Parse food description using Gemini AI
  parseFoodDescription: (description) =>
    api.post('/foods/parse', null, { params: { description } }),
}

// Nutrition API
export const nutritionAPI = {
  getProfile: () => api.get('/nutrition/profile'),
  createProfile: (data) => api.post('/nutrition/profile', data),
  updateProfile: (data) => api.put('/nutrition/profile', data),
  getDailyIntake: (date) => api.get('/nutrition/intake/daily', { params: { target_date: date } }),
  getProgress: (days = 30) => api.get('/nutrition/progress', { params: { days } }),
  getRecommendations: (date) => api.get('/nutrition/recommendations', { params: { target_date: date } }),
  getWeeklySummary: (weeks = 1) => api.get('/nutrition/weekly-summary', { params: { weeks } }),
}

// Recommendations API
export const recommendationsAPI = {
  generate: (request = {}) => api.post('/recommendations/generate', request),
  getRecommendations: (activeOnly = true, limit = 10) => 
    api.get('/recommendations/', { params: { active_only: activeOnly, limit } }),
  getRecommendation: (id) => api.get(`/recommendations/${id}`),
  submitFeedback: (id, feedback) => api.post(`/recommendations/${id}/feedback`, feedback),
  getStats: () => api.get('/recommendations/stats/summary'),
}

// Error handling utility
export const handleApiError = (error) => {
  if (error.response) {
    // Server responded with error status
    const message = error.response.data?.detail || 'An error occurred'
    return { message, status: error.response.status }
  } else if (error.request) {
    // Request was made but no response received
    return { message: 'Network error - please check your connection', status: 0 }
  } else {
    // Something else happened
    return { message: error.message || 'An unexpected error occurred', status: 0 }
  }
}

export { api }
export default api

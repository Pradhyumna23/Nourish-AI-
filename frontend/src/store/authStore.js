import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,

      login: (userData, token) => {
        set({
          user: userData,
          token: token,
          isAuthenticated: true,
          isLoading: false
        })
      },

      logout: () => {
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false
        })
      },

      updateUser: (userData) => {
        set((state) => ({
          user: { ...state.user, ...userData }
        }))
      },

      setLoading: (loading) => {
        set({ isLoading: loading })
      },

      // Check if token is expired
      isTokenExpired: () => {
        const { token } = get()
        if (!token) return true
        
        try {
          const payload = JSON.parse(atob(token.split('.')[1]))
          const currentTime = Date.now() / 1000
          return payload.exp < currentTime
        } catch (error) {
          return true
        }
      },

      // Initialize auth state from storage
      initialize: () => {
        const { token, isTokenExpired, logout } = get()
        if (token && isTokenExpired()) {
          logout()
        }
      }
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated
      })
    }
  )
)

export { useAuthStore }

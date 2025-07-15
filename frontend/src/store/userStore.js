import { create } from 'zustand'
import { userAPI, handleApiError } from '../services/api'

const useUserStore = create((set, get) => ({
  profile: null,
  isLoading: false,
  error: null,

  // Fetch user profile
  fetchProfile: async () => {
    set({ isLoading: true, error: null })
    try {
      const response = await userAPI.getProfile()
      set({ profile: response.data, isLoading: false })
      return response.data
    } catch (error) {
      const errorInfo = handleApiError(error)
      set({ error: errorInfo.message, isLoading: false })
      throw error
    }
  },

  // Update user profile
  updateProfile: async (data) => {
    set({ isLoading: true, error: null })
    try {
      const response = await userAPI.updateProfile(data)
      set({ profile: response.data, isLoading: false })
      return response.data
    } catch (error) {
      const errorInfo = handleApiError(error)
      set({ error: errorInfo.message, isLoading: false })
      throw error
    }
  },

  // Add health condition
  addHealthCondition: async (condition) => {
    set({ isLoading: true, error: null })
    try {
      const response = await userAPI.addHealthCondition(condition)
      set({ profile: response.data, isLoading: false })
      return response.data
    } catch (error) {
      const errorInfo = handleApiError(error)
      set({ error: errorInfo.message, isLoading: false })
      throw error
    }
  },

  // Remove health condition
  removeHealthCondition: async (name) => {
    set({ isLoading: true, error: null })
    try {
      const response = await userAPI.removeHealthCondition(name)
      set({ profile: response.data, isLoading: false })
      return response.data
    } catch (error) {
      const errorInfo = handleApiError(error)
      set({ error: errorInfo.message, isLoading: false })
      throw error
    }
  },

  // Add dietary restriction
  addDietaryRestriction: async (restriction) => {
    set({ isLoading: true, error: null })
    try {
      const response = await userAPI.addDietaryRestriction(restriction)
      set({ profile: response.data, isLoading: false })
      return response.data
    } catch (error) {
      const errorInfo = handleApiError(error)
      set({ error: errorInfo.message, isLoading: false })
      throw error
    }
  },

  // Remove dietary restriction
  removeDietaryRestriction: async (type) => {
    set({ isLoading: true, error: null })
    try {
      const response = await userAPI.removeDietaryRestriction(type)
      set({ profile: response.data, isLoading: false })
      return response.data
    } catch (error) {
      const errorInfo = handleApiError(error)
      set({ error: errorInfo.message, isLoading: false })
      throw error
    }
  },

  // Add allergy
  addAllergy: async (allergy) => {
    set({ isLoading: true, error: null })
    try {
      const response = await userAPI.addAllergy(allergy)
      set({ profile: response.data, isLoading: false })
      return response.data
    } catch (error) {
      const errorInfo = handleApiError(error)
      set({ error: errorInfo.message, isLoading: false })
      throw error
    }
  },

  // Remove allergy
  removeAllergy: async (allergy) => {
    set({ isLoading: true, error: null })
    try {
      const response = await userAPI.removeAllergy(allergy)
      set({ profile: response.data, isLoading: false })
      return response.data
    } catch (error) {
      const errorInfo = handleApiError(error)
      set({ error: errorInfo.message, isLoading: false })
      throw error
    }
  },

  // Clear error
  clearError: () => set({ error: null }),

  // Reset store
  reset: () => set({ profile: null, isLoading: false, error: null }),
}))

export { useUserStore }

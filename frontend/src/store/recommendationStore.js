import { create } from 'zustand'
import { recommendationsAPI, handleApiError } from '../services/api'

const useRecommendationStore = create((set, get) => ({
  // Recommendations list
  recommendations: [],
  isLoading: false,
  error: null,

  // Selected recommendation
  selectedRecommendation: null,
  isLoadingDetails: false,
  detailsError: null,

  // Generation
  isGenerating: false,
  generateError: null,

  // Stats
  stats: null,
  isLoadingStats: false,
  statsError: null,

  // Generate recommendations
  generateRecommendations: async (request = {}) => {
    set({ isGenerating: true, generateError: null })
    try {
      const response = await recommendationsAPI.generate(request)
      set({ 
        recommendations: response.data, 
        isGenerating: false 
      })
      return response.data
    } catch (error) {
      const errorInfo = handleApiError(error)
      set({ generateError: errorInfo.message, isGenerating: false })
      throw error
    }
  },

  // Get recommendations
  getRecommendations: async (activeOnly = true, limit = 10) => {
    set({ isLoading: true, error: null })
    try {
      const response = await recommendationsAPI.getRecommendations(activeOnly, limit)
      set({ 
        recommendations: response.data, 
        isLoading: false 
      })
      return response.data
    } catch (error) {
      const errorInfo = handleApiError(error)
      set({ error: errorInfo.message, isLoading: false })
      throw error
    }
  },

  // Get recommendation details
  getRecommendationDetails: async (id) => {
    set({ isLoadingDetails: true, detailsError: null })
    try {
      const response = await recommendationsAPI.getRecommendation(id)
      set({ 
        selectedRecommendation: response.data, 
        isLoadingDetails: false 
      })
      return response.data
    } catch (error) {
      const errorInfo = handleApiError(error)
      set({ detailsError: errorInfo.message, isLoadingDetails: false })
      throw error
    }
  },

  // Submit feedback
  submitFeedback: async (id, feedback) => {
    try {
      await recommendationsAPI.submitFeedback(id, feedback)
      
      // Update the recommendation in the list
      const { recommendations, selectedRecommendation } = get()
      
      const updatedRecommendations = recommendations.map(rec => 
        rec.id === id 
          ? { 
              ...rec, 
              is_accepted: feedback.is_accepted,
              user_rating: feedback.rating,
              is_viewed: true
            }
          : rec
      )
      
      const updatedSelected = selectedRecommendation?.id === id
        ? {
            ...selectedRecommendation,
            is_accepted: feedback.is_accepted,
            user_rating: feedback.rating,
            is_viewed: true
          }
        : selectedRecommendation

      set({ 
        recommendations: updatedRecommendations,
        selectedRecommendation: updatedSelected
      })
      
      return true
    } catch (error) {
      const errorInfo = handleApiError(error)
      throw new Error(errorInfo.message)
    }
  },

  // Get stats
  getStats: async () => {
    set({ isLoadingStats: true, statsError: null })
    try {
      const response = await recommendationsAPI.getStats()
      set({ 
        stats: response.data, 
        isLoadingStats: false 
      })
      return response.data
    } catch (error) {
      const errorInfo = handleApiError(error)
      set({ statsError: errorInfo.message, isLoadingStats: false })
      throw error
    }
  },

  // Mark recommendation as viewed
  markAsViewed: (id) => {
    const { recommendations, selectedRecommendation } = get()
    
    const updatedRecommendations = recommendations.map(rec => 
      rec.id === id ? { ...rec, is_viewed: true } : rec
    )
    
    const updatedSelected = selectedRecommendation?.id === id
      ? { ...selectedRecommendation, is_viewed: true }
      : selectedRecommendation

    set({ 
      recommendations: updatedRecommendations,
      selectedRecommendation: updatedSelected
    })
  },

  // Clear selected recommendation
  clearSelectedRecommendation: () => set({ 
    selectedRecommendation: null, 
    detailsError: null 
  }),

  // Clear errors
  clearErrors: () => set({ 
    error: null, 
    detailsError: null, 
    generateError: null, 
    statsError: null 
  }),

  // Reset store
  reset: () => set({
    recommendations: [],
    isLoading: false,
    error: null,
    selectedRecommendation: null,
    isLoadingDetails: false,
    detailsError: null,
    isGenerating: false,
    generateError: null,
    stats: null,
    isLoadingStats: false,
    statsError: null,
  }),
}))

export { useRecommendationStore }

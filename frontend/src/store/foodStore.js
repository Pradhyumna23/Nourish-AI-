import { create } from 'zustand'
import { foodAPI, handleApiError } from '../services/api'

const useFoodStore = create((set, get) => ({
  // Search state
  searchResults: [],
  searchQuery: '',
  isSearching: false,
  searchError: null,

  // Food details
  selectedFood: null,
  isFetchingFood: false,
  foodError: null,

  // Food logging
  isLogging: false,
  logError: null,

  // Daily nutrition
  dailyNutrition: null,
  isDailyLoading: false,
  dailyError: null,

  // Food history
  foodHistory: [],
  isHistoryLoading: false,
  historyError: null,

  // Search foods
  searchFoods: async (query, pageSize = 20, pageNumber = 1) => {
    if (!query.trim()) {
      set({ searchResults: [], searchQuery: '' })
      return
    }

    set({ isSearching: true, searchError: null, searchQuery: query })
    try {
      const response = await foodAPI.searchFoods(query, pageSize, pageNumber)
      set({ 
        searchResults: response.data.foods || [], 
        isSearching: false 
      })
      return response.data
    } catch (error) {
      const errorInfo = handleApiError(error)
      set({ searchError: errorInfo.message, isSearching: false })
      throw error
    }
  },

  // Get food details
  getFoodDetails: async (fdcId) => {
    set({ isFetchingFood: true, foodError: null })
    try {
      const response = await foodAPI.getFoodDetails(fdcId)
      set({ selectedFood: response.data, isFetchingFood: false })
      return response.data
    } catch (error) {
      const errorInfo = handleApiError(error)
      set({ foodError: errorInfo.message, isFetchingFood: false })
      throw error
    }
  },

  // Log food
  logFood: async (foodData) => {
    set({ isLogging: true, logError: null })
    try {
      const response = await foodAPI.logFood(foodData)
      set({ isLogging: false })
      
      // Refresh daily nutrition if it's for today
      const today = new Date().toISOString().split('T')[0]
      const logDate = new Date(foodData.date).toISOString().split('T')[0]
      if (logDate === today) {
        get().getDailyNutrition(today)
      }
      
      return response.data
    } catch (error) {
      const errorInfo = handleApiError(error)
      set({ logError: errorInfo.message, isLogging: false })
      throw error
    }
  },

  // Get daily nutrition
  getDailyNutrition: async (date) => {
    set({ isDailyLoading: true, dailyError: null })
    try {
      const response = await foodAPI.getDailyNutrition(date)
      set({ dailyNutrition: response.data, isDailyLoading: false })
      return response.data
    } catch (error) {
      const errorInfo = handleApiError(error)
      set({ dailyError: errorInfo.message, isDailyLoading: false })
      throw error
    }
  },

  // Get food history
  getFoodHistory: async (days = 7) => {
    set({ isHistoryLoading: true, historyError: null })
    try {
      const response = await foodAPI.getFoodHistory(days)
      set({ foodHistory: response.data, isHistoryLoading: false })
      return response.data
    } catch (error) {
      const errorInfo = handleApiError(error)
      set({ historyError: errorInfo.message, isHistoryLoading: false })
      throw error
    }
  },

  // Clear search
  clearSearch: () => set({ 
    searchResults: [], 
    searchQuery: '', 
    searchError: null 
  }),

  // Clear selected food
  clearSelectedFood: () => set({ 
    selectedFood: null, 
    foodError: null 
  }),

  // Clear errors
  clearErrors: () => set({ 
    searchError: null, 
    foodError: null, 
    logError: null, 
    dailyError: null, 
    historyError: null 
  }),

  // Reset store
  reset: () => set({
    searchResults: [],
    searchQuery: '',
    isSearching: false,
    searchError: null,
    selectedFood: null,
    isFetchingFood: false,
    foodError: null,
    isLogging: false,
    logError: null,
    dailyNutrition: null,
    isDailyLoading: false,
    dailyError: null,
    foodHistory: [],
    isHistoryLoading: false,
    historyError: null,
  }),
}))

export { useFoodStore }

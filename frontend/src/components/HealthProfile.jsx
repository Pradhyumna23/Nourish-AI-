import React, { useState, useEffect } from 'react'
import { userAPI } from '../services/api'
import Card from './ui/Card'
import Button from './ui/Button'
import LoadingSpinner from './ui/LoadingSpinner'

const HealthProfile = () => {
  const [profile, setProfile] = useState({
    dietary_restrictions: [],
    health_conditions: [],
    allergies: []
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [newRestriction, setNewRestriction] = useState('')
  const [newCondition, setNewCondition] = useState('')
  const [newAllergy, setNewAllergy] = useState('')

  const dietaryOptions = [
    'vegan', 'vegetarian', 'gluten_free', 'dairy_free', 'nut_free', 
    'keto', 'paleo', 'low_carb', 'low_fat', 'halal', 'kosher'
  ]

  const commonConditions = [
    'diabetes', 'hypertension', 'heart disease', 'high cholesterol',
    'anemia', 'osteoporosis', 'kidney disease', 'liver disease'
  ]

  const commonAllergies = [
    'peanuts', 'tree nuts', 'shellfish', 'fish', 'eggs', 'milk',
    'soy', 'wheat', 'sesame', 'sulfites'
  ]

  useEffect(() => {
    fetchProfile()
  }, [])

  const fetchProfile = async () => {
    try {
      setLoading(true)
      const response = await userAPI.getProfile()
      setProfile({
        dietary_restrictions: response.data.dietary_restrictions || [],
        health_conditions: response.data.health_conditions || [],
        allergies: response.data.allergies || []
      })
    } catch (error) {
      console.error('Failed to fetch profile:', error)
    } finally {
      setLoading(false)
    }
  }

  const addDietaryRestriction = async (type) => {
    try {
      setSaving(true)
      await userAPI.addDietaryRestriction({ type, severity: 'moderate' })
      await fetchProfile()
      setNewRestriction('')
    } catch (error) {
      console.error('Failed to add dietary restriction:', error)
    } finally {
      setSaving(false)
    }
  }

  const removeDietaryRestriction = async (type) => {
    try {
      setSaving(true)
      await userAPI.removeDietaryRestriction(type)
      await fetchProfile()
    } catch (error) {
      console.error('Failed to remove dietary restriction:', error)
    } finally {
      setSaving(false)
    }
  }

  const addHealthCondition = async (name) => {
    try {
      setSaving(true)
      await userAPI.addHealthCondition({ name, severity: 'moderate' })
      await fetchProfile()
      setNewCondition('')
    } catch (error) {
      console.error('Failed to add health condition:', error)
    } finally {
      setSaving(false)
    }
  }

  const addAllergy = async (allergy) => {
    try {
      setSaving(true)
      await userAPI.addAllergy({ allergy })
      await fetchProfile()
      setNewAllergy('')
    } catch (error) {
      console.error('Failed to add allergy:', error)
    } finally {
      setSaving(false)
    }
  }

  const removeAllergy = async (allergy) => {
    try {
      setSaving(true)
      await userAPI.removeAllergy(allergy)
      await fetchProfile()
    } catch (error) {
      console.error('Failed to remove allergy:', error)
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <Card className="p-6">
        <LoadingSpinner />
        <p className="text-center mt-4">Loading health profile...</p>
      </Card>
    )
  }

  return (
    <div className="space-y-4 sm:space-y-6 px-4">
      <div className="text-center">
        <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Health Profile</h2>
        <p className="text-gray-600 mt-2 text-sm sm:text-base">
          Manage your dietary restrictions, health conditions, and allergies for personalized recommendations
        </p>
      </div>

      {/* Dietary Restrictions */}
      <Card className="p-4 sm:p-6">
        <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-3 sm:mb-4">🌱 Dietary Restrictions</h3>

        <div className="flex flex-wrap gap-2 mb-3 sm:mb-4">
          {profile.dietary_restrictions.map((restriction, index) => (
            <span
              key={index}
              className="inline-flex items-center px-2 sm:px-3 py-1 rounded-full text-xs sm:text-sm bg-green-100 text-green-800"
            >
              <span className="truncate max-w-[120px] sm:max-w-none">{restriction.type || restriction}</span>
              <button
                onClick={() => removeDietaryRestriction(restriction.type || restriction)}
                className="ml-1 sm:ml-2 text-green-600 hover:text-green-800 flex-shrink-0"
                disabled={saving}
              >
                ×
              </button>
            </span>
          ))}
        </div>

        <div className="flex flex-wrap gap-2">
          {dietaryOptions
            .filter(option => !profile.dietary_restrictions.some(r => (r.type || r) === option))
            .map(option => (
              <button
                key={option}
                onClick={() => addDietaryRestriction(option)}
                disabled={saving}
                className="px-2 sm:px-3 py-1 text-xs sm:text-sm border border-gray-300 rounded-full hover:bg-gray-50 disabled:opacity-50 truncate"
              >
                + {option.replace('_', ' ')}
              </button>
            ))}
        </div>
      </Card>

      {/* Health Conditions */}
      <Card className="p-4 sm:p-6">
        <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-3 sm:mb-4">🏥 Health Conditions</h3>

        <div className="flex flex-wrap gap-2 mb-3 sm:mb-4">
          {profile.health_conditions.map((condition, index) => (
            <span
              key={index}
              className="inline-flex items-center px-2 sm:px-3 py-1 rounded-full text-xs sm:text-sm bg-red-100 text-red-800"
            >
              <span className="truncate max-w-[120px] sm:max-w-none">{condition.name || condition}</span>
              <button
                onClick={() => removeHealthCondition(condition.name || condition)}
                className="ml-1 sm:ml-2 text-red-600 hover:text-red-800 flex-shrink-0"
                disabled={saving}
              >
                ×
              </button>
            </span>
          ))}
        </div>

        <div className="flex flex-wrap gap-2">
          {commonConditions
            .filter(condition => !profile.health_conditions.some(c => (c.name || c) === condition))
            .map(condition => (
              <button
                key={condition}
                onClick={() => addHealthCondition(condition)}
                disabled={saving}
                className="px-2 sm:px-3 py-1 text-xs sm:text-sm border border-gray-300 rounded-full hover:bg-gray-50 disabled:opacity-50 truncate"
              >
                + {condition}
              </button>
            ))}
        </div>
      </Card>

      {/* Allergies */}
      <Card className="p-4 sm:p-6">
        <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-3 sm:mb-4">⚠️ Allergies</h3>

        <div className="flex flex-wrap gap-2 mb-3 sm:mb-4">
          {profile.allergies.map((allergy, index) => (
            <span
              key={index}
              className="inline-flex items-center px-2 sm:px-3 py-1 rounded-full text-xs sm:text-sm bg-yellow-100 text-yellow-800"
            >
              <span className="truncate max-w-[120px] sm:max-w-none">{allergy}</span>
              <button
                onClick={() => removeAllergy(allergy)}
                className="ml-1 sm:ml-2 text-yellow-600 hover:text-yellow-800 flex-shrink-0"
                disabled={saving}
              >
                ×
              </button>
            </span>
          ))}
        </div>

        <div className="flex flex-wrap gap-2">
          {commonAllergies
            .filter(allergy => !profile.allergies.includes(allergy))
            .map(allergy => (
              <button
                key={allergy}
                onClick={() => addAllergy(allergy)}
                disabled={saving}
                className="px-2 sm:px-3 py-1 text-xs sm:text-sm border border-gray-300 rounded-full hover:bg-gray-50 disabled:opacity-50 truncate"
              >
                + {allergy}
              </button>
            ))}
        </div>
      </Card>

      {/* Safety Information */}
      <Card className="p-4 sm:p-6 bg-blue-50 border-blue-200">
        <h3 className="text-base sm:text-lg font-semibold text-blue-900 mb-2">🛡️ How This Helps</h3>
        <ul className="text-blue-800 text-xs sm:text-sm space-y-1">
          <li>• Food recommendations are filtered based on your restrictions</li>
          <li>• Health condition-specific nutrition advice is provided</li>
          <li>• Allergy warnings prevent unsafe food suggestions</li>
          <li>• Personalized meal plans respect your dietary preferences</li>
        </ul>
      </Card>

      {saving && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg">
            <LoadingSpinner />
            <p className="text-center mt-4">Updating profile...</p>
          </div>
        </div>
      )}
    </div>
  )
}

export default HealthProfile

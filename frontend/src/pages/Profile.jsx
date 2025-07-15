import React, { useState, useEffect } from 'react'
import { useUserStore } from '../store/userStore'
import { useAuthStore } from '../store/authStore'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import LoadingSpinner from '../components/ui/LoadingSpinner'

const Profile = () => {
  const { user, updateUser } = useAuthStore()
  const {
    profile,
    isLoading,
    error,
    fetchProfile,
    updateProfile,
    addHealthCondition,
    removeHealthCondition,
    addDietaryRestriction,
    removeDietaryRestriction,
    addAllergy,
    removeAllergy,
    clearError
  } = useUserStore()

  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    age: '',
    gender: '',
    height_cm: '',
    weight_kg: '',
    target_weight_kg: '',
    activity_level: '',
    primary_goal: '',
    target_calories: ''
  })

  const [newHealthCondition, setNewHealthCondition] = useState({
    name: '',
    severity: 'mild',
    notes: ''
  })

  const [newDietaryRestriction, setNewDietaryRestriction] = useState({
    type: '',
    reason: '',
    strictness: 'moderate'
  })

  const [newAllergy, setNewAllergy] = useState('')
  const [isUpdating, setIsUpdating] = useState(false)

  useEffect(() => {
    fetchProfile()
  }, [fetchProfile])

  useEffect(() => {
    if (profile) {
      setFormData({
        first_name: profile.first_name || '',
        last_name: profile.last_name || '',
        email: profile.email || '',
        age: profile.age || '',
        gender: profile.gender || '',
        height_cm: profile.height_cm || '',
        weight_kg: profile.weight_kg || '',
        target_weight_kg: profile.target_weight_kg || '',
        activity_level: profile.activity_level || '',
        primary_goal: profile.primary_goal || '',
        target_calories: profile.target_calories || ''
      })
    }
  }, [profile])

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleUpdateProfile = async (e) => {
    e.preventDefault()
    setIsUpdating(true)
    clearError()

    try {
      // Prepare update data
      const updateData = { ...formData }

      // Convert numeric fields
      if (updateData.age) updateData.age = parseInt(updateData.age)
      if (updateData.height_cm) updateData.height_cm = parseFloat(updateData.height_cm)
      if (updateData.weight_kg) updateData.weight_kg = parseFloat(updateData.weight_kg)
      if (updateData.target_weight_kg) updateData.target_weight_kg = parseFloat(updateData.target_weight_kg)
      if (updateData.target_calories) updateData.target_calories = parseInt(updateData.target_calories)

      const updatedProfile = await updateProfile(updateData)

      // Update auth store with new user data
      updateUser(updatedProfile)

      alert('Profile updated successfully!')
    } catch (error) {
      console.error('Failed to update profile:', error)
    } finally {
      setIsUpdating(false)
    }
  }

  const handleAddHealthCondition = async (e) => {
    e.preventDefault()
    if (!newHealthCondition.name.trim()) return

    try {
      await addHealthCondition(newHealthCondition)
      setNewHealthCondition({ name: '', severity: 'mild', notes: '' })
    } catch (error) {
      console.error('Failed to add health condition:', error)
    }
  }

  const handleAddDietaryRestriction = async (e) => {
    e.preventDefault()
    if (!newDietaryRestriction.type.trim()) return

    try {
      await addDietaryRestriction(newDietaryRestriction)
      setNewDietaryRestriction({ type: '', reason: '', strictness: 'moderate' })
    } catch (error) {
      console.error('Failed to add dietary restriction:', error)
    }
  }

  const handleAddAllergy = async (e) => {
    e.preventDefault()
    if (!newAllergy.trim()) return

    try {
      await addAllergy(newAllergy.trim())
      setNewAllergy('')
    } catch (error) {
      console.error('Failed to add allergy:', error)
    }
  }

  if (isLoading && !profile) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <LoadingSpinner center text="Loading profile..." />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Profile Settings</h1>

      {error && (
        <div className="bg-danger-50 border border-danger-200 text-danger-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      <div className="space-y-6">
        {/* Personal Information */}
        <Card>
          <Card.Header>
            <Card.Title>Personal Information</Card.Title>
          </Card.Header>
          <Card.Content>
            <form onSubmit={handleUpdateProfile} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="First Name"
                  name="first_name"
                  value={formData.first_name}
                  onChange={handleInputChange}
                  required
                />
                <Input
                  label="Last Name"
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleInputChange}
                  required
                />
              </div>

              <Input
                label="Email"
                name="email"
                type="email"
                value={formData.email}
                onChange={handleInputChange}
                required
              />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Age"
                  name="age"
                  type="number"
                  min="13"
                  max="120"
                  value={formData.age}
                  onChange={handleInputChange}
                />

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Gender
                  </label>
                  <select
                    name="gender"
                    value={formData.gender}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  >
                    <option value="">Select gender</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Input
                  label="Height (cm)"
                  name="height_cm"
                  type="number"
                  min="100"
                  max="250"
                  value={formData.height_cm}
                  onChange={handleInputChange}
                />

                <Input
                  label="Current Weight (kg)"
                  name="weight_kg"
                  type="number"
                  min="20"
                  max="500"
                  step="0.1"
                  value={formData.weight_kg}
                  onChange={handleInputChange}
                />

                <Input
                  label="Target Weight (kg)"
                  name="target_weight_kg"
                  type="number"
                  min="20"
                  max="500"
                  step="0.1"
                  value={formData.target_weight_kg}
                  onChange={handleInputChange}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Activity Level
                  </label>
                  <select
                    name="activity_level"
                    value={formData.activity_level}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  >
                    <option value="">Select activity level</option>
                    <option value="sedentary">Sedentary (little/no exercise)</option>
                    <option value="lightly_active">Lightly Active (light exercise 1-3 days/week)</option>
                    <option value="moderately_active">Moderately Active (moderate exercise 3-5 days/week)</option>
                    <option value="very_active">Very Active (hard exercise 6-7 days/week)</option>
                    <option value="extremely_active">Extremely Active (very hard exercise, physical job)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Primary Goal
                  </label>
                  <select
                    name="primary_goal"
                    value={formData.primary_goal}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  >
                    <option value="">Select primary goal</option>
                    <option value="weight_loss">Weight Loss</option>
                    <option value="weight_gain">Weight Gain</option>
                    <option value="muscle_gain">Muscle Gain</option>
                    <option value="maintenance">Maintenance</option>
                    <option value="health_improvement">Health Improvement</option>
                  </select>
                </div>
              </div>

              <Input
                label="Target Daily Calories (optional)"
                name="target_calories"
                type="number"
                min="800"
                max="5000"
                value={formData.target_calories}
                onChange={handleInputChange}
                helperText="Leave empty to use AI-calculated recommendations"
              />

              <Button
                type="submit"
                loading={isUpdating}
                disabled={isUpdating}
              >
                Update Profile
              </Button>
            </form>
          </Card.Content>
        </Card>

        {/* Health Conditions */}
        <Card>
          <Card.Header>
            <Card.Title>Health Conditions</Card.Title>
          </Card.Header>
          <Card.Content>
            <div className="space-y-4">
              {profile?.health_conditions && profile.health_conditions.length > 0 && (
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Current Conditions:</h4>
                  <div className="space-y-2">
                    {profile.health_conditions.map((condition, index) => (
                      <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                        <div>
                          <span className="font-medium text-gray-900">{condition.name}</span>
                          <span className="text-sm text-gray-500 ml-2">({condition.severity})</span>
                          {condition.notes && (
                            <p className="text-sm text-gray-600 mt-1">{condition.notes}</p>
                          )}
                        </div>
                        <Button
                          size="sm"
                          variant="danger"
                          onClick={() => removeHealthCondition(condition.name)}
                        >
                          Remove
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <form onSubmit={handleAddHealthCondition} className="space-y-3">
                <h4 className="font-medium text-gray-900">Add Health Condition:</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <Input
                    placeholder="Condition name"
                    value={newHealthCondition.name}
                    onChange={(e) => setNewHealthCondition(prev => ({ ...prev, name: e.target.value }))}
                  />

                  <select
                    value={newHealthCondition.severity}
                    onChange={(e) => setNewHealthCondition(prev => ({ ...prev, severity: e.target.value }))}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  >
                    <option value="mild">Mild</option>
                    <option value="moderate">Moderate</option>
                    <option value="severe">Severe</option>
                  </select>

                  <Button type="submit" size="sm">Add</Button>
                </div>

                <Input
                  placeholder="Additional notes (optional)"
                  value={newHealthCondition.notes}
                  onChange={(e) => setNewHealthCondition(prev => ({ ...prev, notes: e.target.value }))}
                />
              </form>
            </div>
          </Card.Content>
        </Card>

        {/* Dietary Restrictions */}
        <Card>
          <Card.Header>
            <Card.Title>Dietary Restrictions</Card.Title>
          </Card.Header>
          <Card.Content>
            <div className="space-y-4">
              {profile?.dietary_restrictions && profile.dietary_restrictions.length > 0 && (
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Current Restrictions:</h4>
                  <div className="space-y-2">
                    {profile.dietary_restrictions.map((restriction, index) => (
                      <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                        <div>
                          <span className="font-medium text-gray-900">{restriction.type}</span>
                          <span className="text-sm text-gray-500 ml-2">({restriction.strictness})</span>
                          {restriction.reason && (
                            <p className="text-sm text-gray-600 mt-1">{restriction.reason}</p>
                          )}
                        </div>
                        <Button
                          size="sm"
                          variant="danger"
                          onClick={() => removeDietaryRestriction(restriction.type)}
                        >
                          Remove
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <form onSubmit={handleAddDietaryRestriction} className="space-y-3">
                <h4 className="font-medium text-gray-900">Add Dietary Restriction:</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <Input
                    placeholder="Restriction type (e.g., vegetarian)"
                    value={newDietaryRestriction.type}
                    onChange={(e) => setNewDietaryRestriction(prev => ({ ...prev, type: e.target.value }))}
                  />

                  <select
                    value={newDietaryRestriction.strictness}
                    onChange={(e) => setNewDietaryRestriction(prev => ({ ...prev, strictness: e.target.value }))}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  >
                    <option value="flexible">Flexible</option>
                    <option value="moderate">Moderate</option>
                    <option value="strict">Strict</option>
                  </select>

                  <Button type="submit" size="sm">Add</Button>
                </div>

                <Input
                  placeholder="Reason (optional)"
                  value={newDietaryRestriction.reason}
                  onChange={(e) => setNewDietaryRestriction(prev => ({ ...prev, reason: e.target.value }))}
                />
              </form>
            </div>
          </Card.Content>
        </Card>

        {/* Allergies */}
        <Card>
          <Card.Header>
            <Card.Title>Allergies</Card.Title>
          </Card.Header>
          <Card.Content>
            <div className="space-y-4">
              {profile?.allergies && profile.allergies.length > 0 && (
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Current Allergies:</h4>
                  <div className="flex flex-wrap gap-2">
                    {profile.allergies.map((allergy, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-danger-100 text-danger-800"
                      >
                        {typeof allergy === 'string' ? allergy : allergy.allergy || allergy.name || 'Unknown'}
                        <button
                          onClick={() => removeAllergy(typeof allergy === 'string' ? allergy : allergy.allergy || allergy.name)}
                          className="ml-2 text-danger-600 hover:text-danger-800"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <form onSubmit={handleAddAllergy} className="flex space-x-3">
                <Input
                  placeholder="Add allergy (e.g., peanuts)"
                  value={newAllergy}
                  onChange={(e) => setNewAllergy(e.target.value)}
                  className="flex-1"
                />
                <Button type="submit" size="sm">Add</Button>
              </form>
            </div>
          </Card.Content>
        </Card>
      </div>
    </div>
  )
}

export default Profile

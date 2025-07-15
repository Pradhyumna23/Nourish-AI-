import React, { useState, useEffect, useRef } from 'react'
import { useAuthStore } from '../store/authStore'
import Card from './ui/Card'
import Button from './ui/Button'
import Input from './ui/Input'
import LoadingSpinner from './ui/LoadingSpinner'

const Chatbot = ({ isOpen, onClose }) => {
  const { user } = useAuthStore()
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    if (isOpen && messages.length === 0) {
      loadChatHistory()
      // Add welcome message
      setMessages([{
        type: 'ai',
        content: `Hello ${user?.first_name || 'there'}! 👋 I'm NourishAI, your personal nutrition assistant. I can help you with meal planning, nutrition advice, food recommendations, and answer any questions about healthy eating. What would you like to know?`,
        timestamp: new Date().toISOString()
      }])
    }
  }, [isOpen, user])

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isOpen])

  const loadChatHistory = async () => {
    setIsLoadingHistory(true)
    try {
      const response = await fetch('http://localhost:8002/api/v1/chat/history?limit=10')
      if (response.ok) {
        const data = await response.json()
        const historyMessages = data.chat_history.flatMap(chat => [
          {
            type: 'user',
            content: chat.user_message,
            timestamp: chat.timestamp
          },
          {
            type: 'ai',
            content: chat.ai_response,
            timestamp: chat.timestamp
          }
        ])
        if (historyMessages.length > 0) {
          setMessages(historyMessages)
        }
      }
    } catch (error) {
      console.error('Failed to load chat history:', error)
    } finally {
      setIsLoadingHistory(false)
    }
  }

  const sendMessage = async (e) => {
    e.preventDefault()
    if (!inputMessage.trim() || isLoading) return

    const userMessage = {
      type: 'user',
      content: inputMessage.trim(),
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    try {
      const response = await fetch('http://localhost:8002/api/v1/chat/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage.content
        })
      })

      if (response.ok) {
        const data = await response.json()
        const aiMessage = {
          type: 'ai',
          content: data.response,
          timestamp: data.timestamp,
          contextUsed: data.context_used
        }
        setMessages(prev => [...prev, aiMessage])
      } else {
        throw new Error('Failed to get AI response')
      }
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage = {
        type: 'ai',
        content: "I'm sorry, I'm having trouble responding right now. Please try again in a moment.",
        timestamp: new Date().toISOString(),
        isError: true
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }

  const clearChat = () => {
    setMessages([{
      type: 'ai',
      content: `Hello ${user?.first_name || 'there'}! 👋 I'm NourishAI, your personal nutrition assistant. How can I help you today?`,
      timestamp: new Date().toISOString()
    }])
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl h-[600px] flex flex-col animate-fadeInUp">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white p-6 rounded-t-2xl flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
              <span className="text-2xl">🤖</span>
            </div>
            <div>
              <h2 className="text-xl font-bold">NourishAI Assistant</h2>
              <p className="text-purple-100 text-sm">Your personal nutrition expert</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Button
              onClick={clearChat}
              variant="ghost"
              className="text-white hover:bg-white/20 p-2"
              title="Clear chat"
            >
              🗑️
            </Button>
            <Button
              onClick={onClose}
              variant="ghost"
              className="text-white hover:bg-white/20 p-2"
              title="Close chat"
            >
              ✕
            </Button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
          {isLoadingHistory && (
            <div className="flex justify-center">
              <LoadingSpinner text="Loading chat history..." />
            </div>
          )}
          
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  message.type === 'user'
                    ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white'
                    : message.isError
                    ? 'bg-red-100 text-red-800 border border-red-200'
                    : 'bg-white text-gray-800 shadow-md border border-gray-200'
                }`}
              >
                <div className="whitespace-pre-wrap">{message.content}</div>
                <div
                  className={`text-xs mt-2 ${
                    message.type === 'user'
                      ? 'text-purple-100'
                      : 'text-gray-500'
                  }`}
                >
                  {formatTime(message.timestamp)}
                  {message.contextUsed && (
                    <span className="ml-2 text-green-600">📊 Personalized</span>
                  )}
                </div>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white rounded-2xl px-4 py-3 shadow-md border border-gray-200">
                <div className="flex items-center space-x-2">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-purple-600 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                  <span className="text-gray-600 text-sm">NourishAI is thinking...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-gray-200 bg-white rounded-b-2xl">
          <form onSubmit={sendMessage} className="flex space-x-3">
            <Input
              ref={inputRef}
              type="text"
              placeholder="Ask me about nutrition, meal planning, or healthy eating..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              disabled={isLoading}
              className="flex-1"
            />
            <Button
              type="submit"
              disabled={!inputMessage.trim() || isLoading}
              variant="gradient"
              className="px-6"
            >
              {isLoading ? '⏳' : '📤'}
            </Button>
          </form>
          <div className="mt-2 flex flex-wrap gap-2">
            {[
              "What should I eat for breakfast?",
              "Help me plan a healthy meal",
              "I need more protein in my diet",
              "What are good snack options?"
            ].map((suggestion, index) => (
              <button
                key={index}
                onClick={() => setInputMessage(suggestion)}
                className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded-full transition-colors"
                disabled={isLoading}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Chatbot

import React from 'react'

function TestApp() {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1 style={{ color: 'blue' }}>🍎 NourishAI Test Page</h1>
      <p>If you can see this, React is working!</p>
      <div style={{ 
        backgroundColor: '#f0f0f0', 
        padding: '20px', 
        borderRadius: '8px',
        marginTop: '20px'
      }}>
        <h2>System Status:</h2>
        <ul>
          <li>✅ React App Loading</li>
          <li>✅ JavaScript Working</li>
          <li>✅ CSS Styling Applied</li>
        </ul>
      </div>
      <button 
        style={{
          backgroundColor: '#007bff',
          color: 'white',
          padding: '10px 20px',
          border: 'none',
          borderRadius: '5px',
          marginTop: '20px',
          cursor: 'pointer'
        }}
        onClick={() => alert('Button clicked! React events are working.')}
      >
        Test Button
      </button>
    </div>
  )
}

export default TestApp

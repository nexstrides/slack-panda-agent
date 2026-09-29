import { useState, useEffect } from 'react'
import './App.css'

interface StatusResponse {
  status: string
  service?: string
}

function App() {
  const [apiStatus, setApiStatus] = useState<string>('checking...')
  const [userMessage, setUserMessage] = useState<string>('')
  const [response, setResponse] = useState<string>('')

  useEffect(() => {
    checkApiHealth()
  }, [])

  const checkApiHealth = async () => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const res = await fetch(`${apiUrl}/health`)
      const data: StatusResponse = await res.json()
      setApiStatus(data.status)
    } catch (error) {
      setApiStatus('disconnected')
    }
  }

  const handleSendMessage = async () => {
    if (!userMessage.trim()) return

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const res = await fetch(`${apiUrl}/echo`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: userMessage }),
      })

      const data = await res.json()
      setResponse(data.response)
      setUserMessage('')
    } catch (error) {
      setResponse('Error sending message')
    }
  }

  return (
    <div className="container">
      <header className="header">
        <h1>🐼 PandaAgent</h1>
        <p>Slack AI Agent Control Panel</p>
      </header>

      <div className="status-section">
        <h2>Status</h2>
        <div className={`status-badge ${apiStatus === 'ok' ? 'connected' : 'disconnected'}`}>
          {apiStatus === 'ok' ? '✓ Connected' : '✗ Disconnected'}
        </div>
        <p className="status-text">API Status: {apiStatus}</p>
      </div>

      <div className="test-section">
        <h2>Test Message</h2>
        <div className="input-group">
          <input
            type="text"
            placeholder="Enter a message..."
            value={userMessage}
            onChange={(e) => setUserMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
          />
          <button onClick={handleSendMessage}>Send</button>
        </div>

        {response && (
          <div className="response-box">
            <h3>Response:</h3>
            <p>{response}</p>
          </div>
        )}
      </div>

      <div className="info-section">
        <h2>Features (MVP)</h2>
        <ul>
          <li>✅ Respond to mentions in Slack channels</li>
          <li>✅ Process slash commands</li>
          <li>✅ Echo responses (basic validation)</li>
          <li>✅ Notification system for mentions</li>
          <li>🔄 Claude AI integration (coming soon)</li>
        </ul>
      </div>

      <footer className="footer">
        <p>PandaAgent v0.1.0 - Slack AI Agent</p>
      </footer>
    </div>
  )
}

export default App

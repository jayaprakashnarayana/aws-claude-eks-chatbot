import React, { useState, useEffect, useRef } from 'react'
import { Send, Bot, User, Trash2, Settings, Shield, Server, Compass } from 'lucide-react'
import './App.css'

function App() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I am Claude, deployed in AWS EKS. How can I help you today?'
    }
  ])
  const [input, setInput] = useState('')
  const [systemPrompt, setSystemPrompt] = useState('You are a helpful AI assistant.')
  const [config, setConfig] = useState({ provider: 'Loading...', model_id: 'Loading...', region: '' })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  
  const messagesEndRef = useRef(null)

  // Fetch backend configurations on mount
  useEffect(() => {
    fetch('/api/config')
      .then((res) => {
        if (!res.ok) throw new Error('Failed to fetch config')
        return res.json()
      })
      .then((data) => setConfig(data))
      .catch((err) => {
        console.error(err)
        setConfig({ provider: 'Error connecting', model_id: 'Unknown', region: 'Unknown' })
      })
  }, [])

  // Auto-scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Simple parser to render text, code snippets, paragraphs, and list items safely
  const renderMessageContent = (content) => {
    if (!content) return null
    
    // Check if there is code block
    const parts = content.split(/(```[\s\S]*?```)/g)
    
    return parts.map((part, index) => {
      if (part.startsWith('```') && part.endsWith('```')) {
        // Extract language and code
        const lines = part.slice(3, -3).trim().split('\n')
        const firstLine = lines[0].trim()
        const isLang = /^[a-zA-Z0-9_-]+$/.test(firstLine)
        const language = isLang ? firstLine : ''
        const code = isLang ? lines.slice(1).join('\n') : lines.join('\n')
        
        return (
          <pre key={index}>
            {language && <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '4px', textTransform: 'uppercase' }}>{language}</div>}
            <code>{code}</code>
          </pre>
        )
      }
      
      // Inline code rendering `code`
      const inlineParts = part.split(/(`[^`\n]+`)/g)
      return (
        <p key={index}>
          {inlineParts.map((subPart, subIndex) => {
            if (subPart.startsWith('`') && subPart.endsWith('`')) {
              return <code key={subIndex}>{subPart.slice(1, -1)}</code>
            }
            return subPart
          })}
        </p>
      )
    })
  }

  const handleSend = async (e) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage = { role: 'user', content: input.trim() }
    const updatedMessages = [...messages, userMessage]
    
    setMessages(updatedMessages)
    setInput('')
    setIsLoading(true)
    setError(null)

    // Add placeholder bot message that we will stream into
    const assistantMessageIndex = updatedMessages.length
    setMessages((prev) => [...prev, { role: 'assistant', content: '' }])

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: updatedMessages,
          system_prompt: systemPrompt
        })
      })

      if (!response.ok) {
        throw new Error(`Failed to initialize chat stream: ${response.statusText}`)
      }

      // Read SSE stream
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let done = false
      let botResponseAccumulator = ''

      while (!done) {
        const { value, done: doneReading } = await reader.read()
        done = doneReading
        if (value) {
          const chunk = decoder.decode(value, { stream: true })
          
          // SSE data format is "data: chunk_content\n\n"
          const lines = chunk.split('\n')
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const dataContent = line.slice(6).trim()
              
              if (dataContent.startsWith('[ERROR:')) {
                throw new Error(dataContent.slice(7, -1))
              }
              
              botResponseAccumulator += dataContent
              
              // Update assistant message in state
              setMessages((prev) => {
                const copy = [...prev]
                copy[assistantMessageIndex] = {
                  role: 'assistant',
                  content: botResponseAccumulator
                }
                return copy
              })
            }
          }
        }
      }
    } catch (err) {
      console.error(err)
      setError(err.message || 'Something went wrong')
      // Remove empty assistant placeholder if we failed immediately
      setMessages((prev) => {
        const copy = [...prev]
        if (copy[assistantMessageIndex] && copy[assistantMessageIndex].content === '') {
          return copy.slice(0, -1)
        }
        return copy
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleClearChat = () => {
    setMessages([
      {
        role: 'assistant',
        content: 'Chat history cleared. How can I help you today?'
      }
    ])
    setError(null)
  }

  return (
    <div className="app-container">
      {/* Sidebar Control Panel */}
      <aside className="sidebar glass-panel">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className="brand-section">
            <span className="brand-logo">💎</span>
            <div>
              <h1 className="brand-title">Antigravity AI</h1>
              <div style={{ fontSize: '0.65rem', color: 'var(--accent-secondary)', fontWeight: 'bold' }}>AWS CLOUD PORTAL</div>
            </div>
          </div>

          <div className="system-prompt-box">
            <label className="section-title" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Settings size={14} /> System Instruction
            </label>
            <textarea
              className="system-prompt-textarea"
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              placeholder="Provide system instructions for Claude..."
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <span className="section-title" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Server size={14} /> Cluster Details
            </span>
            <div className="info-card">
              <div className="info-item">
                <span className="info-label">EKS Host:</span>
                <span className="info-value" style={{ fontFamily: 'monospace' }}>aws-eks-node-group</span>
              </div>
              <div className="info-item">
                <span className="info-label">Provider:</span>
                <span className="info-value">{config.provider}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Model:</span>
                <span className="info-value" style={{ fontSize: '0.75rem', fontFamily: 'monospace' }}>
                  {config.model_id.split('/').pop() || config.model_id}
                </span>
              </div>
              {config.region && (
                <div className="info-item">
                  <span className="info-label">Region:</span>
                  <span className="info-value">{config.region}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div className="connection-badge">
            <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: '#10b981', display: 'inline-block' }}></span>
            Secured via AWS IAM & KMS
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Shield size={12} /> Data is encrypted in transit
          </div>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="chat-main glass-panel">
        <header className="chat-header">
          <div className="chat-header-info">
            <h2 className="chat-header-title">Claude 3.5 Sonnet</h2>
            <div className="chat-header-status">Deployed in Private VPC Subnets</div>
          </div>
          <button className="clear-btn" onClick={handleClearChat} title="Clear conversation history">
            <Trash2 size={16} /> Clear Chat
          </button>
        </header>

        {/* Chat Messages Log */}
        <section className="chat-messages">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message-row ${msg.role}`}>
              {msg.role === 'assistant' && (
                <div className="avatar bot">
                  <Bot size={18} color="white" />
                </div>
              )}
              <div className="message-bubble">
                {renderMessageContent(msg.content)}
              </div>
              {msg.role === 'user' && (
                <div className="avatar">
                  <User size={18} color="white" />
                </div>
              )}
            </div>
          ))}

          {isLoading && messages[messages.length - 1]?.content === '' && (
            <div className="message-row assistant">
              <div className="avatar bot">
                <Bot size={18} color="white" />
              </div>
              <div className="message-bubble" style={{ display: 'flex', alignItems: 'center', minHeight: '44px' }}>
                <div className="typing-indicator">
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div style={{ padding: '12px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: '8px', color: '#f87171', display: 'flex', gap: '8px', fontSize: '0.85rem' }}>
              <span>⚠️</span>
              <div>
                <strong>Error details:</strong> {error}
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </section>

        {/* Chat Input form */}
        <footer className="chat-input-container">
          <form className="input-form" onSubmit={handleSend}>
            <input
              type="text"
              className="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask Claude anything..."
              disabled={isLoading}
            />
            <button type="submit" className="send-button" disabled={!input.trim() || isLoading}>
              <Send size={18} />
            </button>
          </form>
        </footer>
      </main>
    </div>
  )
}

export default App

import { useCallback, useEffect, useRef, useState } from 'react'
import { askQuestion, clearChat, deleteDocument, getChat, getDocuments, uploadDocument } from './services/api'

function Glyph({ children, className = '' }) { return <span aria-hidden="true" className={`inline-flex items-center justify-center ${className}`}>{children}</span> }
function shortDate(value) { return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' }).format(new Date(value)) }
function prettySize(bytes = 0) { return bytes < 1024 * 1024 ? `${Math.max(1, Math.round(bytes / 1024))} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB` }

export default function App() {
  const [documents, setDocuments] = useState([])
  const [selectedId, setSelectedId] = useState(() => localStorage.getItem('papertrail.documentId') || '')
  const [messages, setMessages] = useState([])
  const [question, setQuestion] = useState('')
  const [loadingDocs, setLoadingDocs] = useState(true)
  const [loadingChat, setLoadingChat] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [asking, setAsking] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [menuId, setMenuId] = useState('')
  const fileInput = useRef(null)
  const bottomRef = useRef(null)
  const selected = documents.find((document) => document._id === selectedId)
  const selectedStatus = selected?.status

  const refreshDocuments = useCallback(async () => {
    setLoadingDocs(true)
    try {
      const result = await getDocuments()
      setDocuments(result.data)
      setSelectedId((current) => {
        const nextId = result.data.some((item) => item._id === current) ? current : (result.data[0]?._id || '')
        if (nextId) localStorage.setItem('papertrail.documentId', nextId)
        else localStorage.removeItem('papertrail.documentId')
        return nextId
      })
      setError('')
    } catch (cause) { setError(cause.message) }
    finally { setLoadingDocs(false) }
  }, [])

  useEffect(() => { refreshDocuments() }, [refreshDocuments])
  useEffect(() => {
    const timer = window.setInterval(async () => {
      if (!documents.some((document) => document.status === 'processing')) return
      try {
        const result = await getDocuments()
        setDocuments(result.data)
      } catch { /* The next poll can recover from a temporary API error. */ }
    }, 2000)
    return () => window.clearInterval(timer)
  }, [documents])
  useEffect(() => {
    if (!selectedId) { setMessages([]); return }
    if (selectedStatus !== 'ready') { setMessages([]); setLoadingChat(false); return }
    let active = true
    setLoadingChat(true)
    getChat(selectedId).then((result) => { if (active) { setMessages(result.data); setError('') } })
      .catch((cause) => { if (active) setError(cause.message) })
      .finally(() => { if (active) setLoadingChat(false) })
    return () => { active = false }
  }, [selectedId, selectedStatus])
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }) }, [messages, asking])

  function selectDocument(id) {
    setSelectedId(id); localStorage.setItem('papertrail.documentId', id)
    setMessages([]); setError(''); setNotice(''); setMenuId('')
  }

  async function handleUpload(event) {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) { setError('Choose a PDF file to upload.'); return }
    if (file.size > 20 * 1024 * 1024) { setError('PDF files must be 20 MB or smaller.'); return }
    setUploading(true); setError(''); setNotice('')
    try {
      const result = await uploadDocument(file)
      await refreshDocuments()
      selectDocument(result.data._id)
      setNotice(`${file.name} is uploaded and processing. It will be ready to chat with shortly.`)
    } catch (cause) { setError(cause.message) }
    finally { setUploading(false) }
  }

  async function handleDelete(document) {
    if (!window.confirm(`Delete “${document.name}” and its chat history?`)) return
    setMenuId(''); setError('')
    try {
      await deleteDocument(document._id)
      setNotice(`Deleted ${document.name}.`)
      await refreshDocuments()
    } catch (cause) { setError(cause.message) }
  }

  async function handleAsk(event) {
    event.preventDefault()
    const text = question.trim()
    if (!selected || !text || asking) return
    setQuestion(''); setError(''); setNotice(''); setAsking(true)
    try {
      const result = await askQuestion(selected._id, text)
      setMessages((current) => [...current, result.data])
    } catch (cause) { setQuestion(text); setError(cause.message) }
    finally { setAsking(false) }
  }

  async function handleClear() {
    if (!selected || !messages.length) return
    try { await clearChat(selected._id); setMessages([]); setNotice('Conversation cleared.') }
    catch (cause) { setError(cause.message) }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#home" aria-label="Papertrail home"><span className="brand-mark">P</span><span>papertrail<span className="brand-dot">.</span></span></a>
        <div className="workspace-label"><span>WORKSPACE</span><span className="workspace-pill">PERSONAL</span></div>
        <button className="nav-item nav-active" type="button"><Glyph>▤</Glyph> Documents <span className="nav-count">{documents.length}</span></button>
        <div className="library-heading"><span>Your library</span><button type="button" className="icon-button small" aria-label="Upload a document" onClick={() => fileInput.current?.click()}>＋</button></div>
        <input ref={fileInput} type="file" accept="application/pdf,.pdf" className="sr-only" onChange={handleUpload} />
        <div className="document-list">
          {loadingDocs ? <div className="sidebar-loading"><span className="spinner" /> Loading library…</div> : documents.map((document) => (
            <div key={document._id} className={`document-row ${selectedId === document._id ? 'document-selected' : ''}`}>
              <button className="document-select" type="button" onClick={() => selectDocument(document._id)}>
                <span className="pdf-icon">PDF</span><span className="document-copy"><span className="document-name">{document.name}</span><span className="document-meta">{document.status === 'ready' ? `${document.pageCount} pages · ${shortDate(document.createdAt)}` : document.status}</span></span>
              </button>
              <button className="icon-button row-menu" type="button" aria-label={`Actions for ${document.name}`} onClick={() => setMenuId(menuId === document._id ? '' : document._id)}>···</button>
              {menuId === document._id && <div className="row-menu-pop"><button type="button" onClick={() => handleDelete(document)}>Delete document</button></div>}
            </div>
          ))}
          {!loadingDocs && documents.length === 0 && <div className="empty-library">Your library is empty.<br />Add a PDF to get started.</div>}
        </div>
        <div className="sidebar-bottom"><span className="avatar">PT</span><span className="profile-copy"><strong>My workspace</strong><small>Personal library</small></span><span className="online-dot" /></div>
      </aside>

      <main className="main-panel" id="home">
        <header className="topbar"><div className="breadcrumb"><span>Library</span><span className="crumb-sep">/</span><strong>{selected?.name || 'New conversation'}</strong></div><div className="topbar-actions"><span className="secure-indicator"><i /> Private workspace</span><button className="profile-button" type="button" aria-label="Profile">PT</button></div></header>
        <section className="conversation-page">
          <div className="conversation-heading"><div><div className="eyebrow"><span className="eyebrow-line" /> DOCUMENT ASSISTANT</div><h1>{selected ? selected.name : 'A little more clarity, page by page.'}</h1><p>{selected ? `${selected.pageCount} pages · ${prettySize(selected.size)} · Added ${shortDate(selected.createdAt)}` : 'Bring your documents in, and make space for better questions.'}</p></div>{selected && <button className="clear-button" type="button" onClick={handleClear} disabled={!messages.length}>Clear conversation</button>}</div>

          {(error || notice) && <div className={`toast ${error ? 'toast-error' : 'toast-success'}`} role={error ? 'alert' : 'status'}><span>{error ? '!' : '✓'}</span>{error || notice}<button type="button" aria-label="Dismiss" onClick={() => { setError(''); setNotice('') }}>×</button></div>}

          <div className="chat-stage">
            {!selected ? (
              <div className="welcome-card"><div className="welcome-icon"><Glyph>✳</Glyph></div><span className="welcome-kicker">YOUR PERSONAL READING SPACE</span><h2>Make every document<br />easier to understand.</h2><p>Upload a PDF and ask anything about it. Your conversations stay with each document, ready whenever you return.</p><button className="primary-button" type="button" onClick={() => fileInput.current?.click()} disabled={uploading}>{uploading ? <><span className="spinner light" /> Adding document…</> : <>＋ &nbsp;Add your first PDF</>}</button><span className="upload-hint">PDF · Up to 20 MB</span></div>
            ) : selected.status === 'processing' ? <div className="chat-loading"><span className="spinner" /> Preparing your document…</div> : selected.status === 'failed' ? <div className="chat-loading">This document could not be processed. {selected.processingError || 'Delete it and upload it again.'}</div> : loadingChat ? <div className="chat-loading"><span className="spinner" /> Loading your conversation…</div> : messages.length === 0 ? (
              <div className="first-question"><div className="assistant-avatar">✳</div><div><span className="message-label">PAPERTRAIL ASSISTANT</span><h2>Your document is ready.</h2><p>Ask a question, explore a detail, or get a summary. I’ll look for the answer in <strong>{selected.name}</strong>.</p><div className="suggestions"><button type="button" onClick={() => setQuestion('Summarize the main points of this document.')}>Summarize the main points <span>↗</span></button><button type="button" onClick={() => setQuestion('What are the most important details I should know?')}>What should I know? <span>↗</span></button></div></div></div>
            ) : (
              <div className="message-list">{messages.map((message) => <article className="exchange" key={message._id}><div className="user-message"><span className="user-avatar">You</span><div><span className="message-label">YOU <i>·</i> {shortDate(message.createdAt)}</span><p>{message.question}</p></div></div><div className="assistant-message"><div className="assistant-avatar">✳</div><div className="answer-content"><span className="message-label">PAPERTRAIL ASSISTANT</span><p>{message.answer}</p>{message.sources?.length > 0 && <details className="sources"><summary>Based on {message.sources.length} document {message.sources.length === 1 ? 'excerpt' : 'excerpts'}</summary><div className="source-list">{message.sources.map((source, index) => <blockquote key={`${message._id}-${source.chunkIndex}`}>Excerpt {index + 1}: {source.preview}</blockquote>)}</div></details>}</div></div></article>)}<div ref={bottomRef} /></div>
            )}
          </div>

          {selected?.status === 'ready' && <div className="composer-wrap"><form className="composer" onSubmit={handleAsk}><textarea value={question} onChange={(event) => setQuestion(event.target.value)} maxLength={2000} rows={1} placeholder={`Ask anything about ${selected.name}…`} aria-label="Your question" disabled={asking || uploading} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); event.currentTarget.form.requestSubmit() } }} /><div className="composer-bottom"><span><kbd>↵</kbd> to send <span className="key-divider">·</span> <kbd>⇧ ↵</kbd> for a new line</span><button className="send-button" type="submit" disabled={!question.trim() || asking} aria-label="Send question">{asking ? <span className="spinner light" /> : <Glyph>↑</Glyph>}</button></div></form><div className="composer-foot"><span>Answers are grounded in your selected document.</span><span>{question.length}/2000</span></div></div>}
          {asking && <div className="typing-indicator"><span className="assistant-avatar">✳</span><span className="typing-dots"><i /><i /><i /></span><span>Finding the relevant passages…</span></div>}
        </section>
        <footer className="page-footer"><span>Thoughtful answers, grounded in your documents.</span><span>AI can make mistakes. Verify important details in the source.</span></footer>
      </main>
    </div>
  )
}

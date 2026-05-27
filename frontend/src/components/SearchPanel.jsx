import { useState, useEffect } from 'react'

export default function SearchPanel({ onSearch, loading, defaultQuery = '' }) {
  const [input, setInput] = useState(defaultQuery)

  useEffect(() => {
    if (defaultQuery) setInput(defaultQuery)
  }, [defaultQuery])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (input.trim() && !loading) {
      onSearch(input.trim())
    }
  }

  return (
    <div className="search-panel">
      <h2>检索文献</h2>
      <form onSubmit={handleSubmit}>
        <div className="search-input-group">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="输入文学作品名称，如：离骚、红楼梦、滕王阁序..."
            disabled={loading}
          />
          <button type="submit" disabled={loading || !input.trim()}>
            {loading ? '检索中...' : '开始检索'}
          </button>
        </div>
      </form>
    </div>
  )
}

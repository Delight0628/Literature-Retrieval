import { useState, useRef } from 'react'
import SearchPanel from './components/SearchPanel'
import ModuleOverview from './components/ModuleOverview'
import ContentDetail from './components/ContentDetail'
import MatrixRain from './components/MatrixRain'
import { search, deepSearch } from './api'

function App() {
  const [query, setQuery] = useState('')
  const [modules, setModules] = useState([])
  const [selectedModule, setSelectedModule] = useState(null)
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [entered, setEntered] = useState(false)
  const detailRef = useRef(null)

  const handleHeroSearch = async (searchQuery) => {
    setQuery(searchQuery)
    setEntered(true)
    setLoading(true)
    setError('')
    setSelectedModule(null)
    setDetail(null)

    try {
      const result = await search(searchQuery)
      setModules(result.modules || [])
    } catch (err) {
      setError('搜索失败，请重试')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async (searchQuery) => {
    setQuery(searchQuery)
    setLoading(true)
    setError('')
    setSelectedModule(null)
    setDetail(null)

    try {
      const result = await search(searchQuery)
      setModules(result.modules || [])
    } catch (err) {
      setError('搜索失败，请重试')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleModuleSelect = async (moduleId) => {
    setSelectedModule(moduleId)
    setLoading(true)
    setError('')
    setDetail(null)

    try {
      const result = await deepSearch(query, moduleId)
      setDetail(result)
      setTimeout(() => {
        detailRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }, 100)
    } catch (err) {
      setError('获取详情失败，请重试')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleBack = () => {
    setEntered(false)
    setModules([])
    setDetail(null)
    setSelectedModule(null)
    setError('')
  }

  // 进入结果页
  if (entered) {
    return (
      <div className="app">
        <header className="header">
          <div className="header-inner">
            <img src="/lingnianlogo.png" alt="领念教育" className="header-logo" />
            <div className="header-text">
              <h1>文学知识检索系统</h1>
              <p>双层权威信息采集 · 结构化知识库 · 深度交互展示</p>
            </div>
            <button className="back-btn" onClick={handleBack}>返回首页</button>
          </div>
        </header>

        <div className="container">
          <SearchPanel onSearch={handleSearch} loading={loading} defaultQuery={query} />
          {error && <div className="error">{error}</div>}
          {modules.length > 0 && (
            <ModuleOverview modules={modules} selectedModule={selectedModule} onSelect={handleModuleSelect} />
          )}
          {loading && modules.length > 0 && <div className="loading">正在加载中</div>}
          <div ref={detailRef}>
            {detail && !loading && <ContentDetail detail={detail} query={query} />}
          </div>
        </div>
      </div>
    )
  }

  // Hero 首页
  return (
    <div className="hero-app">
      <MatrixRain />

      <nav className="hero-nav">
        <img src="/lingnianlogo.png" alt="领念教育" className="nav-logo" />
        <div className="nav-links">
          <a href="https://liet-ai.com/sy" target="_blank" rel="noopener noreferrer">首页</a>
          <a href="#">关于我们</a>
          <a href="#">联系我们</a>
        </div>
      </nav>

      <div className="hero-main">
        <div className="hero-badge">AI Powered Literary Research</div>

        <h1 className="hero-title">
          <span className="title-line">文学知识</span>
          <span className="title-line title-accent">检索系统</span>
        </h1>

        <p className="hero-desc">
          双层权威信息采集 · 结构化知识库 · 深度交互展示
        </p>

        <div className="hero-search-box">
          <div className="search-wrapper">
            <svg className="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8"/>
              <path d="m21 21-4.3-4.3"/>
            </svg>
            <input
              type="text"
              placeholder="输入文学作品名称，如：离骚、红楼梦、滕王阁序..."
              onKeyDown={(e) => {
                if (e.key === 'Enter' && e.target.value.trim()) {
                  handleHeroSearch(e.target.value.trim())
                }
              }}
            />
            <button className="hero-search-btn" onClick={() => {
              const input = document.querySelector('.hero-search-box input')
              if (input.value.trim()) handleHeroSearch(input.value.trim())
            }}>
              开始检索
            </button>
          </div>
        </div>

        <div className="hero-tags">
          {['离骚', '红楼梦', '滕王阁序', '唐诗', '宋词'].map(tag => (
            <span key={tag} className="tag" onClick={() => handleHeroSearch(tag)}>{tag}</span>
          ))}
        </div>

        <div className="hero-stats">
          <div className="stat">
            <span className="stat-number">10,000+</span>
            <span className="stat-label">文学作品</span>
          </div>
          <div className="stat-divider"></div>
          <div className="stat">
            <span className="stat-number">100+</span>
            <span className="stat-label">知识模块</span>
          </div>
          <div className="stat-divider"></div>
          <div className="stat">
            <span className="stat-number">AI</span>
            <span className="stat-label">智能检索</span>
          </div>
        </div>
      </div>

      <div className="hero-scroll-hint">
        <div className="scroll-arrow"></div>
      </div>

      <div className="hero-footer">
        <span>© 2026 领念教育 - AI同行 创享未来</span>
      </div>
    </div>
  )
}

export default App

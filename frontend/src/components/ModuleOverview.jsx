const MODULE_ICONS = {
  background: '史',
  author: '人',
  text: '文',
  art: '艺',
  famous: '句',
  influence: '传',
}

export default function ModuleOverview({ modules, selectedModule, onSelect }) {
  return (
    <div className="modules-section">
      <h2>知识模块</h2>
      <div className="modules-grid">
        {modules.map((mod) => (
          <div
            key={mod.id}
            className={`module-card ${selectedModule === mod.id ? 'active' : ''}`}
            onClick={() => onSelect(mod.id)}
          >
            <div className="module-icon">
              {MODULE_ICONS[mod.id] || '籍'}
            </div>
            <h3>{mod.name}</h3>
            <p className="summary">{mod.summary}</p>
            <p className="source">来源：{mod.source}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

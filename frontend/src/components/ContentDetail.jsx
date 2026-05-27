import { downloadDocument } from '../api'
import { useState } from 'react'

export default function ContentDetail({ detail, query }) {
  const [downloading, setDownloading] = useState(false)

  const handleDownload = async () => {
    setDownloading(true)
    try {
      await downloadDocument(query, detail.module.id, detail.content)
    } catch (err) {
      alert('下载失败，请重试')
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div className="detail-panel">
      <h2>{detail.module.name}</h2>

      <div className="detail-content">
        {detail.content || '暂无详细内容'}
      </div>

      {detail.images && detail.images.length > 0 && (
        <div className="detail-images">
          <h4>相关图片</h4>
          <div className="images-grid">
            {detail.images.map((img, idx) => (
              <img
                key={idx}
                src={img}
                alt="相关图片"
                onError={(e) => e.target.style.display = 'none'}
              />
            ))}
          </div>
        </div>
      )}

      {detail.sources && detail.sources.length > 0 && (
        <div className="detail-sources">
          <h4>参考来源</h4>
          {detail.sources.map((src, idx) => (
            <a key={idx} href={src.url} target="_blank" rel="noopener noreferrer">
              {src.name}
            </a>
          ))}
        </div>
      )}

      <button
        className="download-btn"
        onClick={handleDownload}
        disabled={downloading}
      >
        {downloading ? '下载中...' : '下载为 Word 文档'}
      </button>
    </div>
  )
}

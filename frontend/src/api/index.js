const API_BASE = '/api';

export async function search(query) {
  const resp = await fetch(`${API_BASE}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
  if (!resp.ok) throw new Error('搜索失败');
  return resp.json();
}

export async function deepSearch(query, moduleId) {
  const resp = await fetch(`${API_BASE}/search/deep`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, module_id: moduleId }),
  });
  if (!resp.ok) throw new Error('深度检索失败');
  return resp.json();
}

export async function downloadDocument(query, moduleId, content) {
  const resp = await fetch(`${API_BASE}/download`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, module_id: moduleId, content }),
  });
  if (!resp.ok) throw new Error('下载失败');
  const blob = await resp.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${query}_${moduleId}.docx`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  a.remove();
}

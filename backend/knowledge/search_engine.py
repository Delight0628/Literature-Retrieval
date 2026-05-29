"""本地检索引擎

基于关键词匹配 + TF-IDF 相关度排序
支持 jieba 中文分词（可选）
"""

import math
import re
from collections import Counter
from typing import Optional
from .local_store import load_work, load_index, search_index, list_works
from .schema import MODULE_TYPES, get_module_name


# 尝试导入 jieba，如果不可用则使用简单分词
try:
    import jieba
    HAS_JIEBA = True
except ImportError:
    HAS_JIEBA = False


def _tokenize(text: str) -> list[str]:
    """分词"""
    if HAS_JIEBA:
        return list(jieba.cut(text))
    else:
        # 简单分词：按标点和空格分割
        tokens = re.findall(r'[一-龥]+|[a-zA-Z]+|\d+', text)
        return tokens


def _compute_tf(tokens: list[str]) -> dict[str, float]:
    """计算词频（TF）"""
    counter = Counter(tokens)
    total = len(tokens)
    if total == 0:
        return {}
    return {word: count / total for word, count in counter.items()}


def _compute_idf(documents: list[list[str]]) -> dict[str, float]:
    """计算逆文档频率（IDF）"""
    doc_count = len(documents)
    if doc_count == 0:
        return {}

    # 统计每个词出现在多少文档中
    word_doc_count = Counter()
    for doc in documents:
        unique_words = set(doc)
        for word in unique_words:
            word_doc_count[word] += 1

    # 计算 IDF
    return {
        word: math.log(doc_count / (count + 1)) + 1
        for word, count in word_doc_count.items()
    }


def _compute_tfidf(tf: dict[str, float], idf: dict[str, float]) -> dict[str, float]:
    """计算 TF-IDF"""
    return {
        word: tf_val * idf.get(word, 1.0)
        for word, tf_val in tf.items()
    }


def _text_similarity(text1: str, text2: str) -> float:
    """计算两段文本的相似度"""
    tokens1 = _tokenize(text1)
    tokens2 = _tokenize(text2)

    if not tokens1 or not tokens2:
        return 0.0

    # 使用 Jaccard 相似度
    set1 = set(tokens1)
    set2 = set(tokens2)
    intersection = set1 & set2
    union = set1 | set2

    return len(intersection) / len(union) if union else 0.0


def search_works(query: str, top_k: int = 10) -> list[dict]:
    """搜索作品（泛化检索）

    返回匹配的作品列表，包含模块概要
    """
    # 从索引搜索
    results = search_index(query)

    # 如果索引搜索无结果，尝试全文搜索
    if not results:
        all_works = list_works()
        for work_id in all_works:
            work = load_work(work_id)
            if work:
                # 计算查询与作品的相似度
                full_text = f"{work.name} {work.author} {work.abstract}"
                for module in work.modules.values():
                    full_text += f" {module.content}"

                similarity = _text_similarity(query, full_text)
                if similarity > 0.1:  # 阈值
                    results.append({
                        "id": work.id,
                        "name": work.name,
                        "author": work.author,
                        "dynasty": work.dynasty,
                        "abstract": work.abstract[:200],
                        "tags": work.tags,
                        "module_ids": list(work.modules.keys()),
                        "similarity": similarity,
                    })

    # 按相关度排序
    results.sort(key=lambda x: x.get("similarity", 0), reverse=True)

    return results[:top_k]


def get_work_modules(work_id: str, module_id: Optional[str] = None) -> dict:
    """获取作品的模块内容

    Args:
        work_id: 作品ID
        module_id: 模块ID（可选，为None时返回所有模块）

    Returns:
        包含模块列表的字典
    """
    work = load_work(work_id)
    if not work:
        return {"error": f"未找到作品: {work_id}"}

    # 构建模块列表
    modules = []
    for mt in MODULE_TYPES:
        mid = mt["id"]
        module = work.get_module(mid)
        if module:
            modules.append({
                "id": mid,
                "name": mt["name"],
                "summary": module.content[:200] + "..." if len(module.content) > 200 else module.content,
                "source": module.sources[0].name if module.sources else "本地知识库",
                "source_url": module.sources[0].url if module.sources else "",
                "word_count": module.word_count,
            })
        else:
            modules.append({
                "id": mid,
                "name": mt["name"],
                "summary": "暂无概要信息",
                "source": "",
                "source_url": "",
                "word_count": 0,
            })

    return {
        "query": work.name,
        "work_id": work.id,
        "modules": modules,
    }


def get_module_detail(work_id: str, module_id: str) -> dict:
    """获取模块详细内容（深度检索）"""
    work = load_work(work_id)
    if not work:
        return {"error": f"未找到作品: {work_id}"}

    module = work.get_module(module_id)
    if not module:
        return {"error": f"未找到模块: {module_id}"}

    module_info = next(
        (m for m in MODULE_TYPES if m["id"] == module_id),
        {"id": module_id, "name": module_id, "keywords": []}
    )

    return {
        "module": {
            "id": module_id,
            "name": module_info["name"],
            "keywords": module_info.get("keywords", []),
        },
        "content": module.content,
        "sources": [
            {"name": s.name, "url": s.url}
            for s in module.sources
        ],
        "images": module.images,
        "word_count": module.word_count,
    }


def search_by_module(query: str, module_id: str, top_k: int = 5) -> list[dict]:
    """按模块类型搜索"""
    all_works = list_works()
    results = []

    for work_id in all_works:
        work = load_work(work_id)
        if not work:
            continue

        module = work.get_module(module_id)
        if not module:
            continue

        # 计算相关度
        similarity = _text_similarity(query, module.content)
        if similarity > 0.05:
            results.append({
                "work_id": work.id,
                "work_name": work.name,
                "module_id": module_id,
                "module_name": module.module_name,
                "content_preview": module.content[:200],
                "similarity": similarity,
            })

    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:top_k]

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
semantic_search.py - 语义搜索引擎

功能：
1. 使用sentence-transformers生成文本向量
2. 基于LanceDB进行向量相似度搜索
3. 支持多知识库联合检索
4. 自动更新索引

用法：
    python semantic_search.py --query "RPS选股策略"
    python semantic_search.py --query "低空经济" --top-k 10
    python semantic_search.py --build-index  # 重建索引
"""

import os
import sys
import json
import argparse
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional

# 路径配置
BASE_DIR = Path(__file__).parent.parent
WORKSPACE = BASE_DIR
MEMORY_DIR = WORKSPACE / "memory"
LANCE_DB_PATH = MEMORY_DIR / "lancedb"
EMBEDDINGS_DIR = WORKSPACE / "embeddings"

# 知识库目录
KNOWLEDGE_DIRS = [
    MEMORY_DIR,
    WORKSPACE / "workspace-investment" / "memory",
    WORKSPACE / "workspace-novel" / "memory",
    WORKSPACE / "workspace-social" / "memory",
    WORKSPACE / "workspace-math" / "memory",
    WORKSPACE / "workspace-maphot" / "memory",
    WORKSPACE / "workspace-weixin" / "memory",
]

class SemanticSearchEngine:
    """语义搜索引擎"""
    
    def __init__(self, model_name: str = "shibing624/text2vec-base-chinese"):
        self.model_name = model_name
        self.model = None
        self.index = None
        self.table = None
        
    def load_model(self):
        """加载 Embedding 模型"""
        print(f"加载模型: {self.model_name}")
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            print("模型加载成功")
            return True
        except Exception as e:
            print(f"模型加载失败: {e}")
            print("将使用TF-IDF降级方案")
            return False
    
    def build_index(self, force: bool = False):
        """构建向量索引"""
        print("="*60)
        print("开始构建向量索引")
        print("="*60)
        
        # 收集所有文档
        documents = []
        doc_ids = []
        
        for kb_dir in KNOWLEDGE_DIRS:
            if not kb_dir.exists():
                continue
            for root, dirs, files in os.walk(kb_dir):
                for f in files:
                    if not f.endswith('.md'):
                        continue
                    filepath = Path(root) / f
                    try:
                        with open(filepath, 'r', encoding='utf-8') as fh:
                            content = fh.read()
                        # 限制内容长度
                        if len(content) > 5000:
                            content = content[:5000]
                        
                        doc_id = str(filepath).replace('\\', '/').replace('/', '_')
                        documents.append({
                            'id': doc_id,
                            'path': str(filepath),
                            'content': content,
                            'source': kb_dir.name,
                            'updated': datetime.fromtimestamp(filepath.stat().st_mtime).isoformat()
                        })
                        doc_ids.append(doc_id)
                    except Exception as e:
                        print(f"读取失败: {filepath} - {e}")
        
        print(f"共收集 {len(documents)} 个文档")
        
        # 检查是否需要重建
        index_path = LANCE_DB_PATH / "knowledge.lance"
        if index_path.exists() and not force:
            print("索引已存在，使用--force强制重建")
            return
        
        # 生成向量
        print("生成向量...")
        texts = [doc['content'] for doc in documents]
        
        # 尝试使用Embedding模型
        use_model = self.model is not None
        
        if use_model:
            print("使用sentence-transformers生成向量")
            embeddings = self.model.encode(texts, show_progress_bar=True)
        else:
            # 降级方案：使用TF-IDF
            print("使用TF-IDF降级方案")
            from sklearn.feature_extraction.text import TfidfVectorizer
            vectorizer = TfidfVectorizer(max_features=1000)
            embeddings = vectorizer.fit_transform(texts).toarray()
        
        # 保存到LanceDB
        print("保存到LanceDB...")
        try:
            import lance
            data = []
            for i, doc in enumerate(documents):
                row = {
                    'id': doc['id'],
                    'path': doc['path'],
                    'content': doc['content'],
                    'source': doc['source'],
                    'updated': doc['updated'],
                    'vector': embeddings[i].tolist() if len(embeddings[i].shape) > 0 else [embeddings[i]]
                }
                data.append(row)
            
            os.makedirs(LANCE_DB_PATH, exist_ok=True)
            dataset = lance.write_dataset(data, str(index_path))
            self.table = dataset.to_table()
            print(f"索引构建完成: {len(data)} 条记录")
            
            # 保存元数据
            meta_path = LANCE_DB_PATH / "index_meta.json"
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'build_time': datetime.now().isoformat(),
                    'doc_count': len(data),
                    'model': self.model_name if use_model else 'tfidf',
                    'dimensions': len(embeddings[0]) if len(embeddings) > 0 else 0
                }, f, ensure_ascii=False, indent=2)
            
        except ImportError:
            print("LanceDB未安装，使用JSON降级方案")
            self._save_json_index(documents, embeddings)
    
    def _save_json_index(self, documents: List[Dict], embeddings: any):
        """JSON降级存储"""
        os.makedirs(EMBEDDINGS_DIR, exist_ok=True)
        
        # 保存向量
        vectors_path = EMBEDDINGS_DIR / "embeddings.npy"
        import numpy as np
        np.save(vectors_path, embeddings)
        
        # 保存文档映射
        meta_path = EMBEDDINGS_DIR / "doc_mapping.json"
        mapping = {doc['id']: doc for doc in documents}
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        
        print(f"向量已保存: {vectors_path}")
        print(f"映射已保存: {meta_path}")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """语义搜索"""
        if self.model is None:
            if not self.load_model():
                return self._tfidf_search(query, top_k)
        
        # 生成查询向量
        query_vec = self.model.encode([query])[0]
        
        # 加载索引
        index_path = LANCE_DB_PATH / "knowledge.lance"
        if index_path.exists():
            try:
                import lance
                dataset = lance.dataset(str(index_path))
                results = dataset.search(query_vec).limit(top_k).to_list()
                return results
            except ImportError:
                pass
        
        # 降级到JSON
        return self._json_search(query_vec, top_k)
    
    def _tfidf_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """TF-IDF降级搜索"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        
        # 加载文档
        documents = []
        for kb_dir in KNOWLEDGE_DIRS:
            if not kb_dir.exists():
                continue
            for root, dirs, files in os.walk(kb_dir):
                for f in files:
                    if f.endswith('.md'):
                        filepath = Path(root) / f
                        try:
                            with open(filepath, 'r', encoding='utf-8') as fh:
                                content = fh.read()
                            documents.append({
                                'path': str(filepath),
                                'content': content[:5000],
                                'source': kb_dir.name
                            })
                        except:
                            pass
        
        if not documents:
            return []
        
        # TF-IDF搜索
        vectorizer = TfidfVectorizer(max_features=1000)
        corpus = [doc['content'] for doc in documents]
        tfidf_matrix = vectorizer.fit_transform(corpus + [query])
        
        # 计算相似度
        similarities = cosine_similarity(tfidf_matrix[-1:], tfidf_matrix[:-1])[0]
        
        # 排序
        sorted_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in sorted_indices:
            results.append({
                'path': documents[idx]['path'],
                'score': float(similarities[idx]),
                'source': documents[idx]['source']
            })
        
        return results
    
    def _json_search(self, query_vec, top_k: int = 5) -> List[Dict]:
        """JSON降级搜索"""
        import numpy as np
        
        vectors_path = EMBEDDINGS_DIR / "embeddings.npy"
        meta_path = EMBEDDINGS_DIR / "doc_mapping.json"
        
        if not vectors_path.exists() or not meta_path.exists():
            return []
        
        embeddings = np.load(vectors_path)
        with open(meta_path, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
        
        # 余弦相似度
        similarities = np.dot(embeddings, query_vec) / (
            np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_vec)
        )
        
        # 排序
        sorted_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in sorted_indices:
            doc_id = list(mapping.keys())[idx]
            doc = mapping[doc_id]
            results.append({
                'path': doc['path'],
                'score': float(similarities[idx]),
                'source': doc.get('source', 'unknown')
            })
        
        return results
    
    def print_results(self, results: List[Dict], query: str):
        """打印搜索结果"""
        print(f"\n搜索: {query}")
        print(f"返回 {len(results)} 条结果:\n")
        
        for i, result in enumerate(results, 1):
            path = result.get('path', result.get('id', 'unknown'))
            score = result.get('score', 0)
            source = result.get('source', 'unknown')
            
            # 提取片段
            snippet = ""
            if 'path' in result:
                try:
                    with open(result['path'], 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 找关键词附近内容
                        idx = content.find(query[:4])
                        if idx >= 0:
                            start = max(0, idx - 50)
                            end = min(len(content), idx + 100)
                            snippet = content[start:end].replace('\n', ' ')
                        else:
                            snippet = content[:100] + "..."
                except:
                    snippet = "[读取失败]"
            
            print(f"{i}. [{source}] {path}")
            print(f"   相似度: {score:.4f}")
            if snippet:
                print(f"   摘要: {snippet[:80]}...")
            print()

def main():
    parser = argparse.ArgumentParser(description="语义搜索引擎")
    parser.add_argument("--query", type=str, help="搜索查询")
    parser.add_argument("--top-k", type=int, default=5, help="返回结果数")
    parser.add_argument("--build-index", action="store_true", help="构建索引")
    parser.add_argument("--force", action="store_true", help="强制重建索引")
    parser.add_argument("--model", type=str, default="shibing624/text2vec-base-chinese", 
                       help="Embedding模型名称")
    
    args = parser.parse_args()
    
    engine = SemanticSearchEngine(model_name=args.model)
    
    if args.build_index:
        engine.build_index(force=args.force)
    elif args.query:
        # 先加载索引
        index_path = LANCE_DB_PATH / "knowledge.lance"
        if not index_path.exists():
            meta_path = EMBEDDINGS_DIR / "index_meta.json"
            if meta_path.exists():
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                print(f"索引最后构建时间: {meta.get('build_time', 'unknown')}")
                print("索引已存在，直接搜索")
            else:
                print("索引不存在，自动构建...")
                engine.build_index()
        
        # 执行搜索
        results = engine.search(args.query, args.top_k)
        engine.print_results(results, args.query)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

# RAG（检索增强生成）面试指南

RAG（Retrieval-Augmented Generation，检索增强生成）是当前 AI Agent 和企业级 LLM 应用中最核心的技术架构之一。它通过在生成阶段引入外部知识检索，解决了 LLM 知识截止、幻觉和领域知识不足等问题。本章全面覆盖 RAG 的架构设计、关键组件、高级技术、评估方法和生产实践。

---

## 1. RAG 整体架构

RAG 系统的核心流程分为三个阶段：

```
Indexing（索引构建） → Retrieval（检索） → Generation（生成）
```

### 1.1 Indexing（索引阶段）

1. **文档加载**：从各类数据源读取原始文档
2. **文档处理**：清洗、格式化、去噪
3. **文本分块**：将长文档切分为合适大小的片段（Chunk）
4. **向量化**：使用 Embedding 模型将文本块转换为向量
5. **存储索引**：将向量和原始文本存入向量数据库

### 1.2 Retrieval（检索阶段）

1. **查询处理**：对用户查询进行优化（重写、扩展）
2. **向量检索**：将查询向量化，在向量数据库中检索相似文档
3. **混合检索**：结合向量检索和关键词检索
4. **重排序**：对检索结果进行精排，提升相关性
5. **结果筛选**：根据阈值和策略过滤低质量结果

### 1.3 Generation（生成阶段）

1. **上下文构造**：将检索到的文档片段组装到 Prompt 中
2. **LLM 生成**：基于增强后的 Prompt 生成回答
3. **后处理**：引用标注、格式化、事实核查

> **面试题：请描述一个完整 RAG 系统的数据流，从用户提问到返回答案的全过程。**
>
> 完整流程：用户输入查询 → 查询预处理（意图识别、查询改写）→ 查询向量化（Embedding Model）→ 向量数据库检索 Top-K 相似文档 → （可选）BM25 关键词检索 → 检索结果合并去重 → Reranker 重排序 → 取 Top-N 最相关文档 → 构造 Prompt（System Prompt + 检索文档 + 用户问题）→ LLM 生成回答 → 后处理（引用标注、安全检查）→ 返回用户。整个过程中需要处理的关键问题包括：分块质量、检索召回率、上下文长度限制、幻觉控制等。

---

## 2. 文档加载与处理

### 2.1 常见文档格式

| 格式 | 工具 | 注意事项 |
|------|------|----------|
| PDF | PyPDF2, pdfplumber, Unstructured | 表格和图片需要特殊处理，扫描件需 OCR |
| HTML | BeautifulSoup, Unstructured | 需要去除导航、广告等噪音内容 |
| Markdown | 直接解析 | 保留结构化信息（标题层级）有助于分块 |
| Word | python-docx | 注意样式、嵌入图片的处理 |
| 代码文件 | AST 解析 | 按函数/类/模块进行语义分块更有效 |

### 2.2 文档预处理

```python
# 典型的文档处理流程
def preprocess_document(raw_text):
    # 1. 清洗：去除多余空白、特殊字符
    text = re.sub(r'\s+', ' ', raw_text).strip()
    # 2. 去噪：移除页眉页脚、水印等
    text = remove_headers_footers(text)
    # 3. 格式标准化：统一编码、日期格式等
    text = normalize_format(text)
    # 4. 元数据提取：标题、作者、日期、来源
    metadata = extract_metadata(raw_text)
    return text, metadata
```

> **面试题：处理 PDF 文档时常遇到哪些问题？如何解决？**
>
> 1. **表格识别困难**：PDF 中的表格可能被解析为零散文本 → 使用 pdfplumber 或 Camelot 专门提取表格，转为结构化数据
> 2. **多栏布局错乱**：两栏/三栏 PDF 的文本顺序被打乱 → 使用 Layout-aware 解析器（如 Unstructured）
> 3. **扫描件/图片型 PDF**：无法直接提取文本 → OCR（Tesseract/PaddleOCR）+ 后纠错
> 4. **公式和图表**：数学公式被截断、图表信息丢失 → 多模态模型识别图表，LaTeX OCR 处理公式
> 5. **编码问题**：中文 PDF 乱码 → 尝试不同编码，使用 pdfminer 的字体映射功能

---

## 3. 文本分块策略

分块（Chunking）是 RAG 系统中对效果影响最大的环节之一。

### 3.1 Fixed-size Chunking（固定大小分块）

```python
def fixed_size_chunk(text, chunk_size=500, overlap=50):
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunks.append(text[i:i + chunk_size])
    return chunks
```

简单高效，但可能在语义不完整处断开。

### 3.2 Recursive Character Splitting（递归字符分块）

LangChain 的默认策略，按优先级使用不同分隔符递归分割：

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
)
chunks = splitter.split_text(document)
```

先尝试按段落分，段落太长则按句子分，以此类推，尽量保留语义完整性。

### 3.3 Semantic Chunking（语义分块）

使用 Embedding 相似度判断语义断点：

```python
# 思路：计算相邻句子的语义相似度
# 相似度骤降处即为语义边界
sentences = split_into_sentences(text)
embeddings = embed_model.encode(sentences)
similarities = [cosine_similarity(embeddings[i], embeddings[i+1]) 
                for i in range(len(embeddings)-1)]
# 在相似度低于阈值处分块
breakpoints = [i for i, sim in enumerate(similarities) if sim < threshold]
```

### 3.4 Agentic Chunking（智能体分块）

使用 LLM 来决定分块策略：

1. LLM 阅读文档，判断每段内容的主题
2. 将同主题的内容归为一个 chunk
3. 为每个 chunk 生成摘要作为索引

> **面试题：如何选择合适的分块大小（chunk size）？**
>
> 没有万能的 chunk size，需要根据场景调整：
> - **小 chunk（100-300 tokens）**：检索精度高（内容聚焦），但缺乏上下文；适合 FAQ、定义类内容
> - **大 chunk（500-1500 tokens）**：上下文完整，但检索精度可能下降；适合需要完整段落理解的场景
> - **推荐做法**：从 500-800 tokens 开始，通过评估调整；使用 overlap（通常 10-20%）防止信息断裂
> - **Parent-Child 策略**：检索用小 chunk 提高精度，生成时将相邻 chunk 或 parent chunk 一并送入 LLM 保证完整性
> - **最终依据**：在你的评估数据集上做实验，分别测试不同 chunk size 的检索召回率和最终回答质量

---

## 4. Embedding 模型

### 4.1 主流 Embedding 模型

| 模型 | 维度 | 特点 |
|------|------|------|
| OpenAI text-embedding-3-small | 1536 | 性价比高，支持维度缩减 |
| OpenAI text-embedding-3-large | 3072 | 精度最高的商用模型 |
| BGE (BAAI) | 768/1024 | 开源最佳中文 Embedding 之一 |
| E5 (Microsoft) | 768/1024 | 指令式 Embedding，效果优秀 |
| GTE (Alibaba) | 768 | 多语言支持好，中文表现优秀 |
| Cohere Embed v3 | 1024 | 支持多语言，有压缩功能 |
| Jina Embeddings v3 | 1024 | 支持超长文本（8K tokens） |

### 4.2 Embedding 使用要点

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('BAAI/bge-large-zh-v1.5')

# 查询和文档使用不同的前缀（某些模型需要）
query_embedding = model.encode("query: 什么是RAG？")
doc_embedding = model.encode("passage: RAG是检索增强生成的缩写...")

# 计算相似度
similarity = cosine_similarity([query_embedding], [doc_embedding])[0][0]
```

> **面试题：如何选择 Embedding 模型？商用 vs 开源如何决策？**
>
> **选择标准**：
> 1. **语言覆盖**：中文场景优先考虑 BGE/GTE，英文场景 OpenAI/E5 都很好
> 2. **MTEB 排行榜**：参考 HuggingFace MTEB 基准测试排名
> 3. **维度与性能平衡**：高维度（1024/3072）精度更高但存储和计算成本更大
> 4. **上下文长度**：大部分模型限制 512 tokens，超长文本需要选择支持 8K+ 的模型
> 5. **成本考量**：OpenAI Embedding 按 token 收费，开源模型可自部署
> 6. **数据隐私**：敏感数据不宜发送到外部 API → 部署开源模型
> 7. **微调需求**：如需在特定领域微调，开源模型更灵活

---

## 5. 向量数据库

### 5.1 主流向量数据库对比

| 数据库 | 类型 | 特点 | 适用场景 |
|--------|------|------|----------|
| Pinecone | 云托管 | 全托管，简单易用 | 快速上线，不想运维 |
| Weaviate | 开源/云 | 支持混合搜索，GraphQL API | 需要混合检索 |
| Milvus | 开源 | 高性能，支持十亿级向量 | 大规模生产环境 |
| Chroma | 开源 | 轻量级，开发友好 | 原型开发，小规模应用 |
| Qdrant | 开源/云 | Rust 实现，过滤性能优秀 | 需要复杂过滤条件 |
| FAISS | 库 | Meta 开发，纯索引库 | 需要嵌入自有系统 |
| pgvector | 扩展 | PostgreSQL 扩展 | 已有 PG 生态，数据量不大 |

### 5.2 基本使用示例

```python
# Chroma 示例
import chromadb

client = chromadb.Client()
collection = client.create_collection("my_docs")

# 添加文档
collection.add(
    documents=["RAG是检索增强生成", "LLM是大语言模型"],
    metadatas=[{"source": "wiki"}, {"source": "paper"}],
    ids=["doc1", "doc2"]
)

# 查询
results = collection.query(
    query_texts=["什么是RAG？"],
    n_results=3,
    where={"source": "wiki"}  # 元数据过滤
)
```

> **面试题：如何在生产环境中选择向量数据库？**
>
> 考虑因素：
> 1. **数据规模**：<100 万向量，Chroma/pgvector 足够；百万到十亿级用 Milvus/Qdrant；更大规模考虑 Pinecone
> 2. **查询模式**：需要复杂元数据过滤 → Qdrant（过滤性能优秀）；需要全文检索 → Weaviate
> 3. **运维能力**：无专门运维 → 云托管（Pinecone）；有运维团队 → 自部署开源方案
> 4. **延迟要求**：P99 < 50ms → 需要内存级方案或 SSD 优化的数据库
> 5. **一致性需求**：金融等场景需要强一致性 → 考虑有事务支持的方案
> 6. **已有技术栈**：已用 PostgreSQL → pgvector 最低侵入；纯 Python → Chroma 最简单

---

## 6. 向量检索算法

### 6.1 精确搜索（Brute Force / Flat）

遍历所有向量计算相似度，保证找到最精确的结果。时间复杂度 O(n·d)，适合小数据集。

### 6.2 HNSW（Hierarchical Navigable Small World）

构建多层图结构，上层图用于快速定位近似区域，下层图用于精细搜索。

- **优点**：查询速度快（O(log n)），召回率高（通常 >95%）
- **缺点**：内存占用大（需要存储图结构），构建索引慢
- **适用**：中等规模数据集（百万级），对查询延迟要求高

### 6.3 IVF（Inverted File Index）

将向量空间用 K-means 聚类分成多个 Voronoi 区域，查询时只搜索最近的几个区域。

- **nlist**：聚类中心数量
- **nprobe**：查询时搜索的区域数量（nprobe 越大召回率越高，但速度越慢）

### 6.4 PQ（Product Quantization，乘积量化）

将高维向量分成多个子向量，每个子向量用量化码本编码。大幅减少存储空间（如 128 维 float32 可压缩为 16 字节）。

常见组合：**IVF-PQ**（IVF 粗排 + PQ 精排），兼顾速度和空间。

> **面试题：HNSW 和 IVF 各有什么优缺点？如何选择？**
>
> **HNSW**：查询快、召回率高，但内存占用约为原始向量的 1.5-2 倍，构建索引较慢，不支持动态删除（需要标记删除+重建）。
> **IVF**：构建快、支持增量更新，配合 PQ 可大幅压缩内存，但需要调参（nlist/nprobe），且对数据分布的均匀性有要求。
> **选择建议**：数据量 <1000 万且内存充足 → HNSW；数据量 >1000 万或内存受限 → IVF-PQ；实时性要求极高 → HNSW；需要频繁更新数据 → IVF。

---

## 7. 混合检索

### 7.1 Dense + Sparse 检索

```python
# 混合检索示例
def hybrid_search(query, alpha=0.7):
    # Dense 检索（向量相似度）
    dense_results = vector_db.search(
        query_embedding=embed(query), top_k=20
    )
    # Sparse 检索（BM25 关键词匹配）
    sparse_results = bm25_index.search(query, top_k=20)
    
    # Reciprocal Rank Fusion (RRF) 融合
    fused = reciprocal_rank_fusion(
        [dense_results, sparse_results],
        weights=[alpha, 1 - alpha]
    )
    return fused[:10]

def reciprocal_rank_fusion(result_lists, weights, k=60):
    scores = {}
    for results, weight in zip(result_lists, weights):
        for rank, doc in enumerate(results):
            doc_id = doc.id
            scores[doc_id] = scores.get(doc_id, 0) + weight / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

### 7.2 为什么需要混合检索

- **向量检索（Dense）**：擅长语义匹配，能找到意思相近但用词不同的内容
- **关键词检索（Sparse / BM25）**：擅长精确匹配，对专有名词、编号、代码等有优势

> **面试题：举例说明什么场景下纯向量检索不如 BM25？**
>
> 1. **精确术语查询**：用户搜索「RFC 7231」或产品编号「SKU-A10032」，向量检索可能将其与语义相近但不同的编号混淆，BM25 通过精确匹配能直接命中。
> 2. **缩写和代码**：搜索「CORS 错误」，向量检索可能返回一般性的跨域内容，BM25 能精确匹配包含 "CORS" 的文档。
> 3. **低频专业术语**：Embedding 模型对罕见术语的表示不够好，BM25 的 IDF 权重反而对低频词给予更高权重。
> 4. **最佳实践**是使用混合检索，用 RRF 或 Weighted Sum 融合两种结果，取长补短。

---

## 8. 重排序（Reranking）

重排序是在初步检索后，使用更精细的模型对候选结果进行二次排序。

### 8.1 Cross-Encoder Reranker

与 Bi-Encoder（分别编码 query 和 document 再计算相似度）不同，Cross-Encoder 将 query 和 document 拼接在一起输入模型，能够进行更深层的交互匹配：

```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder('BAAI/bge-reranker-v2-m3')

query = "什么是RAG？"
documents = ["RAG是检索增强生成...", "RPC是远程过程调用...", "RAG通过检索外部知识..."]

# Cross-Encoder 对每个 (query, doc) 对打分
pairs = [[query, doc] for doc in documents]
scores = reranker.predict(pairs)

# 按分数排序
ranked = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
```

### 8.2 常用 Reranker

- **BGE Reranker**：BAAI 开源，中英文效果好
- **Cohere Rerank**：商用 API，多语言支持好
- **ColBERT**：Late Interaction 模型，兼顾效率和精度
- **LLM Reranker**：直接用 LLM 判断相关性，成本高但效果最好

> **面试题：为什么需要 Reranking？它在 RAG pipeline 中的价值是什么？**
>
> **需要 Reranking 的原因**：Bi-Encoder（Embedding）检索虽然速度快，但查询和文档分别编码，交互不充分，精排能力有限。Reranker 将查询和文档一起输入模型，可以捕捉更细粒度的语义匹配。
>
> **价值体现**：(1) 典型情况下，Reranking 可将 Top-10 的 NDCG 提升 5-15%；(2) 允许初始检索召回更多候选（Top-50），再由 Reranker 精选 Top-5，提高整体召回率；(3) Reranker 可以过滤掉与查询表面相似但实际不相关的结果。
>
> **Pipeline 通常为**：向量检索 Top-50 → Reranker 精排 → Top-5 送入 LLM。

---

## 9. 查询优化

### 9.1 Query Rewriting（查询重写）

使用 LLM 将用户的口语化查询改写为更适合检索的形式：

```python
rewrite_prompt = """请将以下用户问题改写为更适合搜索引擎检索的查询：

用户问题：{query}
改写后的查询："""

# 原始："那个什么RAG的东西是咋工作的啊"
# 改写后："RAG检索增强生成工作原理"
```

### 9.2 HyDE（Hypothetical Document Embeddings）

先让 LLM 生成一个"假设性回答"，然后用这个回答去检索：

```python
def hyde_search(query):
    # 1. LLM 生成假设性回答
    hypothetical_answer = llm.generate(
        f"请回答以下问题（不需要准确，只需要大致合理）：\n{query}"
    )
    # 2. 用假设性回答的 Embedding 去检索
    results = vector_db.search(embed(hypothetical_answer), top_k=10)
    return results
```

HyDE 的原理是：假设性回答与真实文档在向量空间中更接近（因为它们都是 "回答" 的形式），从而提高检索效果。

### 9.3 Multi-Query（多查询）

将原始问题扩展为多个不同角度的子查询，分别检索后合并结果：

```python
def multi_query_search(query):
    # LLM 生成多个角度的查询
    sub_queries = llm.generate(f"""
    请从3个不同角度重新表述以下问题：
    原始问题：{query}
    """)
    
    all_results = []
    for sub_q in sub_queries:
        results = vector_db.search(embed(sub_q), top_k=5)
        all_results.extend(results)
    
    return deduplicate(all_results)
```

### 9.4 Sub-question Decomposition（子问题分解）

将复杂问题拆分为多个简单子问题，分别检索和回答：

```python
# 原始问题："比较 Python 和 Java 在机器学习领域的优缺点"
# 拆分为：
# 1. "Python 在机器学习领域的优点"
# 2. "Python 在机器学习领域的缺点"
# 3. "Java 在机器学习领域的优点"
# 4. "Java 在机器学习领域的缺点"
```

> **面试题：这些查询优化方法各适用于什么场景？**
>
> - **Query Rewriting**：用户查询口语化、含有拼写错误或过于简短时
> - **HyDE**：查询和目标文档的形式差异大时（如问题 vs 段落）
> - **Multi-Query**：查询含义模糊，可能有多种理解角度时
> - **Sub-question**：复杂问题包含多个子话题，单次检索无法完全覆盖时
> - **Step-back Prompting**：查询过于具体，需要先回答更一般性的问题时
> - 实际生产中常**组合使用**，如 Query Rewriting + Multi-Query + Reranking

---

## 10. Advanced RAG 技术

### 10.1 Self-RAG

模型在生成过程中自主决定是否需要检索、检索结果是否相关、生成内容是否被支持：

1. **检索判断**：模型判断当前是否需要检索（Retrieve token）
2. **相关性判断**：评估检索结果与问题的相关性（ISREL token）
3. **支持性判断**：评估生成内容是否被检索结果支持（ISSUP token）
4. **有用性判断**：评估最终回答的有用程度（ISUSE token）

### 10.2 Corrective RAG（CRAG）

对检索结果进行评估和纠正：

```
1. 检索文档
2. 使用 Knowledge Refinement 模块评估文档质量
   - 如果所有文档都不相关 → 触发 Web 搜索补充
   - 如果部分相关 → 过滤掉不相关文档
   - 如果都相关 → 直接使用
3. 基于精炼后的文档生成回答
```

### 10.3 Adaptive RAG

根据查询的复杂度动态选择策略：
- 简单事实类问题 → 直接检索回答
- 中等复杂度 → 标准 RAG 流程
- 复杂推理 → 多步检索 + CoT 推理

### 10.4 Graph RAG

将文档知识组织为知识图谱，利用图结构进行检索：

1. **实体抽取**：从文档中抽取实体和关系
2. **图构建**：构建知识图谱
3. **社区检测**：对图进行社区检测，生成不同层级的摘要
4. **图检索**：结合图遍历和向量检索

Graph RAG 特别适合多跳推理和需要理解实体关系的场景。

> **面试题：Self-RAG 和标准 RAG 的核心区别是什么？**
>
> 标准 RAG **总是**检索——不管问题是否需要外部知识。Self-RAG 通过特殊 token 让模型**自主判断**何时检索、检索结果是否可用。这带来两个优势：(1) 对于模型已知的简单问题，跳过检索减少延迟；(2) 对检索结果进行质量把关，不相关的结果不会被使用，减少噪音干扰和幻觉。代价是需要在训练阶段引入 Critic 模型的标注数据来训练这些判断能力。

---

## 11. RAG 评估

### 11.1 评估维度

| 维度 | 含义 | 对应问题 |
|------|------|----------|
| Faithfulness（忠实度） | 回答是否基于检索到的文档 | 是否产生幻觉？ |
| Answer Relevancy（答案相关性） | 回答是否与问题相关 | 是否答非所问？ |
| Context Relevancy（上下文相关性） | 检索到的文档是否与问题相关 | 检索是否准确？ |
| Context Recall（上下文召回率） | 回答所需信息是否被检索到 | 是否遗漏关键信息？ |

### 11.2 RAGAS 框架

```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall

dataset = {
    "question": ["什么是RAG？"],
    "answer": ["RAG是检索增强生成，通过..."],
    "contexts": [["RAG全称Retrieval-Augmented Generation..."]],
    "ground_truth": ["RAG是一种结合检索和生成的技术..."]
}

result = evaluate(
    dataset,
    metrics=[faithfulness, answer_relevancy, context_precision, context_recall]
)
print(result)
```

> **面试题：如何构建 RAG 系统的评估体系？**
>
> 1. **离线评估**：构建包含（问题, 标准答案, 相关文档）三元组的评估集，使用 RAGAS 或自定义指标自动评估
> 2. **检索评估**：Recall@K、MRR（Mean Reciprocal Rank）、NDCG 评估检索模块
> 3. **生成评估**：Faithfulness（是否基于检索文档）、Correctness（答案是否正确）
> 4. **端到端评估**：在完整 pipeline 上评估最终回答质量
> 5. **LLM-as-Judge**：使用 GPT-4 对回答进行多维度打分
> 6. **用户反馈**：收集真实用户的满意度评分和反馈
> 7. **错误分析**：定期抽样分析失败案例，分类归因（检索失败 / 生成幻觉 / 格式错误 等）

---

## 12. RAG vs Fine-tuning

| 维度 | RAG | Fine-tuning |
|------|-----|-------------|
| 知识更新 | 实时更新，修改文档即可 | 需要重新训练 |
| 可解释性 | 高，可追溯到源文档 | 低，知识内化在参数中 |
| 成本 | 推理成本稍高（多检索步骤） | 训练成本高，推理成本不变 |
| 适用场景 | 知识频繁变化、需要引用源 | 风格/格式调整、领域术语 |
| 幻觉控制 | 较好（基于检索文档） | 较差（可能编造） |
| 数据需求 | 只需文档，无需标注 | 需要高质量标注数据 |

> **面试题：什么场景下应该用 RAG，什么场景下应该 Fine-tuning？能否结合使用？**
>
> **用 RAG**：知识库频繁更新；需要引用来源；数据敏感不能用于训练；快速上线。
> **用 Fine-tuning**：需要特定输出格式/风格；领域专业术语理解；需要极致的推理速度。
> **结合使用**：先用领域数据 Fine-tune 模型提升领域理解能力，再用 RAG 注入最新知识。这是企业级应用中最常见的方案。例如，Fine-tune 使模型理解金融术语和分析框架，RAG 提供最新的市场数据和研报。

---

## 13. RAG 系统常见问题与优化

### 常见问题及解决方案

1. **检索不到相关文档**：优化分块策略、添加 Query Rewriting、使用混合检索
2. **检索到但不相关**：添加 Reranking、优化 Embedding 模型、使用元数据过滤
3. **回答产生幻觉**：增强 Faithfulness 约束、要求引用、使用 Self-RAG
4. **回答不完整**：增加 Top-K、使用 Multi-Query、优化分块避免信息碎片化
5. **延迟过高**：缓存热门查询、使用更快的 ANN 算法、减少 Reranker 的候选数

---

## 14. 生产环境 RAG 最佳实践

1. **数据质量优先**：投入 80% 的时间在文档质量和分块策略上
2. **混合检索 + Reranking**：这是目前效果最稳定的检索方案
3. **元数据管理**：为每个 chunk 附加来源、时间、类别等元数据，支持过滤
4. **增量更新**：设计文档变更检测和增量索引更新机制
5. **监控与可观测性**：记录每个环节的中间结果（检索结果、重排结果、最终回答）
6. **缓存策略**：对热门查询缓存检索结果和最终答案
7. **降级策略**：检索失败时回退到纯 LLM 回答，并标注 "未找到相关文档"
8. **用户反馈闭环**：收集用户反馈持续优化检索和生成质量

---

## 总结

RAG 是构建知识密集型 AI 应用的核心技术栈。面试中，候选人需要展示对全链路的深入理解——从文档处理、分块策略、Embedding 选型、向量数据库、检索算法、重排序，到高级 RAG 技术和评估方法。关键是不仅知道 "what"，更要理解 "why"（为什么这样设计）和 "how"（在具体场景中如何选择和优化）。
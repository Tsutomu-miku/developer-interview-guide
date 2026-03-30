# 大语言模型基础面试指南

本章系统梳理大语言模型（Large Language Model, LLM）的核心基础知识，涵盖 Transformer 架构、预训练与微调、主流模型演进、Tokenizer 原理、推理参数、上下文窗口、模型量化与部署、多模态模型及评估方法，是 AI Agent 开发面试中最重要的底层知识体系。

---

## 1. Transformer 架构详解

Transformer 是当今几乎所有大语言模型的基石架构，由 Vaswani 等人在 2017 年论文《Attention Is All You Need》中提出，彻底替代了 RNN/LSTM 在序列建模上的主导地位。

### 1.1 Self-Attention（自注意力）

Self-Attention 的核心思想是：对于输入序列中的每个 token，计算它与序列中所有其他 token 的关联权重，从而获得全局上下文信息。

计算公式：

```
Attention(Q, K, V) = softmax(Q·K^T / √d_k) · V
```

其中：
- **Q（Query）**：查询矩阵，代表当前 token "想要查找什么"
- **K（Key）**：键矩阵，代表每个 token "包含什么信息"
- **V（Value）**：值矩阵，代表每个 token "实际输出的信息"
- **d_k**：Key 向量的维度，用于缩放，防止点积过大导致 softmax 梯度消失

> **面试题：为什么 Self-Attention 要除以 √d_k？**
>
> 当 d_k 较大时，Q 和 K 的点积结果的方差也会随之增大（方差约为 d_k），导致 softmax 的输入值过大，使得梯度集中在极小的区域（softmax 饱和），反向传播时梯度接近于零。除以 √d_k 将方差重新归一化为 1，使 softmax 的梯度分布更合理，训练更稳定。

> **面试题：Self-Attention 的时间复杂度是多少？为什么这是长文本处理的瓶颈？**
>
> Self-Attention 的时间和空间复杂度均为 O(n²·d)，其中 n 为序列长度，d 为隐藏维度。当序列长度从 4K 扩展到 128K 时，计算量增长 1024 倍。这就是为什么长文本处理需要诸如 Sliding Window Attention、Flash Attention、Ring Attention 等优化技术。

### 1.2 Multi-Head Attention（多头注意力）

多头注意力将输入分别投影到 h 个不同的子空间中，并行计算 h 组注意力，最后将结果拼接并通过线性变换输出：

```
MultiHead(Q, K, V) = Concat(head_1, ..., head_h) · W^O
head_i = Attention(Q·W_i^Q, K·W_i^K, V·W_i^V)
```

> **面试题：Multi-Head Attention 为什么比 Single-Head Attention 效果好？**
>
> 不同的注意力头可以学习到不同类型的关注模式。例如，某些头关注语法依赖关系（主谓一致），某些头关注语义关系（指代消解），某些头关注位置邻近关系。这种多样化的注意力模式使模型能够在同一层中捕获多种层次的特征，显著提升表达能力。实践中，通常设置 h=8 到 h=128 不等，每个头的维度为 d_model / h。

### 1.3 Position Encoding（位置编码）

Transformer 的注意力机制是排列不变的（Permutation Invariant），即不考虑 token 的顺序。因此需要额外引入位置信息。

**绝对位置编码（Sinusoidal）**：原始 Transformer 使用正弦余弦函数生成位置编码，不需要学习参数：

```
PE(pos, 2i)   = sin(pos / 10000^(2i/d_model))
PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))
```

**可学习位置编码**：GPT 系列使用可学习的绝对位置 Embedding，将每个位置映射为一个可训练向量。

**旋转位置编码（RoPE）**：LLaMA、Qwen 等模型采用 RoPE，通过旋转矩阵将位置信息注入到 Q 和 K 中，具有更好的外推性和相对位置建模能力。其核心思想是：将 Q 和 K 按维度对分组，在每对维度上施加一个与位置相关的旋转角度。

**ALiBi（Attention with Linear Biases）**：不添加位置编码，而是在注意力分数上添加与距离成线性关系的偏置项，具有良好的长度外推能力。

> **面试题：RoPE 相比传统位置编码有什么优势？**
>
> 1. **相对位置建模**：RoPE 天然编码了相对位置信息——两个 token 的注意力分数只依赖于它们的相对距离，而非绝对位置。
> 2. **长度外推**：结合 NTK-aware 缩放或 YaRN 等方法，RoPE 可以较好地外推到训练时未见过的更长序列。
> 3. **效率**：不需要额外的可学习参数，计算开销小。
> 4. **理论优雅**：基于复数旋转的数学框架清晰，便于分析。

### 1.4 FFN（前馈神经网络）

每个 Transformer 层中的 FFN 通常是一个两层全连接网络，带有非线性激活：

```
FFN(x) = W_2 · activation(W_1 · x + b_1) + b_2
```

现代模型（如 LLaMA）常使用 **SwiGLU** 激活函数替代 ReLU/GELU：

```
SwiGLU(x) = (x · W_1) ⊙ SiLU(x · W_3)
```

FFN 的隐藏维度通常是模型维度的 4 倍（或使用 SwiGLU 时为 8/3 倍）。FFN 被认为是模型存储事实性知识的主要模块。

### 1.5 Layer Normalization

Layer Norm 对同一个样本的所有特征维度进行归一化，稳定训练过程。

**Post-Norm**：原始 Transformer 在残差连接之后做 LayerNorm（`LayerNorm(x + Sublayer(x))`）。
**Pre-Norm**：现代模型更常用 Pre-Norm（`x + Sublayer(LayerNorm(x))`），训练更稳定。

**RMSNorm**：LLaMA 系列使用 RMSNorm（Root Mean Square Normalization），去除了均值中心化步骤，只做缩放，计算更高效：

```
RMSNorm(x) = x / RMS(x) · γ，其中 RMS(x) = √(mean(x²))
```

> **面试题：Pre-Norm 和 Post-Norm 有什么区别？为什么现代模型倾向用 Pre-Norm？**
>
> Post-Norm 在深层网络中容易出现梯度消失或训练不稳定问题，需要仔细的学习率 warmup。Pre-Norm 将归一化放在子层之前，使得残差路径上的梯度更加稳定，即使在非常深的网络（100+ 层）中也能顺利训练。代价是 Pre-Norm 在相同模型规模下的最终性能可能略低于精心调优的 Post-Norm，但训练的鲁棒性显著提升。

---

## 2. 预训练与微调

### 2.1 Pre-training（预训练）

预训练是在大规模无标注文本上，通过自监督学习任务训练模型的基础能力。

**Causal Language Modeling（自回归，GPT 系列）**：预测下一个 token，使用因果注意力掩码（只看左边）。

```
目标函数：L = -∑ log P(x_t | x_1, ..., x_{t-1})
```

**Masked Language Modeling（掩码，BERT 系列）**：随机遮盖 15% 的 token，预测被遮盖的 token。

**Seq2Seq（T5/BART）**：编码器-解码器架构，适合翻译、摘要等任务。

> **面试题：为什么 GPT 用自回归预训练而 BERT 用掩码预训练？各有什么优缺点？**
>
> 自回归（GPT）天然适合文本生成任务——模型从左到右逐 token 生成，与推理时的使用方式一致。但它只能利用左侧上下文。掩码（BERT）可以利用双向上下文理解语义，在分类、NER 等理解任务上效果更好，但不擅长开放式生成。当前大模型主流采用自回归方式，因为生成能力的通用性更强，且 Scaling Law 在自回归模型上表现最优。

### 2.2 SFT（Supervised Fine-Tuning，监督微调）

在预训练模型基础上，使用人工标注的（指令, 回答）数据对进行有监督微调，使模型学会遵循指令。

关键要素：
- **数据质量远比数量重要**：LIMA 论文证明 1000 条高质量数据就能获得优秀效果
- **数据格式**：通常采用 instruction-input-output 三元组
- **LoRA/QLoRA**：高效微调方法，只训练小部分参数

### 2.3 RLHF（Reinforcement Learning from Human Feedback）

RLHF 是 ChatGPT 成功的关键技术之一，通过人类偏好数据训练奖励模型，再用强化学习（PPO）优化语言模型。

流程：
1. **收集偏好数据**：人类标注者对模型的多个回答进行排序
2. **训练奖励模型（Reward Model）**：学习人类偏好打分
3. **PPO 优化**：使用奖励模型的分数作为奖励信号，通过 PPO 算法优化语言模型，同时加入 KL 散度约束防止模型偏离太远

> **面试题：RLHF 的主要挑战和局限是什么？**
>
> 1. **奖励模型不完美**：奖励模型可能被 "hack"——模型学会生成奖励模型给高分但实际质量不高的输出（Reward Hacking）。
> 2. **训练不稳定**：PPO 算法超参数敏感，训练过程容易崩溃。
> 3. **标注成本高**：需要大量人类偏好标注数据。
> 4. **人类偏好的主观性**：不同标注者对同一回答的评价可能大相径庭。
> 5. **多目标权衡**：安全性、有用性、真实性之间常存在冲突。

### 2.4 DPO（Direct Preference Optimization）

DPO 是 RLHF 的简化替代方案，直接从偏好数据中优化模型，无需训练奖励模型和使用 PPO。

```
L_DPO = -E[log σ(β · (log π_θ(y_w|x)/π_ref(y_w|x) - log π_θ(y_l|x)/π_ref(y_l|x)))]
```

其中 y_w 是偏好回答，y_l 是非偏好回答，π_ref 是参考策略。

DPO 的优势是训练更稳定、实现更简单、计算更高效。其变体包括 IPO、KTO、ORPO 等。

---

## 3. GPT 系列模型演进

| 模型 | 时间 | 参数量 | 核心创新 |
|------|------|--------|----------|
| GPT-1 | 2018.06 | 1.17 亿 | 预训练+微调范式，12 层 Transformer Decoder |
| GPT-2 | 2019.02 | 15 亿 | Zero-shot 能力，证明 Scaling 的重要性 |
| GPT-3 | 2020.05 | 1750 亿 | In-context Learning，Few-shot 涌现 |
| GPT-3.5 | 2022.03 | ~1750 亿 | InstructGPT，RLHF 对齐 |
| GPT-4 | 2023.03 | 未公开（传闻 MoE） | 多模态，推理能力飞跃 |
| GPT-4o | 2024.05 | 未公开 | 原生多模态（文本/音频/视觉融合） |

> **面试题：什么是 In-context Learning？为什么 GPT-3 级别的模型才展现出这种能力？**
>
> In-context Learning 是指模型无需更新参数，仅通过在 Prompt 中给出少量示例就能学会新任务。GPT-3 展现这一能力的原因包括：(1) 规模效应——1750 亿参数使模型有足够容量存储 "元学习" 能力；(2) 训练数据多样性——大规模语料中隐含了大量"格式模式"；(3) 涌现现象——某些能力在模型规模超过临界点后突然出现。研究表明，In-context Learning 的内在机制可能类似于隐式的梯度下降。

---

## 4. LLaMA/Mistral/Qwen 等开源模型

### LLaMA 系列

- **LLaMA-1**（2023.02）：7B/13B/33B/65B，使用 RoPE + SwiGLU + RMSNorm + Pre-Norm
- **LLaMA-2**（2023.07）：增加到 70B，加入 GQA（Grouped Query Attention），40K context
- **LLaMA-3**（2024.04）：8B/70B，128K 词表，使用 tiktoken tokenizer
- **LLaMA-3.1**（2024.07）：支持 128K context，405B 旗舰模型

### Mistral 系列

- **Mistral-7B**：Sliding Window Attention + GQA，7B 参数超越 LLaMA-2-13B
- **Mixtral-8x7B**：MoE 架构，8 个专家中每次激活 2 个，总参数 46.7B，激活参数 12.9B

### Qwen 系列

- 阿里云开发，支持中英双语
- Qwen-2.5 系列提供 0.5B 到 72B 多个规格
- 在中文任务上表现优异

> **面试题：GQA（Grouped Query Attention）相比 MHA 和 MQA 有什么优势？**
>
> **MHA**（Multi-Head Attention）：每个头有独立的 Q/K/V，参数量和 KV Cache 都较大。**MQA**（Multi-Query Attention）：所有头共享同一组 K/V，显著减少 KV Cache 但可能损失精度。**GQA** 是两者的折中——将 Q 头分成若干组，每组共享一组 K/V。例如 32 个 Q 头分 8 组，使用 8 组 K/V。GQA 在几乎不损失精度的情况下，将 KV Cache 减小为 MHA 的 1/4（8/32），推理速度显著提升。

---

## 5. Tokenizer 原理

Tokenizer 负责将原始文本切分为模型可处理的 token 序列。

### BPE（Byte Pair Encoding）

1. 初始化：将文本拆分为字符级别的 token
2. 统计相邻 token 对的频率
3. 合并频率最高的 token 对，创建新 token
4. 重复步骤 2-3 直到达到目标词表大小

GPT 系列使用 BPE（基于 byte-level 的变体 BBPE）。

### WordPiece

与 BPE 类似，但选择合并的依据不是频率最高，而是使语言模型似然度提升最大的 token 对。BERT 使用 WordPiece。

### SentencePiece

一个独立的分词工具库，支持 BPE 和 Unigram 算法。特点是直接在原始文本（包括空格）上训练，不依赖预分词，适合多语言场景。LLaMA 使用 SentencePiece。

> **面试题：Tokenizer 的设计会如何影响模型性能？**
>
> 1. **词表大小**：词表越大，每个文本对应的 token 数越少（压缩率越高），但 Embedding 层参数量增大。LLaMA-1 词表 32K，LLaMA-3 扩大到 128K。
> 2. **多语言覆盖**：如果 tokenizer 训练数据中某语言占比低，该语言的文本会被拆分为更多 token，导致效率低下和性能下降。
> 3. **特殊 token**：`<bos>`、`<eos>`、`<pad>`、`<unk>` 等特殊 token 的处理影响模型行为。
> 4. **数字和代码**：数字按位拆分还是整体编码、代码缩进的处理方式都会影响相关任务的性能。

---

## 6. 推理参数

### Temperature（温度）

控制输出概率分布的 "锐利度"。将 logits 除以 temperature 后再做 softmax：

```
P(x_i) = exp(z_i / T) / Σ exp(z_j / T)
```

- T=0（贪心解码）：始终选择概率最高的 token，输出确定性最高
- T=0.1~0.5：低创造性，适合事实性问答
- T=0.7~1.0：中等创造性，适合一般对话
- T>1.0：高创造性但可能不连贯，适合创意写作

### Top-p（Nucleus Sampling）

从概率从高到低排序的 token 中，选择累积概率刚好超过 p 的最小集合，然后在这个集合中采样。例如 Top-p=0.9 表示只从概率总和达到 90% 的 token 中采样。

### Top-k

只从概率最高的 k 个 token 中采样。Top-k=1 等价于贪心解码。

### Frequency Penalty 与 Presence Penalty

- **Frequency Penalty**：根据 token 在已生成文本中出现的**次数**减少其 logit，出现越多惩罚越大
- **Presence Penalty**：只要 token 在已生成文本中**出现过**就减少其 logit，不论次数

两者都用于减少重复。Frequency Penalty 对高频 token 惩罚更强，Presence Penalty 更均匀地鼓励多样性。

> **面试题：在生产环境中，你会如何设置推理参数？**
>
> 取决于应用场景：
> - **客服/问答**：Temperature=0，确保回答准确一致
> - **代码生成**：Temperature=0~0.2，Top-p=0.95
> - **创意写作**：Temperature=0.7~1.0，Top-p=0.9
> - **数据抽取/JSON输出**：Temperature=0，确保格式一致
> - 一般不同时使用 Top-p 和 Top-k，选择其一即可
> - Frequency Penalty 设为 0.3~0.5 可有效减少重复

---

## 7. 上下文窗口与长文本处理

上下文窗口（Context Window）是模型能处理的最大 token 数量。

| 模型 | 上下文窗口 |
|------|----------|
| GPT-3 | 4K |
| GPT-4 | 8K / 32K |
| GPT-4 Turbo | 128K |
| Claude 3.5 | 200K |
| LLaMA-3.1 | 128K |
| Gemini 1.5 Pro | 1M / 2M |

### 长文本处理技术

1. **位置编码外推**：NTK-aware Scaling、YaRN、Dynamic NTK 等方法扩展 RoPE 的有效长度
2. **Flash Attention**：通过分块计算和利用 GPU SRAM，将注意力的内存复杂度从 O(n²) 降低到 O(n)，同时加速计算
3. **Sliding Window Attention**：只关注局部窗口内的 token，降低计算量
4. **Ring Attention**：分布式长序列注意力计算
5. **文本分块 + 检索**：将长文本分块存储，使用 RAG 检索相关片段

> **面试题：如果输入文本超过了模型的上下文窗口怎么办？**
>
> 几种策略：(1) **截断**：保留最新的或最重要的内容，简单但丢失信息。(2) **分块摘要**：对长文本分段摘要后再处理，适合摘要类任务。(3) **RAG**：将文本分块建索引，查询时只检索相关片段。(4) **Map-Reduce**：对每个分块并行处理后合并结果。(5) **滑动窗口**：重叠分块逐步处理。(6) **更换更大上下文窗口的模型**。实际生产中最常用的是 RAG 方式。

---

## 8. 模型量化

量化是将模型权重从高精度（FP32/FP16）压缩到低精度（INT8/INT4）的技术，显著减少显存占用和加速推理。

### 量化类型

- **INT8 量化**：权重用 8 位整数表示，显存减半，精度损失小
- **INT4 量化**：权重用 4 位整数表示，显存减为 1/4，有一定精度损失
- **FP8 量化**：使用 8 位浮点数，兼顾精度和效率

### 量化方法

| 方法 | 特点 |
|------|------|
| GPTQ | 基于 OBS（Optimal Brain Surgeon），逐层量化，需要校准数据 |
| AWQ | Activation-aware Weight Quantization，保护重要权重通道 |
| GGUF | GGML 的改进格式，支持 CPU 推理，多种量化级别（Q4_K_M 等） |
| bitsandbytes | HuggingFace 集成，支持 NF4（Normal Float 4-bit） |

> **面试题：量化后的模型精度损失如何评估和控制？**
>
> 1. **评估方法**：在基准测试上比较量化前后的 Perplexity 变化、下游任务精度等。通常 INT8 量化精度损失 <1%，INT4 损失在 1-5%。
> 2. **控制方法**：(a) AWQ 通过分析激活分布保护重要权重；(b) GPTQ 使用校准数据集最小化量化误差；(c) 混合精度——对敏感层（如注意力层）保持更高精度；(d) QLoRA 的 NF4 + Double Quantization 方案能在 4-bit 下保持较好精度。

---

## 9. 模型部署

### vLLM

- 开源高性能推理引擎
- **PagedAttention**：借鉴操作系统虚拟内存的分页机制管理 KV Cache，显著提高 GPU 显存利用率
- 支持连续批处理（Continuous Batching），吞吐量比 HuggingFace 原生推理高 24 倍以上
- 支持 Tensor Parallelism 多卡部署

### TGI（Text Generation Inference）

- HuggingFace 官方推理框架
- 支持 Flash Attention、量化、水印等
- 内置 Token Streaming 和 gRPC/REST API
- 适合 HuggingFace 生态

### Ollama

- 本地模型运行工具
- 类似 Docker 的模型管理体验（`ollama pull`、`ollama run`）
- 支持 GGUF 格式，CPU/GPU 推理
- 适合开发调试和个人使用

### GGML / llama.cpp

- 纯 C/C++ 实现的推理引擎
- 支持 CPU 推理，对 Apple Silicon 优化良好
- GGUF 格式是当前标准
- 资源需求低，适合边缘设备

> **面试题：如何选择模型部署方案？**
>
> - **高吞吐量生产环境**：vLLM（PagedAttention + Continuous Batching）
> - **HuggingFace 生态**：TGI，方便集成 HF 模型
> - **本地开发/个人使用**：Ollama（简单易用）
> - **边缘设备/CPU 推理**：llama.cpp / GGUF
> - **多模型切换**：考虑 vLLM 或 Triton Inference Server
> - **成本敏感**：使用量化模型（GPTQ/AWQ）+ vLLM

---

## 10. 多模态模型

多模态模型能够处理文本、图像、音频、视频等多种输入模态。

### GPT-4V / GPT-4o

- GPT-4V：支持图像+文本输入
- GPT-4o：原生多模态，文本/图像/音频统一处理，延迟极低

### LLaVA（Large Language and Vision Assistant）

- 开源视觉语言模型
- 架构：Vision Encoder（CLIP ViT）+ Projection Layer + LLM
- 两阶段训练：先预训练视觉-语言对齐，再指令微调

### Gemini

- Google 的原生多模态模型
- 从训练开始就在多模态数据上联合训练
- Gemini 1.5 Pro 支持 1M+ context

> **面试题：多模态模型如何对齐不同模态的表示？**
>
> 主要有三种方法：(1) **投影层对齐**：用简单 MLP 或 Cross-Attention 将视觉特征映射到语言模型的输入空间（LLaVA 方式）。(2) **统一 tokenization**：将图像也转换为离散 token（如 DALL-E 的 dVAE），与文本 token 一起处理。(3) **原生多模态训练**：从预训练阶段就在混合模态数据上训练（Gemini 方式），模型内部学习对齐。方法 (3) 理论上最优但训练成本最高，方法 (1) 最灵活且实现简单。

---

## 11. 模型评估

### Perplexity（困惑度）

衡量语言模型对文本的 "困惑" 程度，值越低表示模型对文本的预测能力越强：

```
PPL = exp(-1/N · Σ log P(x_i | x_{<i}))
```

### BLEU / ROUGE

- **BLEU**：衡量生成文本与参考文本的 n-gram 匹配度，常用于机器翻译
- **ROUGE**：基于召回率的文本相似度指标，常用于摘要评估（ROUGE-1/ROUGE-2/ROUGE-L）

### Human Eval

OpenAI 提出的代码生成评估基准，包含 164 个 Python 编程题，衡量 pass@k 指标。

### MMLU（Massive Multitask Language Understanding）

包含 57 个学科的多选题，涵盖 STEM、人文、社会科学等，是衡量模型知识广度的标准基准。

### 其他重要基准

- **GSM8K**：数学推理
- **HumanEval / MBPP**：代码生成
- **HellaSwag**：常识推理
- **TruthfulQA**：真实性评估
- **MT-Bench**：多轮对话能力（GPT-4 评分）
- **AlpacaEval**：指令遵循能力
- **Arena Elo**：人类偏好排名（LMSYS Chatbot Arena）

> **面试题：如何评估一个大语言模型是否适合你的业务场景？**
>
> 1. **基准测试先行**：在通用基准上了解模型的基本能力水平
> 2. **构建领域评估集**：收集业务相关的真实问题和标准答案
> 3. **多维度评估**：准确性、响应速度、成本、安全性、鲁棒性
> 4. **A/B 测试**：在真实用户流量上比较不同模型
> 5. **人工评估**：对关键场景进行人工打分
> 6. **LLM-as-Judge**：使用 GPT-4 等强模型作为自动评估器
> 7. **关注边界情况**：测试模型在对抗性输入、罕见场景下的表现
> 8. **持续监控**：部署后持续跟踪模型输出质量

---

## 总结

大语言模型的基础知识是 AI Agent 开发的根基。面试中，需要深入理解 Transformer 的每个组件、预训练到对齐的完整训练流程、推理优化和部署方案。同时要关注最新进展——模型架构不断演进，新的训练技术、量化方法和部署工具层出不穷。掌握这些基础，才能在 Agent 开发中做出正确的技术选型和优化决策。
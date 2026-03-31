# 云原生与容器化

> 优先级：⭐⭐（低优先级）| 适用于：后端开发、DevOps、SRE、云原生工程师

云原生技术栈已成为现代后端开发的核心基础设施。本章涵盖Docker容器化、Kubernetes编排、Go与K8s生态整合、服务网格、CI/CD与可观测性等关键主题。

---

## 1. Docker基础

### 1.1 容器 vs 虚拟机

| 对比维度 | 容器 | 虚拟机 |
|---------|------|--------|
| 隔离级别 | 进程级（共享宿主内核） | 硬件级（独立OS内核） |
| 启动速度 | 毫秒级 | 分钟级 |
| 资源占用 | MB级 | GB级 |
| 性能损耗 | 接近原生 | 5%-15% |
| 安全性 | 较弱（共享内核） | 较强（完全隔离） |
| 典型技术 | Docker、containerd | VMware、KVM、Hyper-V |

**核心原理：** 容器基于Linux内核的三大特性实现隔离：
- **Namespace**：隔离PID、Network、Mount、UTS、IPC、User
- **Cgroups**：限制CPU、内存、IO等资源使用量
- **UnionFS**：分层文件系统，实现镜像的高效存储和分发

### 1.2 Dockerfile最佳实践（多阶段构建）

```dockerfile
# ============ 阶段1：构建阶段 ============
FROM golang:1.22-alpine AS builder

# 设置工作目录
WORKDIR /app

# 利用Docker缓存机制，先复制依赖文件
COPY go.mod go.sum ./
RUN go mod download

# 复制源代码并编译
COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -ldflags="-w -s" -o /app/server ./cmd/server

# ============ 阶段2：运行阶段 ============
FROM alpine:3.19

# 安装必要的CA证书（HTTPS请求需要）
RUN apk --no-cache add ca-certificates tzdata

# 创建非root用户
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /app
COPY --from=builder /app/server .
COPY --from=builder /app/configs ./configs

# 使用非root用户运行
USER appuser

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s \
    CMD wget --quiet --tries=1 --spider http://localhost:8080/health || exit 1

ENTRYPOINT ["./server"]
```

**关键优化点：**
- `-ldflags="-w -s"`：去掉调试信息，减小二进制体积约30%
- `CGO_ENABLED=0`：静态编译，无需glibc依赖
- 分层COPY：先复制go.mod利用缓存，避免每次改代码都重新下载依赖

### 1.3 镜像优化策略

```dockerfile
# 方案1：Alpine（~5MB基础镜像）
FROM alpine:3.19

# 方案2：scratch（0MB，最小镜像）
FROM scratch
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /app/server /server
ENTRYPOINT ["/server"]

# 方案3：distroless（Google维护，含最小运行时）
FROM gcr.io/distroless/static-debian12
COPY --from=builder /app/server /server
ENTRYPOINT ["/server"]
```

**镜像大小对比：**
| 基础镜像 | 大小 | 适用场景 |
|---------|------|---------|
| golang:1.22 | ~800MB | 仅用于构建阶段 |
| alpine:3.19 | ~5MB | 需要shell调试 |
| distroless | ~2MB | 生产环境推荐 |
| scratch | 0MB | 极致精简，静态二进制 |

### 1.4 Docker网络模式

```bash
# bridge模式（默认）：容器通过虚拟网桥通信
docker run --network bridge myapp

# host模式：直接使用宿主机网络栈，性能最好
docker run --network host myapp

# none模式：无网络，完全隔离
docker run --network none myapp

# 自定义网络：推荐用于多容器通信
docker network create mynet
docker run --network mynet --name svc-a myapp-a
docker run --network mynet --name svc-b myapp-b
# svc-b可以通过 svc-a:8080 直接访问
```

### 1.5 Docker Compose编排

```yaml
# docker-compose.yml
version: "3.9"
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    environment:
      - DB_HOST=postgres
      - REDIS_HOST=redis
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 512M
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: admin
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    volumes:
      - pg_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U admin"]
      interval: 10s
      timeout: 5s
      retries: 5
    secrets:
      - db_password

  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data

volumes:
  pg_data:
  redis_data:

secrets:
  db_password:
    file: ./secrets/db_password.txt
```

---

## 2. Kubernetes核心概念

### 2.1 架构概述

```
┌─────────────────── Master Node ───────────────────┐
│  kube-apiserver ── etcd（分布式KV存储）            │
│  kube-scheduler（调度器）                          │
│  kube-controller-manager（控制器管理器）            │
│  cloud-controller-manager（云厂商控制器）           │
└───────────────────────────────────────────────────┘
              │ 通过 kubelet API 通信
┌─────────────────── Worker Node ───────────────────┐
│  kubelet（节点代理）                               │
│  kube-proxy（网络代理，iptables/IPVS）             │
│  Container Runtime（containerd/CRI-O）             │
│  [Pod] [Pod] [Pod]                                │
└───────────────────────────────────────────────────┘
```

### 2.2 核心资源对象

```yaml
# Deployment：无状态应用部署
apiVersion: apps/v1
kind: Deployment
metadata:
  name: go-api
  labels:
    app: go-api
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # 滚动更新时最多多创建1个Pod
      maxUnavailable: 0  # 更新过程中不允许有Pod不可用
  selector:
    matchLabels:
      app: go-api
  template:
    metadata:
      labels:
        app: go-api
    spec:
      containers:
        - name: api
          image: myregistry/go-api:v1.2.0
          ports:
            - containerPort: 8080
          resources:
            requests:         # 调度依据，保证最低资源
              cpu: "100m"
              memory: "128Mi"
            limits:           # 硬上限，超出OOMKill
              cpu: "500m"
              memory: "512Mi"
          livenessProbe:      # 存活探针：失败则重启容器
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 15
          readinessProbe:     # 就绪探针：失败则摘除流量
            httpGet:
              path: /ready
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
          env:
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: db-secret
                  key: password
---
# Service：服务发现和负载均衡
apiVersion: v1
kind: Service
metadata:
  name: go-api-svc
spec:
  type: ClusterIP
  selector:
    app: go-api
  ports:
    - port: 80
      targetPort: 8080
---
# Ingress：外部HTTP路由
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: go-api-ingress
  annotations:
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  ingressClassName: nginx
  tls:
    - hosts: [api.example.com]
      secretName: tls-secret
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /api/v1
            pathType: Prefix
            backend:
              service:
                name: go-api-svc
                port:
                  number: 80
```

### 2.3 HPA自动扩缩容

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: go-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: go-api
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 30   # 快速扩容
      policies:
        - type: Percent
          value: 100
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300  # 缓慢缩容，防止抖动
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
```

### 2.4 调度策略

```yaml
spec:
  # 节点亲和性：调度到特定标签的节点
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: disktype
                operator: In
                values: [ssd]
    # Pod反亲和性：同一应用的Pod分散到不同节点
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
        - weight: 100
          podAffinityTerm:
            labelSelector:
              matchLabels:
                app: go-api
            topologyKey: kubernetes.io/hostname
  # 容忍污点：允许调度到有特定污点的节点
  tolerations:
    - key: "gpu"
      operator: "Equal"
      value: "true"
      effect: "NoSchedule"
```

---

## 3. Go与Kubernetes

### 3.1 client-go开发

```go
package main

import (
    "context"
    "fmt"
    "os"
    "path/filepath"

    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
    "k8s.io/client-go/kubernetes"
    "k8s.io/client-go/tools/clientcmd"
)

func main() {
    // 加载kubeconfig
    home, _ := os.UserHomeDir()
    kubeconfig := filepath.Join(home, ".kube", "config")
    config, err := clientcmd.BuildConfigFromFlags("", kubeconfig)
    if err != nil {
        panic(err)
    }

    // 创建clientset
    clientset, err := kubernetes.NewForConfig(config)
    if err != nil {
        panic(err)
    }

    // 列出所有Pods
    pods, err := clientset.CoreV1().Pods("default").List(
        context.TODO(), metav1.ListOptions{},
    )
    if err != nil {
        panic(err)
    }

    for _, pod := range pods.Items {
        fmt.Printf("Pod: %s, Status: %s\n", pod.Name, pod.Status.Phase)
    }

    // 动态扩缩Deployment
    scale, _ := clientset.AppsV1().Deployments("default").GetScale(
        context.TODO(), "go-api", metav1.GetOptions{},
    )
    scale.Spec.Replicas = 5
    _, err = clientset.AppsV1().Deployments("default").UpdateScale(
        context.TODO(), "go-api", scale, metav1.UpdateOptions{},
    )
    if err != nil {
        fmt.Printf("扩容失败: %v\n", err)
    }
}
```

### 3.2 Informer机制与Custom Controller

```go
package main

import (
    "fmt"
    "time"

    v1 "k8s.io/api/core/v1"
    "k8s.io/apimachinery/pkg/util/wait"
    "k8s.io/client-go/informers"
    "k8s.io/client-go/kubernetes"
    "k8s.io/client-go/tools/cache"
    "k8s.io/client-go/tools/clientcmd"
    "k8s.io/client-go/util/workqueue"
)

// Informer核心架构：
// API Server --> Reflector(List/Watch) --> DeltaFIFO --> Indexer(本地缓存)
//                                              |
//                                         EventHandler --> WorkQueue --> Controller处理

type PodController struct {
    informer  cache.SharedIndexInformer
    workqueue workqueue.RateLimitingInterface
}

func NewPodController(clientset *kubernetes.Clientset) *PodController {
    // 创建SharedInformerFactory（全局共享，避免重复List/Watch）
    factory := informers.NewSharedInformerFactory(clientset, 30*time.Second)
    podInformer := factory.Core().V1().Pods().Informer()

    queue := workqueue.NewRateLimitingQueue(
        workqueue.DefaultControllerRateLimiter(),
    )

    controller := &PodController{
        informer:  podInformer,
        workqueue: queue,
    }

    // 注册事件处理函数
    podInformer.AddEventHandler(cache.ResourceEventHandlerFuncs{
        AddFunc: func(obj interface{}) {
            key, err := cache.MetaNamespaceKeyFunc(obj)
            if err == nil {
                queue.Add(key)
            }
        },
        UpdateFunc: func(oldObj, newObj interface{}) {
            key, err := cache.MetaNamespaceKeyFunc(newObj)
            if err == nil {
                queue.Add(key)
            }
        },
        DeleteFunc: func(obj interface{}) {
            key, err := cache.DeletionHandlingMetaNamespaceKeyFunc(obj)
            if err == nil {
                queue.Add(key)
            }
        },
    })

    return controller
}

func (c *PodController) Run(stopCh <-chan struct{}) {
    go c.informer.Run(stopCh)

    // 等待缓存同步完成
    if !cache.WaitForCacheSync(stopCh, c.informer.HasSynced) {
        fmt.Println("缓存同步超时")
        return
    }

    // 启动worker处理队列中的事件
    go wait.Until(c.runWorker, time.Second, stopCh)
    <-stopCh
}

func (c *PodController) runWorker() {
    for c.processNextItem() {
    }
}

func (c *PodController) processNextItem() bool {
    key, quit := c.workqueue.Get()
    if quit {
        return false
    }
    defer c.workqueue.Done(key)

    err := c.reconcile(key.(string))
    if err == nil {
        c.workqueue.Forget(key)
    } else {
        c.workqueue.AddRateLimited(key) // 失败重试
    }
    return true
}

func (c *PodController) reconcile(key string) error {
    namespace, name, _ := cache.SplitMetaNamespaceKey(key)
    // 从本地缓存读取（不直接访问API Server）
    obj, exists, err := c.informer.GetStore().GetByKey(key)
    if err != nil || !exists {
        fmt.Printf("Pod已删除: %s/%s\n", namespace, name)
        return nil
    }
    pod := obj.(*v1.Pod)
    fmt.Printf("Reconcile Pod: %s/%s, Phase: %s\n",
        namespace, name, pod.Status.Phase)
    return nil
}
```

### 3.3 CRD与Operator模式

```go
// 定义CRD结构体（api/v1/types.go）
// +kubebuilder:object:root=true
// +kubebuilder:subresource:status
// +kubebuilder:printcolumn:name="Replicas",type=integer,JSONPath=`.spec.replicas`
type MyApp struct {
    metav1.TypeMeta   `json:",inline"`
    metav1.ObjectMeta `json:"metadata,omitempty"`
    Spec   MyAppSpec   `json:"spec,omitempty"`
    Status MyAppStatus `json:"status,omitempty"`
}

type MyAppSpec struct {
    Image    string `json:"image"`
    Replicas int32  `json:"replicas"`
    Port     int32  `json:"port"`
}

type MyAppStatus struct {
    AvailableReplicas int32  `json:"availableReplicas"`
    Phase             string `json:"phase"` // Pending/Running/Failed
}

// Operator Reconcile逻辑核心思想：
// 期望状态(Spec) vs 实际状态(Status) --> 驱动操作让实际趋近期望
```

### 3.4 Admission Webhook

```go
// Validating Webhook：校验Pod必须设置资源限制
func handleValidate(w http.ResponseWriter, r *http.Request) {
    var admissionReview admissionv1.AdmissionReview
    json.NewDecoder(r.Body).Decode(&admissionReview)

    pod := &corev1.Pod{}
    json.Unmarshal(admissionReview.Request.Object.Raw, pod)

    allowed := true
    message := "验证通过"

    for _, container := range pod.Spec.Containers {
        if container.Resources.Limits == nil {
            allowed = false
            message = fmt.Sprintf("容器 %s 必须设置resources.limits", container.Name)
            break
        }
    }

    resp := &admissionv1.AdmissionResponse{
        UID:     admissionReview.Request.UID,
        Allowed: allowed,
        Result:  &metav1.Status{Message: message},
    }

    admissionReview.Response = resp
    json.NewEncoder(w).Encode(admissionReview)
}
```

---

## 4. 服务网格

### 4.1 Istio架构

```
┌─────── 控制平面（istiod） ───────┐
│  Pilot（配置下发、服务发现）       │
│  Citadel（证书管理、mTLS）        │
│  Galley（配置验证）               │
└──────────────────────────────────┘
          │ xDS协议下发配置
┌─────── 数据平面 ─────────────────┐
│  Pod A                           │
│  ┌───────────┐  ┌─────────────┐  │
│  │ App容器    │←→│ Envoy Sidecar│  │
│  └───────────┘  └─────────────┘  │
│                       ↕ mTLS     │
│  Pod B                           │
│  ┌───────────┐  ┌─────────────┐  │
│  │ App容器    │←→│ Envoy Sidecar│  │
│  └───────────┘  └─────────────┘  │
└──────────────────────────────────┘
```

### 4.2 流量管理

```yaml
# VirtualService：金丝雀发布，90%流量到v1，10%到v2
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: go-api
spec:
  hosts:
    - go-api
  http:
    - match:
        - headers:
            x-canary:
              exact: "true"
      route:
        - destination:
            host: go-api
            subset: v2
    - route:
        - destination:
            host: go-api
            subset: v1
          weight: 90
        - destination:
            host: go-api
            subset: v2
          weight: 10
---
# DestinationRule：定义子集和负载均衡策略
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: go-api
spec:
  host: go-api
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        h2UpgradePolicy: UPGRADE
    outlierDetection:     # 熔断配置
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 30s
  subsets:
    - name: v1
      labels:
        version: v1
    - name: v2
      labels:
        version: v2
```

---

## 5. CI/CD与GitOps

### 5.1 GitHub Actions Pipeline

```yaml
# .github/workflows/deploy.yml
name: Build & Deploy
on:
  push:
    branches: [main]
    tags: ["v*"]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: "1.22"
      - run: go test -race -coverprofile=coverage.out ./...
      - run: go vet ./...

  build-push:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    needs: build-push
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: 更新Helm values中的镜像tag
        run: |
          sed -i "s/tag:.*/tag: ${{ github.sha }}/" helm/values.yaml
      - name: 提交变更触发ArgoCD同步
        run: |
          git config user.name "github-actions"
          git config user.email "actions@github.com"
          git commit -am "deploy: update image to ${{ github.sha }}"
          git push
```

### 5.2 Helm Chart核心结构

```yaml
# helm/values.yaml
replicaCount: 3
image:
  repository: ghcr.io/myorg/go-api
  tag: latest
  pullPolicy: IfNotPresent
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 20
  targetCPUUtilization: 70
ingress:
  enabled: true
  hostname: api.example.com
  tls: true
```

---

## 6. 云原生可观测性

### 6.1 Prometheus + Go应用集成

```go
package main

import (
    "net/http"
    "time"

    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
    httpRequestsTotal = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "http_requests_total",
            Help: "HTTP请求总数",
        },
        []string{"method", "path", "status"},
    )

    httpRequestDuration = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "http_request_duration_seconds",
            Help:    "HTTP请求延迟分布",
            Buckets: []float64{0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5},
        },
        []string{"method", "path"},
    )

    activeConnections = prometheus.NewGauge(
        prometheus.GaugeOpts{
            Name: "active_connections",
            Help: "当前活跃连接数",
        },
    )
)

func init() {
    prometheus.MustRegister(httpRequestsTotal, httpRequestDuration, activeConnections)
}

// 中间件：自动采集请求指标
func metricsMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        activeConnections.Inc()
        defer activeConnections.Dec()

        wrapped := &statusWriter{ResponseWriter: w, status: 200}
        next.ServeHTTP(wrapped, r)

        duration := time.Since(start).Seconds()
        httpRequestsTotal.WithLabelValues(
            r.Method, r.URL.Path, fmt.Sprintf("%d", wrapped.status),
        ).Inc()
        httpRequestDuration.WithLabelValues(r.Method, r.URL.Path).Observe(duration)
    })
}

func main() {
    mux := http.NewServeMux()
    mux.Handle("/metrics", promhttp.Handler())
    mux.HandleFunc("/api/users", handleUsers)
    http.ListenAndServe(":8080", metricsMiddleware(mux))
}
```

### 6.2 OpenTelemetry集成

```go
package main

import (
    "context"
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
    "go.opentelemetry.io/otel/sdk/resource"
    sdktrace "go.opentelemetry.io/otel/sdk/trace"
    semconv "go.opentelemetry.io/otel/semconv/v1.21.0"
    "go.opentelemetry.io/otel/trace"
)

func initTracer() (*sdktrace.TracerProvider, error) {
    exporter, err := otlptracehttp.New(context.Background(),
        otlptracehttp.WithEndpoint("otel-collector:4318"),
        otlptracehttp.WithInsecure(),
    )
    if err != nil {
        return nil, err
    }

    tp := sdktrace.NewTracerProvider(
        sdktrace.WithBatcher(exporter),
        sdktrace.WithResource(resource.NewWithAttributes(
            semconv.SchemaURL,
            semconv.ServiceName("go-api"),
            semconv.ServiceVersion("v1.2.0"),
            semconv.DeploymentEnvironment("production"),
        )),
        sdktrace.WithSampler(sdktrace.ParentBased(
            sdktrace.TraceIDRatioBased(0.1), // 生产环境采样10%
        )),
    )
    otel.SetTracerProvider(tp)
    return tp, nil
}

func handleOrder(ctx context.Context) error {
    tracer := otel.Tracer("order-service")

    ctx, span := tracer.Start(ctx, "handleOrder",
        trace.WithAttributes(
            attribute.String("order.type", "standard"),
        ),
    )
    defer span.End()

    // 子span：数据库查询
    ctx, dbSpan := tracer.Start(ctx, "db.query")
    // ... 数据库操作
    dbSpan.End()

    // 子span：调用外部服务
    ctx, rpcSpan := tracer.Start(ctx, "rpc.payment")
    // ... RPC调用
    rpcSpan.End()

    return nil
}
```

### 6.3 日志与链路追踪最佳实践

**结构化日志（使用slog）：**

```go
import "log/slog"

logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
    Level: slog.LevelInfo,
}))

// 关联Trace ID实现日志与链路追踪联动
logger.Info("订单创建成功",
    slog.String("trace_id", span.SpanContext().TraceID().String()),
    slog.String("order_id", orderID),
    slog.Int("amount", 9900),
    slog.Duration("latency", time.Since(start)),
)
// 输出: {"time":"...","level":"INFO","msg":"订单创建成功","trace_id":"abc123","order_id":"ORD-001",...}
```

**可观测性三支柱关联：**
| 支柱 | 工具 | 作用 |
|------|------|------|
| Metrics | Prometheus + Grafana | 发现异常（延迟升高/错误率飙升） |
| Logging | Loki / ELK | 定位具体错误信息 |
| Tracing | Jaeger / Tempo | 追踪请求在微服务间的完整链路 |

通过Trace ID将三者关联，实现从告警到根因的快速定位。

---

## 7. 面试题精选

### Q1：Docker镜像分层存储的原理是什么？如何优化镜像大小？

**答：** Docker镜像采用UnionFS分层存储，每条Dockerfile指令生成一个只读层，容器运行时在最上层添加可写层。优化手段包括：使用多阶段构建将编译环境和运行环境分离；合并RUN指令减少层数；使用Alpine/scratch/distroless作为基础镜像；`.dockerignore`排除无关文件；Go应用使用`CGO_ENABLED=0`静态编译后可用scratch零基础镜像，最终镜像仅包含单个二进制文件。

### Q2：Kubernetes中Pod的生命周期有哪些阶段？

**答：** Pod的Phase包括：Pending（已接受但未调度或镜像拉取中）、Running（至少一个容器在运行）、Succeeded（所有容器正常退出）、Failed（至少一个容器异常退出）、Unknown（节点通信失败）。关键机制包括：Init Container先于业务容器运行；PostStart/PreStop生命周期钩子；三种探针（Liveness/Readiness/Startup）控制容器健康状态和流量路由。

### Q3：Kubernetes的调度流程是怎样的？

**答：** kube-scheduler的调度分为两个阶段：(1)预选（Filtering）：根据资源需求、nodeSelector、亲和/反亲和规则、污点容忍等条件过滤不满足的节点；(2)优选（Scoring）：对候选节点打分，考虑资源均衡度、节点亲和性权重、Pod拓扑分散等因素，选择得分最高的节点。绑定后kubelet创建Pod。

### Q4：Informer机制的工作原理和优势？

**答：** Informer通过List+Watch机制与API Server交互：首次List获取全量数据存入本地缓存（Indexer），之后Watch增量事件。事件经过DeltaFIFO队列分发到注册的EventHandler，再写入WorkQueue供Controller消费。优势：大幅减少API Server压力（读请求走本地缓存）；SharedInformer多个Controller共享同一份缓存；WorkQueue支持去重、限速重试。

### Q5：如何实现Kubernetes的零停机部署？

**答：** 综合方案包括：RollingUpdate策略配置`maxSurge=1, maxUnavailable=0`确保始终有足够Pod提供服务；Readiness Probe确保新Pod就绪后才接收流量；PreStop Hook中加入`sleep 5`等待Endpoint更新传播；PodDisruptionBudget限制同时不可用Pod数量；优雅关闭代码在收到SIGTERM后停止接收新请求、完成进行中的请求、释放资源。

### Q6：Istio服务网格的Sidecar注入原理是什么？

**答：** Istio通过Mutating Admission Webhook在Pod创建时自动注入Envoy Sidecar容器和Init容器。Init容器通过iptables规则劫持所有入站/出站流量到Envoy。Envoy作为透明代理处理mTLS加密、负载均衡、熔断、重试、流量路由等功能，业务代码无需修改。控制平面istiod通过xDS协议向Envoy推送配置。

### Q7：Prometheus的Pull模式有什么优势？

**答：** Pull模式（Prometheus主动抓取目标/metrics端点）的优势：服务端控制抓取频率和目标，灵活可靠；目标异常时能通过up指标快速发现；无需在应用中配置推送地址，解耦更彻底；配合ServiceMonitor可自动发现K8s中的监控目标。短生命周期任务可通过Pushgateway补充Push能力。

### Q8：如何设计Kubernetes资源的requests和limits？

**答：** requests是调度保证值，limits是硬上限。CPU超limits会被throttle（限流），内存超limits会OOMKill。最佳实践：通过VPA或实际监控数据确定基线；requests设为P95使用量，limits设为requests的2-3倍；QoS等级：Guaranteed（requests=limits）适合核心服务，Burstable适合一般服务，BestEffort（无设置）仅用于非关键任务。

### Q9：GitOps的核心原则是什么？ArgoCD如何实现？

**答：** GitOps核心原则：Git仓库作为唯一真实来源（Single Source of Truth）；所有变更通过Git提交驱动；系统自动将集群状态收敛至Git中的期望状态。ArgoCD实现：持续监控Git仓库与集群状态的差异（Drift Detection）；检测到差异后自动或手动触发同步；支持Helm、Kustomize、原生YAML等多种清单格式；提供完整的回滚能力和审计日志。

### Q10：如何实现Kubernetes集群的多租户隔离？

**答：** 多层隔离策略：Namespace级别的逻辑隔离；RBAC精细权限控制（Role/ClusterRole）；ResourceQuota限制Namespace资源总量；LimitRange设置单个Pod默认资源配额；NetworkPolicy实现Pod间网络隔离；PodSecurityStandard限制容器权限（禁止root、只读文件系统等）；如需更强隔离可使用Virtual Cluster（vcluster）或Kata Container。

### Q11：OpenTelemetry在微服务可观测性中的作用？

**答：** OpenTelemetry（OTel）是CNCF统一的可观测性框架，提供Traces、Metrics、Logs三种信号的标准化采集SDK和协议（OTLP）。优势：厂商中立，避免锁定；自动检测（Auto-Instrumentation）减少代码侵入；OTel Collector作为统一网关，支持多种后端（Jaeger、Prometheus、Loki等）。Go中通过`otel` SDK创建Tracer/Meter，结合Middleware自动注入到HTTP/gRPC调用链。

### Q12：容器安全的最佳实践有哪些？

**答：** 镜像安全：使用distroless/scratch最小镜像、Trivy扫描CVE漏洞、签名验证（Cosign）；运行时安全：非root用户运行、只读根文件系统、禁止特权模式；K8s安全：PodSecurityStandard/OPA Gatekeeper策略执行、NetworkPolicy最小化网络暴露；供应链安全：SBOM（软件物料清单）、镜像来源可追溯、依赖自动更新（Dependabot/Renovate）。
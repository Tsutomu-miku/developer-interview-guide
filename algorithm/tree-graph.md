# 树与图经典算法题

树和图是面试中的重要考点，涉及递归思维、BFS/DFS 遍历、分治策略以及拓扑排序等核心技巧。本章覆盖二叉树和图领域最常见的面试题，每道题均给出 JavaScript 和 Go 两种语言的完整实现。

---

## 二叉树前中后序遍历

**题目描述：** 给定一棵二叉树的根节点 `root`，分别返回它的前序遍历（根-左-右）、中序遍历（左-根-右）和后序遍历（左-右-根）结果。

**思路分析：**

**递归法：** 最直观的方式，按照遍历顺序递归处理左右子树即可。

**迭代法（前序）：** 使用栈，先将根节点入栈，每次弹出栈顶节点访问，然后先压右子节点再压左子节点（保证左子树先处理）。

**迭代法（中序）：** 使用栈，先沿左子树一路入栈到底，然后弹出访问，再转向右子树重复此过程。

**迭代法（后序）：** 可以用前序遍历的变形（根-右-左）然后反转结果；也可以用标记法在栈中记录节点是否已处理过右子树。

**时间复杂度：** O(n)，空间复杂度 O(n)。

```javascript
// 递归法 —— 前序
function preorderTraversal(root) {
  const result = [];
  function dfs(node) {
    if (node === null) return;
    result.push(node.val);
    dfs(node.left);
    dfs(node.right);
  }
  dfs(root);
  return result;
}

// 递归法 —— 中序
function inorderTraversal(root) {
  const result = [];
  function dfs(node) {
    if (node === null) return;
    dfs(node.left);
    result.push(node.val);
    dfs(node.right);
  }
  dfs(root);
  return result;
}

// 递归法 —— 后序
function postorderTraversal(root) {
  const result = [];
  function dfs(node) {
    if (node === null) return;
    dfs(node.left);
    dfs(node.right);
    result.push(node.val);
  }
  dfs(root);
  return result;
}

// 迭代法 —— 前序
function preorderIterative(root) {
  if (root === null) return [];
  const result = [], stack = [root];
  while (stack.length > 0) {
    const node = stack.pop();
    result.push(node.val);
    if (node.right) stack.push(node.right);
    if (node.left) stack.push(node.left);
  }
  return result;
}

// 迭代法 —— 中序
function inorderIterative(root) {
  const result = [], stack = [];
  let curr = root;
  while (curr !== null || stack.length > 0) {
    while (curr !== null) {
      stack.push(curr);
      curr = curr.left;
    }
    curr = stack.pop();
    result.push(curr.val);
    curr = curr.right;
  }
  return result;
}

// 迭代法 —— 后序（前序变形取反）
function postorderIterative(root) {
  if (root === null) return [];
  const result = [], stack = [root];
  while (stack.length > 0) {
    const node = stack.pop();
    result.push(node.val);
    if (node.left) stack.push(node.left);
    if (node.right) stack.push(node.right);
  }
  return result.reverse();
}
```

```go
// 递归法 —— 前序
func preorderTraversal(root *TreeNode) []int {
    var result []int
    var dfs func(*TreeNode)
    dfs = func(node *TreeNode) {
        if node == nil {
            return
        }
        result = append(result, node.Val)
        dfs(node.Left)
        dfs(node.Right)
    }
    dfs(root)
    return result
}

// 递归法 —— 中序
func inorderTraversal(root *TreeNode) []int {
    var result []int
    var dfs func(*TreeNode)
    dfs = func(node *TreeNode) {
        if node == nil {
            return
        }
        dfs(node.Left)
        result = append(result, node.Val)
        dfs(node.Right)
    }
    dfs(root)
    return result
}

// 递归法 —— 后序
func postorderTraversal(root *TreeNode) []int {
    var result []int
    var dfs func(*TreeNode)
    dfs = func(node *TreeNode) {
        if node == nil {
            return
        }
        dfs(node.Left)
        dfs(node.Right)
        result = append(result, node.Val)
    }
    dfs(root)
    return result
}

// 迭代法 —— 中序
func inorderIterative(root *TreeNode) []int {
    var result []int
    var stack []*TreeNode
    curr := root
    for curr != nil || len(stack) > 0 {
        for curr != nil {
            stack = append(stack, curr)
            curr = curr.Left
        }
        curr = stack[len(stack)-1]
        stack = stack[:len(stack)-1]
        result = append(result, curr.Val)
        curr = curr.Right
    }
    return result
}
```

---

## 层序遍历（BFS）

**题目描述：** 给你二叉树的根节点 `root`，返回其节点值的层序遍历结果（即逐层地，从左到右访问所有节点）。

**思路分析：** 使用队列实现 BFS。初始将根节点入队，每次处理当前层的所有节点（记录当前队列长度），将它们的值加入当前层的结果数组，并将其子节点入队。循环直到队列为空。

**时间复杂度：** O(n)，空间复杂度 O(n)。

```javascript
function levelOrder(root) {
  if (root === null) return [];
  const result = [];
  const queue = [root];
  while (queue.length > 0) {
    const levelSize = queue.length;
    const level = [];
    for (let i = 0; i < levelSize; i++) {
      const node = queue.shift();
      level.push(node.val);
      if (node.left) queue.push(node.left);
      if (node.right) queue.push(node.right);
    }
    result.push(level);
  }
  return result;
}
```

```go
func levelOrder(root *TreeNode) [][]int {
    if root == nil {
        return nil
    }
    var result [][]int
    queue := []*TreeNode{root}
    for len(queue) > 0 {
        levelSize := len(queue)
        level := make([]int, 0, levelSize)
        for i := 0; i < levelSize; i++ {
            node := queue[0]
            queue = queue[1:]
            level = append(level, node.Val)
            if node.Left != nil {
                queue = append(queue, node.Left)
            }
            if node.Right != nil {
                queue = append(queue, node.Right)
            }
        }
        result = append(result, level)
    }
    return result
}
```

---

## 二叉树最大深度与最小深度

**题目描述：**
- **最大深度：** 给定一棵二叉树，找出其最大深度。最大深度是从根节点到最远叶子节点的最长路径上的节点数。
- **最小深度：** 找出从根节点到最近叶子节点的最短路径上的节点数。

**思路分析：** 最大深度使用递归：`maxDepth(root) = 1 + max(maxDepth(left), maxDepth(right))`。最小深度需要注意：当某个子树为空时不能取 0，因为空子树那一侧没有叶子节点。只有当左右子树都不为空时才取两者较小值；若一侧为空则取另一侧。

**时间复杂度：** O(n)，空间复杂度 O(h)，h 为树的高度。

```javascript
function maxDepth(root) {
  if (root === null) return 0;
  return 1 + Math.max(maxDepth(root.left), maxDepth(root.right));
}

function minDepth(root) {
  if (root === null) return 0;
  if (root.left === null) return 1 + minDepth(root.right);
  if (root.right === null) return 1 + minDepth(root.left);
  return 1 + Math.min(minDepth(root.left), minDepth(root.right));
}
```

```go
func maxDepth(root *TreeNode) int {
    if root == nil {
        return 0
    }
    left := maxDepth(root.Left)
    right := maxDepth(root.Right)
    if left > right {
        return 1 + left
    }
    return 1 + right
}

func minDepth(root *TreeNode) int {
    if root == nil {
        return 0
    }
    if root.Left == nil {
        return 1 + minDepth(root.Right)
    }
    if root.Right == nil {
        return 1 + minDepth(root.Left)
    }
    left := minDepth(root.Left)
    right := minDepth(root.Right)
    if left < right {
        return 1 + left
    }
    return 1 + right
}
```

---

## 验证二叉搜索树

**题目描述：** 给你一个二叉树的根节点 `root`，判断其是否是一个有效的二叉搜索树（BST）。有效 BST 的定义：左子树所有节点的值小于根节点，右子树所有节点的值大于根节点，且左右子树也都是 BST。

**思路分析：** 递归时传入当前节点允许的值范围 `(min, max)`。根节点范围为 `(-Infinity, +Infinity)`。左子节点的上界更新为父节点的值，右子节点的下界更新为父节点的值。也可以利用 BST 的中序遍历是严格递增序列这一性质来验证。

**时间复杂度：** O(n)，空间复杂度 O(h)。

```javascript
function isValidBST(root) {
  function validate(node, min, max) {
    if (node === null) return true;
    if (node.val <= min || node.val >= max) return false;
    return validate(node.left, min, node.val) &&
           validate(node.right, node.val, max);
  }
  return validate(root, -Infinity, Infinity);
}
```

```go
func isValidBST(root *TreeNode) bool {
    return validate(root, math.MinInt64, math.MaxInt64)
}

func validate(node *TreeNode, min, max int) bool {
    if node == nil {
        return true
    }
    if node.Val <= min || node.Val >= max {
        return false
    }
    return validate(node.Left, min, node.Val) && validate(node.Right, node.Val, max)
}
```

---

## 二叉树的最近公共祖先

**题目描述：** 给定一棵二叉树的根节点 `root` 和两个节点 `p`、`q`，找到它们的最近公共祖先（LCA）。最近公共祖先是指在树中同时拥有 `p` 和 `q` 作为后代的最深节点（节点也可以是自身的后代）。

**思路分析：** 递归遍历整棵树。对于当前节点，如果为 null 或等于 p 或 q，则直接返回当前节点。递归地在左右子树中查找 p 和 q。如果左右子树的返回值都不为 null，说明 p 和 q 分别在当前节点的两侧，当前节点即为 LCA。如果只有一侧返回非 null，则 LCA 在那一侧。

**时间复杂度：** O(n)，空间复杂度 O(h)。

```javascript
function lowestCommonAncestor(root, p, q) {
  if (root === null || root === p || root === q) return root;
  const left = lowestCommonAncestor(root.left, p, q);
  const right = lowestCommonAncestor(root.right, p, q);
  if (left !== null && right !== null) return root;
  return left !== null ? left : right;
}
```

```go
func lowestCommonAncestor(root, p, q *TreeNode) *TreeNode {
    if root == nil || root == p || root == q {
        return root
    }
    left := lowestCommonAncestor(root.Left, p, q)
    right := lowestCommonAncestor(root.Right, p, q)
    if left != nil && right != nil {
        return root
    }
    if left != nil {
        return left
    }
    return right
}
```

---

## 翻转二叉树

**题目描述：** 给你一棵二叉树的根节点 `root`，翻转这棵二叉树（即将每个节点的左右子树交换），并返回其根节点。

**思路分析：** 递归地交换每个节点的左右子树。对于当前节点，先递归翻转左子树和右子树，然后交换左右子节点的引用。base case 是节点为 null 时返回 null。

**时间复杂度：** O(n)，空间复杂度 O(h)。

```javascript
function invertTree(root) {
  if (root === null) return null;
  const left = invertTree(root.left);
  const right = invertTree(root.right);
  root.left = right;
  root.right = left;
  return root;
}
```

```go
func invertTree(root *TreeNode) *TreeNode {
    if root == nil {
        return nil
    }
    left := invertTree(root.Left)
    right := invertTree(root.Right)
    root.Left = right
    root.Right = left
    return root
}
```

---

## 从前序与中序遍历构造二叉树

**题目描述：** 给定两个整数数组 `preorder` 和 `inorder`，其中 `preorder` 是二叉树的前序遍历，`inorder` 是同一棵树的中序遍历，请构造并返回这棵二叉树。

**思路分析：** 前序遍历的第一个元素是根节点。在中序遍历中找到根节点的位置，其左边是左子树的中序遍历，右边是右子树的中序遍历。由此可以确定左右子树的节点个数，进而在前序遍历中划分出左右子树的前序遍历。递归地构造左右子树。为了快速查找中序遍历中根节点的位置，预先建立值到下标的哈希映射。

**时间复杂度：** O(n)，空间复杂度 O(n)。

```javascript
function buildTree(preorder, inorder) {
  const indexMap = new Map();
  inorder.forEach((val, idx) => indexMap.set(val, idx));

  function build(preStart, preEnd, inStart, inEnd) {
    if (preStart > preEnd) return null;
    const rootVal = preorder[preStart];
    const root = new TreeNode(rootVal);
    const inRootIdx = indexMap.get(rootVal);
    const leftSize = inRootIdx - inStart;

    root.left = build(preStart + 1, preStart + leftSize, inStart, inRootIdx - 1);
    root.right = build(preStart + leftSize + 1, preEnd, inRootIdx + 1, inEnd);
    return root;
  }

  return build(0, preorder.length - 1, 0, inorder.length - 1);
}
```

```go
func buildTree(preorder []int, inorder []int) *TreeNode {
    indexMap := make(map[int]int)
    for i, v := range inorder {
        indexMap[v] = i
    }

    var build func(preStart, preEnd, inStart, inEnd int) *TreeNode
    build = func(preStart, preEnd, inStart, inEnd int) *TreeNode {
        if preStart > preEnd {
            return nil
        }
        rootVal := preorder[preStart]
        root := &TreeNode{Val: rootVal}
        inRootIdx := indexMap[rootVal]
        leftSize := inRootIdx - inStart

        root.Left = build(preStart+1, preStart+leftSize, inStart, inRootIdx-1)
        root.Right = build(preStart+leftSize+1, preEnd, inRootIdx+1, inEnd)
        return root
    }

    return build(0, len(preorder)-1, 0, len(inorder)-1)
}
```

---

## 二叉树序列化与反序列化

**题目描述：** 请设计一个算法来实现二叉树的序列化与反序列化。序列化是将一棵二叉树转换为某种字符串表示；反序列化是将字符串恢复为原始的二叉树结构。

**思路分析：** 使用前序遍历进行序列化，用特殊标记（如 `"null"`）表示空节点，节点之间用逗号分隔。反序列化时按前序顺序依次读取值，遇到 `"null"` 返回空节点，否则创建节点并递归构建左右子树。也可以使用层序遍历（BFS）方式实现。

**时间复杂度：** O(n)，空间复杂度 O(n)。

```javascript
function serialize(root) {
  const parts = [];
  function dfs(node) {
    if (node === null) {
      parts.push("null");
      return;
    }
    parts.push(String(node.val));
    dfs(node.left);
    dfs(node.right);
  }
  dfs(root);
  return parts.join(",");
}

function deserialize(data) {
  const values = data.split(",");
  let index = 0;
  function dfs() {
    if (values[index] === "null") {
      index++;
      return null;
    }
    const node = new TreeNode(parseInt(values[index]));
    index++;
    node.left = dfs();
    node.right = dfs();
    return node;
  }
  return dfs();
}
```

```go
type Codec struct{}

func (c *Codec) serialize(root *TreeNode) string {
    var parts []string
    var dfs func(*TreeNode)
    dfs = func(node *TreeNode) {
        if node == nil {
            parts = append(parts, "null")
            return
        }
        parts = append(parts, strconv.Itoa(node.Val))
        dfs(node.Left)
        dfs(node.Right)
    }
    dfs(root)
    return strings.Join(parts, ",")
}

func (c *Codec) deserialize(data string) *TreeNode {
    values := strings.Split(data, ",")
    index := 0
    var dfs func() *TreeNode
    dfs = func() *TreeNode {
        if values[index] == "null" {
            index++
            return nil
        }
        val, _ := strconv.Atoi(values[index])
        node := &TreeNode{Val: val}
        index++
        node.Left = dfs()
        node.Right = dfs()
        return node
    }
    return dfs()
}
```

---

## 岛屿数量

**题目描述：** 给你一个由 `'1'`（陆地）和 `'0'`（水）组成的二维网格 `grid`，请计算网格中岛屿的数量。岛屿总是被水包围，并且每座岛屿只能由水平方向和/或垂直方向上相邻的陆地连接形成。

**思路分析：**

**DFS 解法：** 遍历每个格子，遇到 `'1'` 时计数加一，并从该格子出发进行 DFS，将所有相连的 `'1'` 标记为已访问（改为 `'0'` 或使用 visited 数组），防止重复计数。

**BFS 解法：** 类似地，遇到 `'1'` 时用 BFS 将整个连通区域标记为已访问。

**时间复杂度：** O(m x n)，空间复杂度 O(m x n)（最坏情况下递归栈或队列）。

```javascript
// DFS
function numIslands(grid) {
  if (grid.length === 0) return 0;
  const m = grid.length, n = grid[0].length;
  let count = 0;

  function dfs(i, j) {
    if (i < 0 || i >= m || j < 0 || j >= n || grid[i][j] === '0') return;
    grid[i][j] = '0';
    dfs(i + 1, j);
    dfs(i - 1, j);
    dfs(i, j + 1);
    dfs(i, j - 1);
  }

  for (let i = 0; i < m; i++) {
    for (let j = 0; j < n; j++) {
      if (grid[i][j] === '1') {
        count++;
        dfs(i, j);
      }
    }
  }
  return count;
}

// BFS
function numIslandsBFS(grid) {
  if (grid.length === 0) return 0;
  const m = grid.length, n = grid[0].length;
  let count = 0;
  const dirs = [[1,0],[-1,0],[0,1],[0,-1]];

  for (let i = 0; i < m; i++) {
    for (let j = 0; j < n; j++) {
      if (grid[i][j] === '1') {
        count++;
        grid[i][j] = '0';
        const queue = [[i, j]];
        while (queue.length > 0) {
          const [x, y] = queue.shift();
          for (const [dx, dy] of dirs) {
            const nx = x + dx, ny = y + dy;
            if (nx >= 0 && nx < m && ny >= 0 && ny < n && grid[nx][ny] === '1') {
              grid[nx][ny] = '0';
              queue.push([nx, ny]);
            }
          }
        }
      }
    }
  }
  return count;
}
```

```go
// DFS
func numIslands(grid [][]byte) int {
    if len(grid) == 0 {
        return 0
    }
    m, n := len(grid), len(grid[0])
    count := 0

    var dfs func(int, int)
    dfs = func(i, j int) {
        if i < 0 || i >= m || j < 0 || j >= n || grid[i][j] == '0' {
            return
        }
        grid[i][j] = '0'
        dfs(i+1, j)
        dfs(i-1, j)
        dfs(i, j+1)
        dfs(i, j-1)
    }

    for i := 0; i < m; i++ {
        for j := 0; j < n; j++ {
            if grid[i][j] == '1' {
                count++
                dfs(i, j)
            }
        }
    }
    return count
}

// BFS
func numIslandsBFS(grid [][]byte) int {
    if len(grid) == 0 {
        return 0
    }
    m, n := len(grid), len(grid[0])
    count := 0
    dirs := [][2]int{{1, 0}, {-1, 0}, {0, 1}, {0, -1}}

    for i := 0; i < m; i++ {
        for j := 0; j < n; j++ {
            if grid[i][j] == '1' {
                count++
                grid[i][j] = '0'
                queue := [][2]int{{i, j}}
                for len(queue) > 0 {
                    cell := queue[0]
                    queue = queue[1:]
                    for _, d := range dirs {
                        nx, ny := cell[0]+d[0], cell[1]+d[1]
                        if nx >= 0 && nx < m && ny >= 0 && ny < n && grid[nx][ny] == '1' {
                            grid[nx][ny] = '0'
                            queue = append(queue, [2]int{nx, ny})
                        }
                    }
                }
            }
        }
    }
    return count
}
```

---

## 课程表（拓扑排序）

**题目描述：** 你这个学期必须选修 `numCourses` 门课程，记为 `0` 到 `numCourses - 1`。在选修某些课程之前需要一些先修课程，用 `prerequisites[i] = [ai, bi]` 表示修课程 `ai` 之前必须先修 `bi`。判断是否可能完成所有课程的学习（即课程依赖关系中没有环）。

**思路分析：** 这是一个经典的拓扑排序问题。将课程关系建模为有向图，使用 BFS（Kahn 算法）：统计每个节点的入度，将入度为 0 的节点入队。每次出队一个节点，将其所有邻居的入度减一，若某邻居入度变为 0 则入队。最终如果处理的节点数等于总课程数，则没有环，可以完成所有课程。也可以用 DFS 检测环。

**时间复杂度：** O(V + E)，V 为课程数，E 为先修关系数。空间复杂度 O(V + E)。

```javascript
// BFS（Kahn 算法）
function canFinish(numCourses, prerequisites) {
  const inDegree = new Array(numCourses).fill(0);
  const graph = Array.from({ length: numCourses }, () => []);

  for (const [course, pre] of prerequisites) {
    graph[pre].push(course);
    inDegree[course]++;
  }

  const queue = [];
  for (let i = 0; i < numCourses; i++) {
    if (inDegree[i] === 0) queue.push(i);
  }

  let count = 0;
  while (queue.length > 0) {
    const node = queue.shift();
    count++;
    for (const neighbor of graph[node]) {
      inDegree[neighbor]--;
      if (inDegree[neighbor] === 0) queue.push(neighbor);
    }
  }

  return count === numCourses;
}

// 课程表 II —— 返回拓扑排序顺序
function findOrder(numCourses, prerequisites) {
  const inDegree = new Array(numCourses).fill(0);
  const graph = Array.from({ length: numCourses }, () => []);

  for (const [course, pre] of prerequisites) {
    graph[pre].push(course);
    inDegree[course]++;
  }

  const queue = [];
  for (let i = 0; i < numCourses; i++) {
    if (inDegree[i] === 0) queue.push(i);
  }

  const order = [];
  while (queue.length > 0) {
    const node = queue.shift();
    order.push(node);
    for (const neighbor of graph[node]) {
      inDegree[neighbor]--;
      if (inDegree[neighbor] === 0) queue.push(neighbor);
    }
  }

  return order.length === numCourses ? order : [];
}
```

```go
// BFS（Kahn 算法）
func canFinish(numCourses int, prerequisites [][]int) bool {
    inDegree := make([]int, numCourses)
    graph := make([][]int, numCourses)
    for i := range graph {
        graph[i] = []int{}
    }

    for _, p := range prerequisites {
        course, pre := p[0], p[1]
        graph[pre] = append(graph[pre], course)
        inDegree[course]++
    }

    queue := []int{}
    for i := 0; i < numCourses; i++ {
        if inDegree[i] == 0 {
            queue = append(queue, i)
        }
    }

    count := 0
    for len(queue) > 0 {
        node := queue[0]
        queue = queue[1:]
        count++
        for _, neighbor := range graph[node] {
            inDegree[neighbor]--
            if inDegree[neighbor] == 0 {
                queue = append(queue, neighbor)
            }
        }
    }

    return count == numCourses
}

// 课程表 II —— 返回拓扑排序顺序
func findOrder(numCourses int, prerequisites [][]int) []int {
    inDegree := make([]int, numCourses)
    graph := make([][]int, numCourses)
    for i := range graph {
        graph[i] = []int{}
    }

    for _, p := range prerequisites {
        course, pre := p[0], p[1]
        graph[pre] = append(graph[pre], course)
        inDegree[course]++
    }

    queue := []int{}
    for i := 0; i < numCourses; i++ {
        if inDegree[i] == 0 {
            queue = append(queue, i)
        }
    }

    order := []int{}
    for len(queue) > 0 {
        node := queue[0]
        queue = queue[1:]
        order = append(order, node)
        for _, neighbor := range graph[node] {
            inDegree[neighbor]--
            if inDegree[neighbor] == 0 {
                queue = append(queue, neighbor)
            }
        }
    }

    if len(order) == numCourses {
        return order
    }
    return []int{}
}
```

---

## 总结

| 题目 | 核心技巧 | 时间复杂度 |
|------|----------|-----------|
| 前中后序遍历 | 递归 / 栈迭代 | O(n) |
| 层序遍历 | BFS + 队列 | O(n) |
| 最大/最小深度 | 递归 | O(n) |
| 验证 BST | 递归 + 值范围 | O(n) |
| 最近公共祖先 | 递归分治 | O(n) |
| 翻转二叉树 | 递归 | O(n) |
| 前序+中序构造树 | 递归 + 哈希定位 | O(n) |
| 序列化/反序列化 | 前序遍历 + 标记 | O(n) |
| 岛屿数量 | DFS / BFS | O(m x n) |
| 课程表 | 拓扑排序（Kahn） | O(V+E) |

树和图问题的关键在于熟练运用**递归思维**（大多数树的问题都可以分解为子问题）、掌握 **BFS/DFS** 遍历模板，以及理解**拓扑排序**等图算法。面试中要特别注意递归的 base case 和边界条件处理。
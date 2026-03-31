# 动态规划经典题

动态规划（Dynamic Programming，简称 DP）是算法面试中最高频的考点之一。其核心思想是将一个复杂问题拆解为若干重叠子问题，通过记录子问题的解（状态）来避免重复计算，从而实现高效求解。掌握 DP 的关键在于：明确**状态定义**、推导**状态转移方程**、确定**边界条件**和**遍历顺序**。

---

## 爬楼梯（Climbing Stairs）

### 题目描述

假设你正在爬楼梯，需要 `n` 阶才能到达楼顶。每次你可以爬 1 或 2 个台阶，问有多少种不同的方法可以爬到楼顶。

### 思路分析

- **状态定义**：`dp[i]` 表示爬到第 `i` 阶的方法数。
- **转移方程**：`dp[i] = dp[i-1] + dp[i-2]`，因为到第 `i` 阶要么从 `i-1` 爬 1 阶，要么从 `i-2` 爬 2 阶。
- **边界条件**：`dp[0] = 1, dp[1] = 1`。
- **时间复杂度**：O(n)，**空间复杂度**：O(1)（滚动变量优化）。

```javascript
function climbStairs(n) {
  if (n <= 1) return 1;
  let prev2 = 1, prev1 = 1;
  for (let i = 2; i <= n; i++) {
    const curr = prev1 + prev2;
    prev2 = prev1;
    prev1 = curr;
  }
  return prev1;
}
```

```go
func climbStairs(n int) int {
    if n <= 1 {
        return 1
    }
    prev2, prev1 := 1, 1
    for i := 2; i <= n; i++ {
        curr := prev1 + prev2
        prev2 = prev1
        prev1 = curr
    }
    return prev1
}
```

---

## 斐波那契数列（Fibonacci Number）

### 题目描述

斐波那契数列 `F(n)` 定义为：`F(0) = 0, F(1) = 1, F(n) = F(n-1) + F(n-2)`。给定 `n`，计算 `F(n)`。

### 思路分析

与爬楼梯几乎相同，唯一区别是边界值不同。使用滚动变量即可将空间优化到 O(1)。

```javascript
function fib(n) {
  if (n <= 1) return n;
  let prev2 = 0, prev1 = 1;
  for (let i = 2; i <= n; i++) {
    const curr = prev1 + prev2;
    prev2 = prev1;
    prev1 = curr;
  }
  return prev1;
}
```

```go
func fib(n int) int {
    if n <= 1 {
        return n
    }
    prev2, prev1 := 0, 1
    for i := 2; i <= n; i++ {
        curr := prev1 + prev2
        prev2 = prev1
        prev1 = curr
    }
    return prev1
}
```

---

## 打家劫舍 I（House Robber I）

### 题目描述

你是一个专业的小偷，沿街有一排房屋，每间房有一定现金。相邻的房屋装有相互连通的防盗系统，如果两间相邻的房屋同一晚被闯入，系统会自动报警。求在不触动警报的情况下，一夜之内能偷到的最高金额。

### 思路分析

- **状态定义**：`dp[i]` 表示前 `i` 间房能偷到的最大金额。
- **转移方程**：`dp[i] = max(dp[i-1], dp[i-2] + nums[i])`。
- **边界条件**：`dp[0] = nums[0], dp[1] = max(nums[0], nums[1])`。
- **时间复杂度**：O(n)，**空间复杂度**：O(1)。

```javascript
function rob(nums) {
  if (nums.length === 0) return 0;
  if (nums.length === 1) return nums[0];
  let prev2 = nums[0];
  let prev1 = Math.max(nums[0], nums[1]);
  for (let i = 2; i < nums.length; i++) {
    const curr = Math.max(prev1, prev2 + nums[i]);
    prev2 = prev1;
    prev1 = curr;
  }
  return prev1;
}
```

```go
func rob(nums []int) int {
    n := len(nums)
    if n == 0 {
        return 0
    }
    if n == 1 {
        return nums[0]
    }
    prev2 := nums[0]
    prev1 := max(nums[0], nums[1])
    for i := 2; i < n; i++ {
        curr := max(prev1, prev2+nums[i])
        prev2 = prev1
        prev1 = curr
    }
    return prev1
}

func max(a, b int) int {
    if a > b {
        return a
    }
    return b
}
```

---

## 打家劫舍 II（House Robber II）

### 题目描述

房屋围成一圈（首尾相连），其余条件同 I。求不触动警报能偷到的最高金额。

### 思路分析

环形问题拆解为两个线性子问题：偷 `[0, n-2]` 或偷 `[1, n-1]`，取两者的最大值。每个子问题用 House Robber I 的方式求解。

```javascript
function rob(nums) {
  const n = nums.length;
  if (n === 0) return 0;
  if (n === 1) return nums[0];
  if (n === 2) return Math.max(nums[0], nums[1]);

  function robRange(start, end) {
    let prev2 = nums[start];
    let prev1 = Math.max(nums[start], nums[start + 1]);
    for (let i = start + 2; i <= end; i++) {
      const curr = Math.max(prev1, prev2 + nums[i]);
      prev2 = prev1;
      prev1 = curr;
    }
    return prev1;
  }

  return Math.max(robRange(0, n - 2), robRange(1, n - 1));
}
```

```go
func rob(nums []int) int {
    n := len(nums)
    if n == 0 {
        return 0
    }
    if n == 1 {
        return nums[0]
    }
    if n == 2 {
        return max(nums[0], nums[1])
    }

    robRange := func(start, end int) int {
        prev2 := nums[start]
        prev1 := max(nums[start], nums[start+1])
        for i := start + 2; i <= end; i++ {
            curr := max(prev1, prev2+nums[i])
            prev2 = prev1
            prev1 = curr
        }
        return prev1
    }

    return max(robRange(0, n-2), robRange(1, n-1))
}
```

---

## 打家劫舍 III（House Robber III）

### 题目描述

房屋排列成一棵二叉树，直接相连的两个房屋不能同时被偷。求能偷到的最高金额。

### 思路分析

树形 DP：对每个节点返回两个状态——选该节点的最大收益和不选该节点的最大收益。用后序遍历自底向上计算。

```javascript
function rob(root) {
  function dfs(node) {
    if (!node) return [0, 0]; // [不选, 选]
    const left = dfs(node.left);
    const right = dfs(node.right);
    const notRob = Math.max(...left) + Math.max(...right);
    const doRob = node.val + left[0] + right[0];
    return [notRob, doRob];
  }
  return Math.max(...dfs(root));
}
```

```go
func rob(root *TreeNode) int {
    var dfs func(node *TreeNode) (int, int)
    dfs = func(node *TreeNode) (int, int) {
        if node == nil {
            return 0, 0
        }
        lNotRob, lDoRob := dfs(node.Left)
        rNotRob, rDoRob := dfs(node.Right)
        notRob := max(lNotRob, lDoRob) + max(rNotRob, rDoRob)
        doRob := node.Val + lNotRob + rNotRob
        return notRob, doRob
    }
    a, b := dfs(root)
    return max(a, b)
}
```

---

## 最长递增子序列（Longest Increasing Subsequence）

### 题目描述

给定一个整数数组 `nums`，找到其中最长严格递增子序列的长度。

### 思路分析

**方法一：DP**，O(n²)。`dp[i]` 表示以 `nums[i]` 结尾的 LIS 长度，对每个 `i`，遍历 `j < i`，若 `nums[j] < nums[i]`，则 `dp[i] = max(dp[i], dp[j] + 1)`。

**方法二：贪心 + 二分**，O(n log n)。维护一个单调递增的 `tails` 数组，遍历每个元素，用二分查找替换 `tails` 中第一个 `>= nums[i]` 的位置，若都小于则追加。最终 `tails.length` 即答案。

```javascript
// 贪心 + 二分 O(n log n)
function lengthOfLIS(nums) {
  const tails = [];
  for (const num of nums) {
    let lo = 0, hi = tails.length;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (tails[mid] < num) lo = mid + 1;
      else hi = mid;
    }
    tails[lo] = num;
  }
  return tails.length;
}
```

```go
func lengthOfLIS(nums []int) int {
    tails := []int{}
    for _, num := range nums {
        lo, hi := 0, len(tails)
        for lo < hi {
            mid := (lo + hi) / 2
            if tails[mid] < num {
                lo = mid + 1
            } else {
                hi = mid
            }
        }
        if lo == len(tails) {
            tails = append(tails, num)
        } else {
            tails[lo] = num
        }
    }
    return len(tails)
}
```

---

## 最长公共子序列（Longest Common Subsequence）

### 题目描述

给定两个字符串 `text1` 和 `text2`，返回这两个字符串的最长公共子序列的长度。

### 思路分析

- **状态定义**：`dp[i][j]` 表示 `text1[0..i-1]` 和 `text2[0..j-1]` 的 LCS 长度。
- **转移方程**：若 `text1[i-1] == text2[j-1]`，`dp[i][j] = dp[i-1][j-1] + 1`；否则 `dp[i][j] = max(dp[i-1][j], dp[i][j-1])`。
- **时间复杂度**：O(m*n)，**空间复杂度**：O(m*n)，可用滚动数组优化至 O(min(m,n))。

```javascript
function longestCommonSubsequence(text1, text2) {
  const m = text1.length, n = text2.length;
  const dp = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (text1[i - 1] === text2[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }
  return dp[m][n];
}
```

```go
func longestCommonSubsequence(text1 string, text2 string) int {
    m, n := len(text1), len(text2)
    dp := make([][]int, m+1)
    for i := range dp {
        dp[i] = make([]int, n+1)
    }
    for i := 1; i <= m; i++ {
        for j := 1; j <= n; j++ {
            if text1[i-1] == text2[j-1] {
                dp[i][j] = dp[i-1][j-1] + 1
            } else {
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
            }
        }
    }
    return dp[m][n]
}
```

---

## 编辑距离（Edit Distance）

### 题目描述

给定两个单词 `word1` 和 `word2`，求将 `word1` 转换成 `word2` 所使用的最少操作数。可用操作：插入一个字符、删除一个字符、替换一个字符。

### 思路分析

- **状态定义**：`dp[i][j]` 表示 `word1[0..i-1]` 变换为 `word2[0..j-1]` 所需的最少操作数。
- **转移方程**：若 `word1[i-1] == word2[j-1]`，`dp[i][j] = dp[i-1][j-1]`；否则 `dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])`（分别对应删除、插入、替换）。
- **边界条件**：`dp[i][0] = i, dp[0][j] = j`。
- **时间复杂度**：O(m*n)。

```javascript
function minDistance(word1, word2) {
  const m = word1.length, n = word2.length;
  const dp = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
  for (let i = 0; i <= m; i++) dp[i][0] = i;
  for (let j = 0; j <= n; j++) dp[0][j] = j;
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (word1[i - 1] === word2[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1];
      } else {
        dp[i][j] = 1 + Math.min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]);
      }
    }
  }
  return dp[m][n];
}
```

```go
func minDistance(word1 string, word2 string) int {
    m, n := len(word1), len(word2)
    dp := make([][]int, m+1)
    for i := range dp {
        dp[i] = make([]int, n+1)
        dp[i][0] = i
    }
    for j := 0; j <= n; j++ {
        dp[0][j] = j
    }
    for i := 1; i <= m; i++ {
        for j := 1; j <= n; j++ {
            if word1[i-1] == word2[j-1] {
                dp[i][j] = dp[i-1][j-1]
            } else {
                dp[i][j] = 1 + min(dp[i-1][j], min(dp[i][j-1], dp[i-1][j-1]))
            }
        }
    }
    return dp[m][n]
}

func min(a, b int) int {
    if a < b {
        return a
    }
    return b
}
```

---

## 01 背包问题（0/1 Knapsack）

### 题目描述

有 `n` 件物品，每件物品有重量 `w[i]` 和价值 `v[i]`。背包容量为 `W`。每件物品只能选一次，求能放入背包的最大总价值。

### 思路分析

- **状态定义**：`dp[i][j]` 表示前 `i` 件物品、背包容量 `j` 时的最大价值。
- **转移方程**：`dp[i][j] = max(dp[i-1][j], dp[i-1][j-w[i]] + v[i])`（前提 `j >= w[i]`）。
- 空间优化：使用一维数组，**逆序**遍历容量 `j`。
- **时间复杂度**：O(n*W)。

```javascript
function knapsack01(weights, values, W) {
  const n = weights.length;
  const dp = new Array(W + 1).fill(0);
  for (let i = 0; i < n; i++) {
    for (let j = W; j >= weights[i]; j--) {
      dp[j] = Math.max(dp[j], dp[j - weights[i]] + values[i]);
    }
  }
  return dp[W];
}
```

```go
func knapsack01(weights, values []int, W int) int {
    dp := make([]int, W+1)
    for i := 0; i < len(weights); i++ {
        for j := W; j >= weights[i]; j-- {
            if dp[j-weights[i]]+values[i] > dp[j] {
                dp[j] = dp[j-weights[i]] + values[i]
            }
        }
    }
    return dp[W]
}
```

---

## 完全背包问题（Complete Knapsack）

### 题目描述

与 01 背包类似，但每件物品可以选**无限次**。

### 思路分析

与 01 背包唯一的区别：一维 DP 遍历容量时改为**正序**，这样同一件物品可以被多次选取。

```javascript
function knapsackComplete(weights, values, W) {
  const n = weights.length;
  const dp = new Array(W + 1).fill(0);
  for (let i = 0; i < n; i++) {
    for (let j = weights[i]; j <= W; j++) {
      dp[j] = Math.max(dp[j], dp[j - weights[i]] + values[i]);
    }
  }
  return dp[W];
}
```

```go
func knapsackComplete(weights, values []int, W int) int {
    dp := make([]int, W+1)
    for i := 0; i < len(weights); i++ {
        for j := weights[i]; j <= W; j++ {
            if dp[j-weights[i]]+values[i] > dp[j] {
                dp[j] = dp[j-weights[i]] + values[i]
            }
        }
    }
    return dp[W]
}
```

---

## 零钱兑换（Coin Change）

### 题目描述

给定不同面额的硬币 `coins` 和一个总金额 `amount`，求凑成该金额所需的最少硬币个数。每种硬币可以使用无限次。若不能凑成则返回 -1。

### 思路分析

本质是完全背包的变体。`dp[j]` 表示凑成金额 `j` 的最少硬币数，`dp[j] = min(dp[j], dp[j - coin] + 1)`。初始化 `dp[0] = 0`，其余为 `Infinity`。

```javascript
function coinChange(coins, amount) {
  const dp = new Array(amount + 1).fill(Infinity);
  dp[0] = 0;
  for (const coin of coins) {
    for (let j = coin; j <= amount; j++) {
      dp[j] = Math.min(dp[j], dp[j - coin] + 1);
    }
  }
  return dp[amount] === Infinity ? -1 : dp[amount];
}
```

```go
func coinChange(coins []int, amount int) int {
    dp := make([]int, amount+1)
    for i := range dp {
        dp[i] = amount + 1
    }
    dp[0] = 0
    for _, coin := range coins {
        for j := coin; j <= amount; j++ {
            if dp[j-coin]+1 < dp[j] {
                dp[j] = dp[j-coin] + 1
            }
        }
    }
    if dp[amount] > amount {
        return -1
    }
    return dp[amount]
}
```

---

## 买卖股票的最佳时机 I（Best Time to Buy and Sell Stock I）

### 题目描述

给定股票每天的价格数组，你最多只能完成**一笔**交易（买入和卖出各一次），求最大利润。

### 思路分析

遍历价格，维护至今为止的最低价 `minPrice`，每天计算 `price - minPrice` 的最大值即可。时间 O(n)，空间 O(1)。

```javascript
function maxProfit(prices) {
  let minPrice = Infinity, maxP = 0;
  for (const p of prices) {
    if (p < minPrice) minPrice = p;
    else if (p - minPrice > maxP) maxP = p - minPrice;
  }
  return maxP;
}
```

```go
func maxProfit(prices []int) int {
    minPrice := prices[0]
    maxP := 0
    for _, p := range prices {
        if p < minPrice {
            minPrice = p
        } else if p-minPrice > maxP {
            maxP = p - minPrice
        }
    }
    return maxP
}
```

---

## 买卖股票的最佳时机 II（Best Time to Buy and Sell Stock II）

### 题目描述

可以完成**无限次**交易，但同一时间最多持有一股。求最大利润。

### 思路分析

贪心：只要后一天比前一天高就买入卖出（累加所有上涨差价）。也可以用 DP：`dp[i][0]` 不持股，`dp[i][1]` 持股。

```javascript
function maxProfit(prices) {
  let profit = 0;
  for (let i = 1; i < prices.length; i++) {
    if (prices[i] > prices[i - 1]) {
      profit += prices[i] - prices[i - 1];
    }
  }
  return profit;
}
```

```go
func maxProfit(prices []int) int {
    profit := 0
    for i := 1; i < len(prices); i++ {
        if prices[i] > prices[i-1] {
            profit += prices[i] - prices[i-1]
        }
    }
    return profit
}
```

---

## 买卖股票的最佳时机 III（Best Time to Buy and Sell Stock III）

### 题目描述

最多完成**两笔**交易，求最大利润。

### 思路分析

使用状态机 DP。定义四个状态变量：第一次买入 `buy1`、第一次卖出 `sell1`、第二次买入 `buy2`、第二次卖出 `sell2`。依次转移即可。

```javascript
function maxProfit(prices) {
  let buy1 = -Infinity, sell1 = 0;
  let buy2 = -Infinity, sell2 = 0;
  for (const p of prices) {
    buy1 = Math.max(buy1, -p);
    sell1 = Math.max(sell1, buy1 + p);
    buy2 = Math.max(buy2, sell1 - p);
    sell2 = Math.max(sell2, buy2 + p);
  }
  return sell2;
}
```

```go
func maxProfit(prices []int) int {
    buy1, sell1 := -1<<31, 0
    buy2, sell2 := -1<<31, 0
    for _, p := range prices {
        buy1 = max(buy1, -p)
        sell1 = max(sell1, buy1+p)
        buy2 = max(buy2, sell1-p)
        sell2 = max(sell2, buy2+p)
    }
    return sell2
}
```

---

## 买卖股票的最佳时机 IV（Best Time to Buy and Sell Stock IV）

### 题目描述

最多完成 **k 笔**交易，求最大利润。

### 思路分析

推广 III 的状态机思路。使用 `buy[j]` 和 `sell[j]` 分别表示第 `j` 次买入和卖出后的最大利润。当 `k >= n/2` 时退化为无限次交易。

```javascript
function maxProfit(k, prices) {
  const n = prices.length;
  if (k >= Math.floor(n / 2)) {
    let profit = 0;
    for (let i = 1; i < n; i++) {
      if (prices[i] > prices[i - 1]) profit += prices[i] - prices[i - 1];
    }
    return profit;
  }
  const buy = new Array(k + 1).fill(-Infinity);
  const sell = new Array(k + 1).fill(0);
  for (const p of prices) {
    for (let j = 1; j <= k; j++) {
      buy[j] = Math.max(buy[j], sell[j - 1] - p);
      sell[j] = Math.max(sell[j], buy[j] + p);
    }
  }
  return sell[k];
}
```

```go
func maxProfit(k int, prices []int) int {
    n := len(prices)
    if k >= n/2 {
        profit := 0
        for i := 1; i < n; i++ {
            if prices[i] > prices[i-1] {
                profit += prices[i] - prices[i-1]
            }
        }
        return profit
    }
    buy := make([]int, k+1)
    sell := make([]int, k+1)
    for j := range buy {
        buy[j] = -1 << 31
    }
    for _, p := range prices {
        for j := 1; j <= k; j++ {
            buy[j] = max(buy[j], sell[j-1]-p)
            sell[j] = max(sell[j], buy[j]+p)
        }
    }
    return sell[k]
}
```

---

## 最大子数组和（Maximum Subarray / Kadane 算法）

### 题目描述

给定一个整数数组 `nums`，找到具有最大和的连续子数组（至少包含一个元素），返回其最大和。

### 思路分析

**Kadane 算法**：维护以当前元素结尾的最大子数组和 `curMax`。若 `curMax < 0` 则重置为当前元素，否则累加当前元素。全局取最大值。时间 O(n)，空间 O(1)。

```javascript
function maxSubArray(nums) {
  let curMax = nums[0], globalMax = nums[0];
  for (let i = 1; i < nums.length; i++) {
    curMax = Math.max(nums[i], curMax + nums[i]);
    globalMax = Math.max(globalMax, curMax);
  }
  return globalMax;
}
```

```go
func maxSubArray(nums []int) int {
    curMax, globalMax := nums[0], nums[0]
    for i := 1; i < len(nums); i++ {
        if curMax+nums[i] > nums[i] {
            curMax = curMax + nums[i]
        } else {
            curMax = nums[i]
        }
        if curMax > globalMax {
            globalMax = curMax
        }
    }
    return globalMax
}
```

---

## 不同路径（Unique Paths）

### 题目描述

一个机器人位于 `m x n` 网格的左上角，每次只能向下或向右移动一步，求到达右下角共有多少条不同路径。

### 思路分析

- **状态定义**：`dp[i][j]` 表示到达 `(i, j)` 的路径数。
- **转移方程**：`dp[i][j] = dp[i-1][j] + dp[i][j-1]`。
- **边界条件**：第一行和第一列全为 1。
- **时间复杂度**：O(m*n)，空间可优化至 O(n)。

```javascript
function uniquePaths(m, n) {
  const dp = new Array(n).fill(1);
  for (let i = 1; i < m; i++) {
    for (let j = 1; j < n; j++) {
      dp[j] += dp[j - 1];
    }
  }
  return dp[n - 1];
}
```

```go
func uniquePaths(m int, n int) int {
    dp := make([]int, n)
    for j := range dp {
        dp[j] = 1
    }
    for i := 1; i < m; i++ {
        for j := 1; j < n; j++ {
            dp[j] += dp[j-1]
        }
    }
    return dp[n-1]
}
```

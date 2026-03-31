# 回溯与贪心算法

回溯（Backtracking）和贪心（Greedy）是两类重要的算法思想。回溯通过递归穷举所有可能的解空间，在不满足条件时及时"剪枝"回退；贪心则在每一步选择当前最优解，期望通过局部最优达到全局最优。本章涵盖经典回溯模板和高频面试题，以及常见的贪心问题。

---

## 回溯算法模板

回溯的核心框架如下：

```
function backtrack(路径, 选择列表):
    if 满足结束条件:
        收集结果
        return
    for 选择 in 选择列表:
        做选择（加入路径）
        backtrack(路径, 选择列表)
        撤销选择（回退路径）
```

关键要素：**路径**（已做出的选择）、**选择列表**（当前可以做的选择）、**结束条件**（到达决策树底层的条件）。

---

## 全排列 I（Permutations I）

### 题目描述

给定一个不含重复数字的数组 `nums`，返回其所有可能的全排列。

### 思路分析

经典回溯：维护一个 `used` 数组标记哪些数字已被使用。每一层递归遍历所有未使用的数字加入路径，路径长度等于 `nums.length` 时收集结果。

```javascript
function permute(nums) {
  const res = [];
  const used = new Array(nums.length).fill(false);

  function backtrack(path) {
    if (path.length === nums.length) {
      res.push([...path]);
      return;
    }
    for (let i = 0; i < nums.length; i++) {
      if (used[i]) continue;
      used[i] = true;
      path.push(nums[i]);
      backtrack(path);
      path.pop();
      used[i] = false;
    }
  }

  backtrack([]);
  return res;
}
```

```go
func permute(nums []int) [][]int {
    res := [][]int{}
    used := make([]bool, len(nums))
    var backtrack func(path []int)
    backtrack = func(path []int) {
        if len(path) == len(nums) {
            tmp := make([]int, len(path))
            copy(tmp, path)
            res = append(res, tmp)
            return
        }
        for i := 0; i < len(nums); i++ {
            if used[i] {
                continue
            }
            used[i] = true
            path = append(path, nums[i])
            backtrack(path)
            path = path[:len(path)-1]
            used[i] = false
        }
    }
    backtrack([]int{})
    return res
}
```

---

## 全排列 II（Permutations II）

### 题目描述

给定一个**可包含重复数字**的序列 `nums`，返回所有不重复的全排列。

### 思路分析

在全排列 I 的基础上增加去重：先排序，然后在同一层递归中，如果当前数字与前一个相同且前一个未被使用（即刚被撤销），则跳过，避免产生重复排列。

```javascript
function permuteUnique(nums) {
  nums.sort((a, b) => a - b);
  const res = [];
  const used = new Array(nums.length).fill(false);

  function backtrack(path) {
    if (path.length === nums.length) {
      res.push([...path]);
      return;
    }
    for (let i = 0; i < nums.length; i++) {
      if (used[i]) continue;
      if (i > 0 && nums[i] === nums[i - 1] && !used[i - 1]) continue;
      used[i] = true;
      path.push(nums[i]);
      backtrack(path);
      path.pop();
      used[i] = false;
    }
  }

  backtrack([]);
  return res;
}
```

```go
func permuteUnique(nums []int) [][]int {
    sort.Ints(nums)
    res := [][]int{}
    used := make([]bool, len(nums))
    var backtrack func(path []int)
    backtrack = func(path []int) {
        if len(path) == len(nums) {
            tmp := make([]int, len(path))
            copy(tmp, path)
            res = append(res, tmp)
            return
        }
        for i := 0; i < len(nums); i++ {
            if used[i] {
                continue
            }
            if i > 0 && nums[i] == nums[i-1] && !used[i-1] {
                continue
            }
            used[i] = true
            path = append(path, nums[i])
            backtrack(path)
            path = path[:len(path)-1]
            used[i] = false
        }
    }
    backtrack([]int{})
    return res
}
```

---

## 组合总和 I（Combination Sum I）

### 题目描述

给定一个无重复元素的正整数数组 `candidates` 和一个目标数 `target`，找出所有可以使数字和为 `target` 的组合。每个数字可以被**无限制重复选取**。

### 思路分析

回溯 + 剪枝。为避免重复组合，每次从当前索引 `start` 开始选择（而非从 0 开始）。当剩余 `target < 0` 时剪枝。

```javascript
function combinationSum(candidates, target) {
  const res = [];
  candidates.sort((a, b) => a - b);

  function backtrack(start, path, remain) {
    if (remain === 0) {
      res.push([...path]);
      return;
    }
    for (let i = start; i < candidates.length; i++) {
      if (candidates[i] > remain) break; // 剪枝
      path.push(candidates[i]);
      backtrack(i, path, remain - candidates[i]); // 可重复选，所以传 i
      path.pop();
    }
  }

  backtrack(0, [], target);
  return res;
}
```

```go
func combinationSum(candidates []int, target int) [][]int {
    sort.Ints(candidates)
    res := [][]int{}
    var backtrack func(start int, path []int, remain int)
    backtrack = func(start int, path []int, remain int) {
        if remain == 0 {
            tmp := make([]int, len(path))
            copy(tmp, path)
            res = append(res, tmp)
            return
        }
        for i := start; i < len(candidates); i++ {
            if candidates[i] > remain {
                break
            }
            path = append(path, candidates[i])
            backtrack(i, path, remain-candidates[i])
            path = path[:len(path)-1]
        }
    }
    backtrack(0, []int{}, target)
    return res
}
```

---

## 组合总和 II（Combination Sum II）

### 题目描述

`candidates` 中每个数字只能使用**一次**，且 `candidates` 中可能包含重复数字。找出所有和为 `target` 的不重复组合。

### 思路分析

排序后回溯。与 I 的区别：递归时传 `i + 1`（每个元素只用一次），同一层中跳过重复元素（`i > start && candidates[i] === candidates[i-1]`）。

```javascript
function combinationSum2(candidates, target) {
  candidates.sort((a, b) => a - b);
  const res = [];

  function backtrack(start, path, remain) {
    if (remain === 0) {
      res.push([...path]);
      return;
    }
    for (let i = start; i < candidates.length; i++) {
      if (candidates[i] > remain) break;
      if (i > start && candidates[i] === candidates[i - 1]) continue; // 同层去重
      path.push(candidates[i]);
      backtrack(i + 1, path, remain - candidates[i]);
      path.pop();
    }
  }

  backtrack(0, [], target);
  return res;
}
```

```go
func combinationSum2(candidates []int, target int) [][]int {
    sort.Ints(candidates)
    res := [][]int{}
    var backtrack func(start int, path []int, remain int)
    backtrack = func(start int, path []int, remain int) {
        if remain == 0 {
            tmp := make([]int, len(path))
            copy(tmp, path)
            res = append(res, tmp)
            return
        }
        for i := start; i < len(candidates); i++ {
            if candidates[i] > remain {
                break
            }
            if i > start && candidates[i] == candidates[i-1] {
                continue
            }
            path = append(path, candidates[i])
            backtrack(i+1, path, remain-candidates[i])
            path = path[:len(path)-1]
        }
    }
    backtrack(0, []int{}, target)
    return res
}
```

---

## 组合总和 III（Combination Sum III）

### 题目描述

找出所有相加之和为 `n` 的 `k` 个数的组合，组合中只使用数字 1 到 9，每个数字最多使用一次。

### 思路分析

从 1-9 中选 k 个不重复的数使得和为 n。回溯搜索，当 `path.length === k` 且 `remain === 0` 时收集结果。

```javascript
function combinationSum3(k, n) {
  const res = [];

  function backtrack(start, path, remain) {
    if (path.length === k) {
      if (remain === 0) res.push([...path]);
      return;
    }
    for (let i = start; i <= 9; i++) {
      if (i > remain) break;
      path.push(i);
      backtrack(i + 1, path, remain - i);
      path.pop();
    }
  }

  backtrack(1, [], n);
  return res;
}
```

```go
func combinationSum3(k int, n int) [][]int {
    res := [][]int{}
    var backtrack func(start int, path []int, remain int)
    backtrack = func(start int, path []int, remain int) {
        if len(path) == k {
            if remain == 0 {
                tmp := make([]int, len(path))
                copy(tmp, path)
                res = append(res, tmp)
            }
            return
        }
        for i := start; i <= 9; i++ {
            if i > remain {
                break
            }
            path = append(path, i)
            backtrack(i+1, path, remain-i)
            path = path[:len(path)-1]
        }
    }
    backtrack(1, []int{}, n)
    return res
}
```

---

## 子集 I（Subsets I）

### 题目描述

给定一组不含重复元素的整数数组 `nums`，返回其所有可能的子集（幂集）。

### 思路分析

回溯：对每个元素有"选"和"不选"两种选择。或者每一层从 `start` 开始遍历，每加入一个元素就收集一次结果。

```javascript
function subsets(nums) {
  const res = [];

  function backtrack(start, path) {
    res.push([...path]);
    for (let i = start; i < nums.length; i++) {
      path.push(nums[i]);
      backtrack(i + 1, path);
      path.pop();
    }
  }

  backtrack(0, []);
  return res;
}
```

```go
func subsets(nums []int) [][]int {
    res := [][]int{}
    var backtrack func(start int, path []int)
    backtrack = func(start int, path []int) {
        tmp := make([]int, len(path))
        copy(tmp, path)
        res = append(res, tmp)
        for i := start; i < len(nums); i++ {
            path = append(path, nums[i])
            backtrack(i+1, path)
            path = path[:len(path)-1]
        }
    }
    backtrack(0, []int{})
    return res
}
```

---

## 子集 II（Subsets II）

### 题目描述

给定一个可能包含重复元素的整数数组 `nums`，返回其所有不重复的子集。

### 思路分析

先排序，回溯时同一层跳过重复元素（`i > start && nums[i] === nums[i-1]`），与组合总和 II 的去重逻辑一致。

```javascript
function subsetsWithDup(nums) {
  nums.sort((a, b) => a - b);
  const res = [];

  function backtrack(start, path) {
    res.push([...path]);
    for (let i = start; i < nums.length; i++) {
      if (i > start && nums[i] === nums[i - 1]) continue;
      path.push(nums[i]);
      backtrack(i + 1, path);
      path.pop();
    }
  }

  backtrack(0, []);
  return res;
}
```

```go
func subsetsWithDup(nums []int) [][]int {
    sort.Ints(nums)
    res := [][]int{}
    var backtrack func(start int, path []int)
    backtrack = func(start int, path []int) {
        tmp := make([]int, len(path))
        copy(tmp, path)
        res = append(res, tmp)
        for i := start; i < len(nums); i++ {
            if i > start && nums[i] == nums[i-1] {
                continue
            }
            path = append(path, nums[i])
            backtrack(i+1, path)
            path = path[:len(path)-1]
        }
    }
    backtrack(0, []int{})
    return res
}
```

---

## N 皇后（N-Queens）

### 题目描述

在 `n x n` 的棋盘上放置 `n` 个皇后，使得它们彼此不能互相攻击（同行、同列、同对角线）。返回所有不同的解。

### 思路分析

逐行放置皇后。使用三个集合分别记录已占用的列、左对角线（`row - col`）和右对角线（`row + col`）。每行尝试每一列，若不冲突则放置并递归下一行。

```javascript
function solveNQueens(n) {
  const res = [];
  const board = Array.from({ length: n }, () => '.'.repeat(n));
  const cols = new Set(), diag1 = new Set(), diag2 = new Set();

  function backtrack(row) {
    if (row === n) {
      res.push([...board]);
      return;
    }
    for (let col = 0; col < n; col++) {
      if (cols.has(col) || diag1.has(row - col) || diag2.has(row + col)) continue;
      cols.add(col);
      diag1.add(row - col);
      diag2.add(row + col);
      board[row] = board[row].substring(0, col) + 'Q' + board[row].substring(col + 1);
      backtrack(row + 1);
      board[row] = board[row].substring(0, col) + '.' + board[row].substring(col + 1);
      cols.delete(col);
      diag1.delete(row - col);
      diag2.delete(row + col);
    }
  }

  backtrack(0);
  return res;
}
```

```go
func solveNQueens(n int) [][]string {
    res := [][]string{}
    board := make([][]byte, n)
    for i := range board {
        board[i] = make([]byte, n)
        for j := range board[i] {
            board[i][j] = '.'
        }
    }
    cols := map[int]bool{}
    diag1 := map[int]bool{}
    diag2 := map[int]bool{}

    var backtrack func(row int)
    backtrack = func(row int) {
        if row == n {
            snapshot := make([]string, n)
            for i := range board {
                snapshot[i] = string(board[i])
            }
            res = append(res, snapshot)
            return
        }
        for col := 0; col < n; col++ {
            if cols[col] || diag1[row-col] || diag2[row+col] {
                continue
            }
            cols[col] = true
            diag1[row-col] = true
            diag2[row+col] = true
            board[row][col] = 'Q'
            backtrack(row + 1)
            board[row][col] = '.'
            delete(cols, col)
            delete(diag1, row-col)
            delete(diag2, row+col)
        }
    }
    backtrack(0)
    return res
}
```

---

## 括号生成（Generate Parentheses）

### 题目描述

给出 `n` 代表生成括号的对数，生成所有可能的并且有效的括号组合。

### 思路分析

回溯：维护左括号和右括号的剩余数量 `open` 和 `close`。当 `open > 0` 时可添加左括号；当 `close > open` 时可添加右括号。两者均为 0 时收集结果。

```javascript
function generateParenthesis(n) {
  const res = [];

  function backtrack(path, open, close) {
    if (path.length === 2 * n) {
      res.push(path);
      return;
    }
    if (open < n) backtrack(path + '(', open + 1, close);
    if (close < open) backtrack(path + ')', open, close + 1);
  }

  backtrack('', 0, 0);
  return res;
}
```

```go
func generateParenthesis(n int) []string {
    res := []string{}
    var backtrack func(path string, open, close int)
    backtrack = func(path string, open, close int) {
        if len(path) == 2*n {
            res = append(res, path)
            return
        }
        if open < n {
            backtrack(path+"(", open+1, close)
        }
        if close < open {
            backtrack(path+")", open, close+1)
        }
    }
    backtrack("", 0, 0)
    return res
}
```

---

## 单词搜索（Word Search）

### 题目描述

给定一个 `m x n` 二维字符网格 `board` 和一个字符串单词 `word`，判断 `word` 是否存在于网格中。单词可由相邻单元格（水平或垂直）组成，同一个单元格不能重复使用。

### 思路分析

对每个格子作为起点进行 DFS 回溯。在当前位置匹配字符后，标记已访问，向四个方向递归。若最终匹配完所有字符则返回 true，否则回退标记。

```javascript
function exist(board, word) {
  const m = board.length, n = board[0].length;
  const dirs = [[0, 1], [0, -1], [1, 0], [-1, 0]];

  function dfs(i, j, k) {
    if (k === word.length) return true;
    if (i < 0 || i >= m || j < 0 || j >= n || board[i][j] !== word[k]) return false;
    const tmp = board[i][j];
    board[i][j] = '#'; // 标记已访问
    for (const [di, dj] of dirs) {
      if (dfs(i + di, j + dj, k + 1)) return true;
    }
    board[i][j] = tmp; // 回退
    return false;
  }

  for (let i = 0; i < m; i++) {
    for (let j = 0; j < n; j++) {
      if (dfs(i, j, 0)) return true;
    }
  }
  return false;
}
```

```go
func exist(board [][]byte, word string) bool {
    m, n := len(board), len(board[0])
    dirs := [][2]int{{0, 1}, {0, -1}, {1, 0}, {-1, 0}}

    var dfs func(i, j, k int) bool
    dfs = func(i, j, k int) bool {
        if k == len(word) {
            return true
        }
        if i < 0 || i >= m || j < 0 || j >= n || board[i][j] != word[k] {
            return false
        }
        tmp := board[i][j]
        board[i][j] = '#'
        for _, d := range dirs {
            if dfs(i+d[0], j+d[1], k+1) {
                return true
            }
        }
        board[i][j] = tmp
        return false
    }

    for i := 0; i < m; i++ {
        for j := 0; j < n; j++ {
            if dfs(i, j, 0) {
                return true
            }
        }
    }
    return false
}
```

---

## 贪心算法概念

贪心算法（Greedy Algorithm）在每一步都选择当前看起来最优的方案，不进行回溯。贪心的适用条件：问题具有**贪心选择性质**（局部最优能导致全局最优）和**最优子结构**。贪心不一定总能得到全局最优解，因此需要证明其正确性。

---

## 跳跃游戏 I（Jump Game I）

### 题目描述

给定一个非负整数数组 `nums`，你最初位于第一个位置。数组中的每个元素代表你在该位置可以跳跃的最大长度。判断你是否能够到达最后一个位置。

### 思路分析

贪心：维护当前能到达的最远位置 `maxReach`。遍历每个位置 `i`，若 `i > maxReach` 则无法到达，否则更新 `maxReach = max(maxReach, i + nums[i])`。若 `maxReach >= n-1` 则可以到达。

```javascript
function canJump(nums) {
  let maxReach = 0;
  for (let i = 0; i < nums.length; i++) {
    if (i > maxReach) return false;
    maxReach = Math.max(maxReach, i + nums[i]);
    if (maxReach >= nums.length - 1) return true;
  }
  return true;
}
```

```go
func canJump(nums []int) bool {
    maxReach := 0
    for i := 0; i < len(nums); i++ {
        if i > maxReach {
            return false
        }
        if i+nums[i] > maxReach {
            maxReach = i + nums[i]
        }
        if maxReach >= len(nums)-1 {
            return true
        }
    }
    return true
}
```

---

## 跳跃游戏 II（Jump Game II）

### 题目描述

同样的设定，假设你总是可以到达最后一个位置，求到达最后位置的最少跳跃次数。

### 思路分析

贪心 BFS 思想：维护当前跳跃的边界 `end`，最远距离 `farthest`，跳跃次数 `jumps`。遍历时更新 `farthest`，到达 `end` 时必须跳跃一次并更新 `end = farthest`。

```javascript
function jump(nums) {
  let jumps = 0, end = 0, farthest = 0;
  for (let i = 0; i < nums.length - 1; i++) {
    farthest = Math.max(farthest, i + nums[i]);
    if (i === end) {
      jumps++;
      end = farthest;
      if (end >= nums.length - 1) break;
    }
  }
  return jumps;
}
```

```go
func jump(nums []int) int {
    jumps, end, farthest := 0, 0, 0
    for i := 0; i < len(nums)-1; i++ {
        if i+nums[i] > farthest {
            farthest = i + nums[i]
        }
        if i == end {
            jumps++
            end = farthest
            if end >= len(nums)-1 {
                break
            }
        }
    }
    return jumps
}
```

---

## 分发糖果（Candy）

### 题目描述

`n` 个孩子站成一排，每个孩子有一个评分。按照以下要求给孩子分配糖果：每个孩子至少 1 颗糖果；评分更高的孩子比相邻的孩子获得更多糖果。求最少需要多少颗糖果。

### 思路分析

两次遍历贪心：
1. 从左到右：若 `ratings[i] > ratings[i-1]`，则 `candy[i] = candy[i-1] + 1`。
2. 从右到左：若 `ratings[i] > ratings[i+1]`，则 `candy[i] = max(candy[i], candy[i+1] + 1)`。

两次遍历确保同时满足左右两侧的约束。

```javascript
function candy(ratings) {
  const n = ratings.length;
  const candies = new Array(n).fill(1);

  for (let i = 1; i < n; i++) {
    if (ratings[i] > ratings[i - 1]) {
      candies[i] = candies[i - 1] + 1;
    }
  }
  for (let i = n - 2; i >= 0; i--) {
    if (ratings[i] > ratings[i + 1]) {
      candies[i] = Math.max(candies[i], candies[i + 1] + 1);
    }
  }
  return candies.reduce((a, b) => a + b, 0);
}
```

```go
func candy(ratings []int) int {
    n := len(ratings)
    candies := make([]int, n)
    for i := range candies {
        candies[i] = 1
    }
    for i := 1; i < n; i++ {
        if ratings[i] > ratings[i-1] {
            candies[i] = candies[i-1] + 1
        }
    }
    for i := n - 2; i >= 0; i-- {
        if ratings[i] > ratings[i+1] && candies[i] <= candies[i+1] {
            candies[i] = candies[i+1] + 1
        }
    }
    total := 0
    for _, c := range candies {
        total += c
    }
    return total
}
```

---

## 无重叠区间（Non-overlapping Intervals）

### 题目描述

给定一个区间的集合 `intervals`，其中 `intervals[i] = [start_i, end_i]`。返回需要移除的最少区间数量，使剩余区间互不重叠。

### 思路分析

贪心：按区间结束时间排序。优先保留结束早的区间（给后续区间留更多空间）。遍历时，若当前区间起始 `< prevEnd`，则需要移除（计数+1），否则更新 `prevEnd`。

```javascript
function eraseOverlapIntervals(intervals) {
  intervals.sort((a, b) => a[1] - b[1]);
  let count = 0;
  let prevEnd = -Infinity;
  for (const [start, end] of intervals) {
    if (start < prevEnd) {
      count++;
    } else {
      prevEnd = end;
    }
  }
return count;
}
```

```go
func eraseOverlapIntervals(intervals [][]int) int {
    sort.Slice(intervals, func(i, j int) bool {
        return intervals[i][1] < intervals[j][1]
    })
    count := 0
    prevEnd := -1 << 31
    for _, interval := range intervals {
        if interval[0] < prevEnd {
            count++
        } else {
            prevEnd = interval[1]
        }
    }
    return count
}
```

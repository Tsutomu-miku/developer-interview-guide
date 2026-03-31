# 数组与字符串经典算法题

本章涵盖面试中最常见的数组与字符串类算法题，包括哈希表、双指针、滑动窗口、动态规划等核心技巧。每道题均提供详细的思路分析与 JavaScript、Go 两种语言的完整实现。

---

## 两数之和

**题目描述：** 给定一个整数数组 `nums` 和一个整数目标值 `target`，请你在该数组中找出和为目标值的那两个整数，并返回它们的数组下标。假设每种输入只会对应一个答案，且同一个元素不能重复使用。

**思路分析：** 暴力解法需要两层循环，时间复杂度 O(n²)。更优的做法是利用哈希表：遍历数组时，对于每个元素 `nums[i]`，先查看哈希表中是否已存在 `target - nums[i]`，若存在则直接返回两个下标；若不存在则将当前元素及其下标存入哈希表。这样只需一次遍历即可完成。

**时间复杂度：** O(n)，空间复杂度 O(n)。

```javascript
function twoSum(nums, target) {
  const map = new Map();
  for (let i = 0; i < nums.length; i++) {
    const complement = target - nums[i];
    if (map.has(complement)) {
      return [map.get(complement), i];
    }
    map.set(nums[i], i);
  }
  return [];
}
```

```go
func twoSum(nums []int, target int) []int {
    m := make(map[int]int)
    for i, num := range nums {
        complement := target - num
        if j, ok := m[complement]; ok {
            return []int{j, i}
        }
        m[num] = i
    }
    return nil
}
```

---

## 三数之和

**题目描述：** 给定一个包含 n 个整数的数组 `nums`，判断 `nums` 中是否存在三个元素 a、b、c，使得 a + b + c = 0。请找出所有满足条件且不重复的三元组。

**思路分析：** 先对数组排序，然后固定第一个数，对剩余部分使用双指针查找。排序后可以方便地跳过重复元素以避免结果重复。固定 `nums[i]` 后，设 `left = i + 1`，`right = n - 1`，若三数之和大于 0 则 right 左移，小于 0 则 left 右移，等于 0 则记录结果并同时移动两个指针跳过重复值。

**时间复杂度：** O(n²)，空间复杂度 O(1)（不计输出）。

```javascript
function threeSum(nums) {
  nums.sort((a, b) => a - b);
  const result = [];
  for (let i = 0; i < nums.length - 2; i++) {
    if (nums[i] > 0) break;
    if (i > 0 && nums[i] === nums[i - 1]) continue;
    let left = i + 1, right = nums.length - 1;
    while (left < right) {
      const sum = nums[i] + nums[left] + nums[right];
      if (sum === 0) {
        result.push([nums[i], nums[left], nums[right]]);
        while (left < right && nums[left] === nums[left + 1]) left++;
        while (left < right && nums[right] === nums[right - 1]) right--;
        left++;
        right--;
      } else if (sum < 0) {
        left++;
      } else {
        right--;
      }
    }
  }
  return result;
}
```

```go
func threeSum(nums []int) [][]int {
    sort.Ints(nums)
    var result [][]int
    n := len(nums)
    for i := 0; i < n-2; i++ {
        if nums[i] > 0 {
            break
        }
        if i > 0 && nums[i] == nums[i-1] {
            continue
        }
        left, right := i+1, n-1
        for left < right {
            sum := nums[i] + nums[left] + nums[right]
            if sum == 0 {
                result = append(result, []int{nums[i], nums[left], nums[right]})
                for left < right && nums[left] == nums[left+1] {
                    left++
                }
                for left < right && nums[right] == nums[right-1] {
                    right--
                }
                left++
                right--
            } else if sum < 0 {
                left++
            } else {
                right--
            }
        }
    }
    return result
}
```

---

## 最长无重复子串

**题目描述：** 给定一个字符串 `s`，请你找出其中不含有重复字符的最长子串的长度。

**思路分析：** 使用滑动窗口技巧。维护一个窗口 `[left, right)`，用哈希集合记录窗口内的字符。右指针不断向右扩展，当遇到重复字符时，左指针向右收缩直到窗口内不含重复字符。每次更新窗口大小的最大值。也可以用哈希表记录字符最后出现的位置，遇到重复时直接将 left 跳到重复字符上次出现位置的下一个。

**时间复杂度：** O(n)，空间复杂度 O(min(n, m))，m 为字符集大小。

```javascript
function lengthOfLongestSubstring(s) {
  const map = new Map();
  let maxLen = 0, left = 0;
  for (let right = 0; right < s.length; right++) {
    if (map.has(s[right]) && map.get(s[right]) >= left) {
      left = map.get(s[right]) + 1;
    }
    map.set(s[right], right);
    maxLen = Math.max(maxLen, right - left + 1);
  }
  return maxLen;
}
```

```go
func lengthOfLongestSubstring(s string) int {
    m := make(map[byte]int)
    maxLen, left := 0, 0
    for right := 0; right < len(s); right++ {
        if idx, ok := m[s[right]]; ok && idx >= left {
            left = idx + 1
        }
        m[s[right]] = right
        if right-left+1 > maxLen {
            maxLen = right - left + 1
        }
    }
    return maxLen
}
```

---

## 合并区间

**题目描述：** 以数组 `intervals` 表示若干个区间的集合，其中单个区间为 `intervals[i] = [starti, endi]`。请合并所有重叠的区间，并返回一个不重叠的区间数组。

**思路分析：** 先按区间的起始位置排序，然后遍历排序后的区间。维护一个结果数组，对于每个区间，如果它的起始位置大于结果数组中最后一个区间的结束位置，说明不重叠，直接加入结果；否则合并，更新结果数组最后一个区间的结束位置为两者结束位置的较大值。

**时间复杂度：** O(n log n)（排序），空间复杂度 O(n)。

```javascript
function merge(intervals) {
  if (intervals.length <= 1) return intervals;
  intervals.sort((a, b) => a[0] - b[0]);
  const result = [intervals[0]];
  for (let i = 1; i < intervals.length; i++) {
    const last = result[result.length - 1];
    if (intervals[i][0] <= last[1]) {
      last[1] = Math.max(last[1], intervals[i][1]);
    } else {
      result.push(intervals[i]);
    }
  }
  return result;
}
```

```go
func merge(intervals [][]int) [][]int {
    sort.Slice(intervals, func(i, j int) bool {
        return intervals[i][0] < intervals[j][0]
    })
    result := [][]int{intervals[0]}
    for i := 1; i < len(intervals); i++ {
        last := result[len(result)-1]
        if intervals[i][0] <= last[1] {
            if intervals[i][1] > last[1] {
                last[1] = intervals[i][1]
            }
        } else {
            result = append(result, intervals[i])
        }
    }
    return result
}
```

---

## 盛最多水的容器

**题目描述：** 给定 n 个非负整数 `a1, a2, ..., an`，每个数代表坐标中的一个点 `(i, ai)`。在坐标内画 n 条垂直线，找出其中的两条线，使得它们与 x 轴共同构成的容器可以容纳最多的水。

**思路分析：** 使用双指针法。初始时左指针在最左端，右指针在最右端。每次计算当前容器的面积（宽度乘以两端较矮的高度），然后移动较矮一端的指针向内收缩。因为如果移动较高一端的指针，宽度减小且高度不会增大（受限于较矮端），面积只会减小；而移动较矮端可能遇到更高的线，有机会增大面积。

**时间复杂度：** O(n)，空间复杂度 O(1)。

```javascript
function maxArea(height) {
  let left = 0, right = height.length - 1;
  let max = 0;
  while (left < right) {
    const area = Math.min(height[left], height[right]) * (right - left);
    max = Math.max(max, area);
    if (height[left] < height[right]) {
      left++;
    } else {
      right--;
    }
  }
  return max;
}
```

```go
func maxArea(height []int) int {
    left, right := 0, len(height)-1
    maxWater := 0
    for left < right {
        h := height[left]
        if height[right] < h {
            h = height[right]
        }
        area := h * (right - left)
        if area > maxWater {
            maxWater = area
        }
        if height[left] < height[right] {
            left++
        } else {
            right--
        }
    }
    return maxWater
}
```

---

## 接雨水

**题目描述：** 给定 n 个非负整数表示每个宽度为 1 的柱子的高度图，计算按此排列的柱子，下雨之后能接多少雨水。

**思路分析：**

**方法一——双指针法：** 维护左右两个指针以及左侧最大高度 `leftMax` 和右侧最大高度 `rightMax`。当 `leftMax < rightMax` 时，左侧位置能接的水由 `leftMax` 决定（因为右侧一定有更高的墙挡住），此时处理左指针位置并右移；反之处理右指针位置并左移。

**方法二——单调栈法：** 维护一个单调递减栈，栈中存储下标。遍历数组，当当前柱子高度大于栈顶对应高度时，说明栈顶元素被夹在中间可以接水。弹出栈顶，以新的栈顶为左边界、当前柱子为右边界，计算该层能接的水量。

**时间复杂度：** O(n)，空间复杂度双指针法 O(1)，单调栈法 O(n)。

```javascript
// 双指针法
function trap(height) {
  let left = 0, right = height.length - 1;
  let leftMax = 0, rightMax = 0, water = 0;
  while (left < right) {
    if (height[left] < height[right]) {
      if (height[left] >= leftMax) {
        leftMax = height[left];
      } else {
        water += leftMax - height[left];
      }
      left++;
    } else {
      if (height[right] >= rightMax) {
        rightMax = height[right];
      } else {
        water += rightMax - height[right];
      }
      right--;
    }
  }
  return water;
}

// 单调栈法
function trapStack(height) {
  const stack = [];
  let water = 0;
  for (let i = 0; i < height.length; i++) {
    while (stack.length > 0 && height[i] > height[stack[stack.length - 1]]) {
      const top = stack.pop();
      if (stack.length === 0) break;
      const left = stack[stack.length - 1];
      const w = i - left - 1;
      const h = Math.min(height[i], height[left]) - height[top];
      water += w * h;
    }
    stack.push(i);
  }
  return water;
}
```

```go
// 双指针法
func trap(height []int) int {
    left, right := 0, len(height)-1
    leftMax, rightMax, water := 0, 0, 0
    for left < right {
        if height[left] < height[right] {
            if height[left] >= leftMax {
                leftMax = height[left]
            } else {
                water += leftMax - height[left]
            }
            left++
        } else {
            if height[right] >= rightMax {
                rightMax = height[right]
            } else {
                water += rightMax - height[right]
            }
            right--
        }
    }
    return water
}

// 单调栈法
func trapStack(height []int) int {
    stack := []int{}
    water := 0
    for i := 0; i < len(height); i++ {
        for len(stack) > 0 && height[i] > height[stack[len(stack)-1]] {
            top := stack[len(stack)-1]
            stack = stack[:len(stack)-1]
            if len(stack) == 0 {
                break
            }
            leftIdx := stack[len(stack)-1]
            w := i - leftIdx - 1
            h := min(height[i], height[leftIdx]) - height[top]
            water += w * h
        }
        stack = append(stack, i)
    }
    return water
}

func min(a, b int) int {
    if a < b {
        return a
    }
    return b
}
```

---

## 字符串反转与回文判断

**题目描述：**
1. **反转字符串：** 编写一个函数，将输入的字符串反转过来。要求原地修改字符数组，使用 O(1) 的额外空间。
2. **回文判断：** 给定一个字符串，判断它是否是回文串，只考虑字母和数字字符，可以忽略大小写。

**思路分析：** 反转字符串使用双指针，分别从首尾向中间靠拢并交换字符。回文判断同样使用双指针，从两端向中间移动，跳过非字母数字字符，比较对应字符是否相同（忽略大小写）。

**时间复杂度：** O(n)，空间复杂度 O(1)。

```javascript
// 反转字符串
function reverseString(s) {
  let left = 0, right = s.length - 1;
  while (left < right) {
    [s[left], s[right]] = [s[right], s[left]];
    left++;
    right--;
  }
}

// 回文判断
function isPalindrome(s) {
  let left = 0, right = s.length - 1;
  while (left < right) {
    while (left < right && !isAlphanumeric(s[left])) left++;
    while (left < right && !isAlphanumeric(s[right])) right--;
    if (s[left].toLowerCase() !== s[right].toLowerCase()) return false;
    left++;
    right--;
  }
  return true;
}

function isAlphanumeric(c) {
  return /[a-zA-Z0-9]/.test(c);
}
```

```go
// 反转字符串
func reverseString(s []byte) {
    left, right := 0, len(s)-1
    for left < right {
        s[left], s[right] = s[right], s[left]
        left++
        right--
    }
}

// 回文判断
func isPalindrome(s string) bool {
    left, right := 0, len(s)-1
    for left < right {
        for left < right && !isAlphanumeric(s[left]) {
            left++
        }
        for left < right && !isAlphanumeric(s[right]) {
            right--
        }
        if toLower(s[left]) != toLower(s[right]) {
            return false
        }
        left++
        right--
    }
    return true
}

func isAlphanumeric(c byte) bool {
    return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9')
}

func toLower(c byte) byte {
    if c >= 'A' && c <= 'Z' {
        return c + 32
    }
    return c
}
```

---

## 最长回文子串

**题目描述：** 给你一个字符串 `s`，找到 `s` 中最长的回文子串。

**思路分析：**

**方法一——中心扩展法：** 回文串一定以某个字符或两个字符之间的间隙为中心向两端对称扩展。遍历每个可能的中心（共 2n-1 个），从中心向两端扩展，记录最长回文子串。

**方法二——动态规划：** 定义 `dp[i][j]` 表示 `s[i..j]` 是否为回文。若 `s[i] == s[j]` 且 `dp[i+1][j-1]` 为真（或 `j - i < 3`），则 `dp[i][j]` 为真。从短子串开始填表，记录最长回文的起始位置和长度。

**时间复杂度：** 两种方法均为 O(n²)，中心扩展法空间 O(1)，DP 法空间 O(n²)。

```javascript
// 中心扩展法
function longestPalindrome(s) {
  if (s.length < 2) return s;
  let start = 0, maxLen = 1;

  function expandAroundCenter(left, right) {
    while (left >= 0 && right < s.length && s[left] === s[right]) {
      if (right - left + 1 > maxLen) {
        start = left;
        maxLen = right - left + 1;
      }
      left--;
      right++;
    }
  }

  for (let i = 0; i < s.length; i++) {
    expandAroundCenter(i, i);     // 奇数长度
    expandAroundCenter(i, i + 1); // 偶数长度
  }
  return s.substring(start, start + maxLen);
}
```

```go
func longestPalindrome(s string) string {
    if len(s) < 2 {
        return s
    }
    start, maxLen := 0, 1

    expand := func(left, right int) {
        for left >= 0 && right < len(s) && s[left] == s[right] {
            if right-left+1 > maxLen {
                start = left
                maxLen = right - left + 1
            }
            left--
            right++
        }
    }

    for i := 0; i < len(s); i++ {
        expand(i, i)   // 奇数长度
        expand(i, i+1) // 偶数长度
    }
    return s[start : start+maxLen]
}
```

---

## 字符串匹配（KMP 算法）

**题目描述：** 实现 `strStr()` 函数——给你两个字符串 `haystack` 和 `needle`，请在 `haystack` 字符串中找出 `needle` 字符串的第一个匹配项的下标。如果不存在返回 -1。

**思路分析：** KMP 算法通过预处理模式串构建「部分匹配表」（next 数组 / 前缀函数），避免在匹配失败时从头开始比较。next 数组 `next[i]` 表示 `needle[0..i]` 中最长的相等前后缀长度。匹配时，当字符不匹配时，利用 next 数组跳过已知匹配的前缀部分，从而将整体匹配时间降至线性。

**时间复杂度：** O(n + m)，n 为 haystack 长度，m 为 needle 长度。空间复杂度 O(m)。

```javascript
function strStr(haystack, needle) {
  if (needle.length === 0) return 0;
  const next = buildNext(needle);
  let j = 0;
  for (let i = 0; i < haystack.length; i++) {
    while (j > 0 && haystack[i] !== needle[j]) {
      j = next[j - 1];
    }
    if (haystack[i] === needle[j]) {
      j++;
    }
    if (j === needle.length) {
      return i - needle.length + 1;
    }
  }
  return -1;
}

function buildNext(pattern) {
  const next = new Array(pattern.length).fill(0);
  let len = 0, i = 1;
  while (i < pattern.length) {
    if (pattern[i] === pattern[len]) {
      len++;
      next[i] = len;
      i++;
    } else {
      if (len > 0) {
        len = next[len - 1];
      } else {
        next[i] = 0;
        i++;
      }
    }
  }
  return next;
}
```

```go
func strStr(haystack string, needle string) int {
    if len(needle) == 0 {
        return 0
    }
    next := buildNext(needle)
    j := 0
    for i := 0; i < len(haystack); i++ {
        for j > 0 && haystack[i] != needle[j] {
            j = next[j-1]
        }
        if haystack[i] == needle[j] {
            j++
        }
        if j == len(needle) {
            return i - len(needle) + 1
        }
    }
    return -1
}

func buildNext(pattern string) []int {
    next := make([]int, len(pattern))
    length, i := 0, 1
    for i < len(pattern) {
        if pattern[i] == pattern[length] {
            length++
            next[i] = length
            i++
        } else {
            if length > 0 {
                length = next[length-1]
            } else {
                next[i] = 0
                i++
            }
        }
    }
    return next
}
```

---

## 螺旋矩阵

**题目描述：** 给你一个 `m x n` 的矩阵 `matrix`，请按照顺时针螺旋顺序，返回矩阵中的所有元素。

**思路分析：** 定义四个边界：`top`、`bottom`、`left`、`right`，按照「右 → 下 → 左 → 上」的顺序依次遍历矩阵的外圈，每遍历完一条边就收缩对应的边界。当上下边界交叉或左右边界交叉时停止。注意在向左和向上遍历前需要检查边界是否仍然有效，避免重复遍历。

**时间复杂度：** O(m × n)，空间复杂度 O(1)（不计输出）。

```javascript
function spiralOrder(matrix) {
  const result = [];
  if (matrix.length === 0) return result;
  let top = 0, bottom = matrix.length - 1;
  let left = 0, right = matrix[0].length - 1;

  while (top <= bottom && left <= right) {
    // 向右
    for (let i = left; i <= right; i++) {
      result.push(matrix[top][i]);
    }
    top++;
    // 向下
    for (let i = top; i <= bottom; i++) {
      result.push(matrix[i][right]);
    }
    right--;
    // 向左
    if (top <= bottom) {
      for (let i = right; i >= left; i--) {
        result.push(matrix[bottom][i]);
      }
      bottom--;
    }
    // 向上
    if (left <= right) {
      for (let i = bottom; i >= top; i--) {
        result.push(matrix[i][left]);
      }
      left++;
    }
  }
  return result;
}
```

```go
func spiralOrder(matrix [][]int) []int {
    var result []int
    if len(matrix) == 0 {
        return result
    }
    top, bottom := 0, len(matrix)-1
    left, right := 0, len(matrix[0])-1

    for top <= bottom && left <= right {
        // 向右
        for i := left; i <= right; i++ {
            result = append(result, matrix[top][i])
        }
        top++
        // 向下
        for i := top; i <= bottom; i++ {
            result = append(result, matrix[i][right])
        }
        right--
        // 向左
        if top <= bottom {
            for i := right; i >= left; i-- {
                result = append(result, matrix[bottom][i])
            }
            bottom--
        }
        // 向上
        if left <= right {
            for i := bottom; i >= top; i-- {
                result = append(result, matrix[i][left])
            }
            left++
        }
    }
    return result
}
```

---

## 总结

| 题目 | 核心技巧 | 时间复杂度 |
|------|----------|-----------|
| 两数之和 | 哈希表 | O(n) |
| 三数之和 | 排序 + 双指针 | O(n²) |
| 最长无重复子串 | 滑动窗口 | O(n) |
| 合并区间 | 排序 + 线性扫描 | O(n log n) |
| 盛最多水的容器 | 双指针 | O(n) |
| 接雨水 | 双指针 / 单调栈 | O(n) |
| 字符串反转/回文 | 双指针 | O(n) |
| 最长回文子串 | 中心扩展 / DP | O(n²) |
| KMP 字符串匹配 | 前缀函数 | O(n + m) |
| 螺旋矩阵 | 边界模拟 | O(m × n) |

掌握数组与字符串问题的关键在于熟练运用**哈希表**加速查找、**双指针**压缩搜索空间、**滑动窗口**处理子串/子数组问题，以及针对特定问题选择合适的数据结构（如单调栈）。这些技巧是面试中最高频考察的知识点。
# 排序与搜索算法

排序和搜索是计算机科学的基础，也是面试中的高频考点。本章涵盖八大经典排序算法及其复杂度对比，以及二分查找的多种变体和高级搜索问题。

---

## 八大排序算法

### 冒泡排序（Bubble Sort）

反复遍历数组，比较相邻元素并交换。每轮将最大元素"冒泡"到末尾。

- **时间复杂度**：平均 O(n²)，最好 O(n)（已有序时提前终止），最坏 O(n²)
- **空间复杂度**：O(1)
- **稳定性**：稳定

```javascript
function bubbleSort(arr) {
  const n = arr.length;
  for (let i = 0; i < n - 1; i++) {
    let swapped = false;
    for (let j = 0; j < n - 1 - i; j++) {
      if (arr[j] > arr[j + 1]) {
        [arr[j], arr[j + 1]] = [arr[j + 1], arr[j]];
        swapped = true;
      }
    }
    if (!swapped) break;
  }
  return arr;
}
```

```go
func bubbleSort(arr []int) []int {
    n := len(arr)
    for i := 0; i < n-1; i++ {
        swapped := false
        for j := 0; j < n-1-i; j++ {
            if arr[j] > arr[j+1] {
                arr[j], arr[j+1] = arr[j+1], arr[j]
                swapped = true
            }
        }
        if !swapped {
            break
        }
    }
    return arr
}
```

### 选择排序（Selection Sort）

每轮从未排序部分选出最小元素，放到已排序部分末尾。

- **时间复杂度**：O(n²)（所有情况）
- **空间复杂度**：O(1)
- **稳定性**：不稳定

```javascript
function selectionSort(arr) {
  const n = arr.length;
  for (let i = 0; i < n - 1; i++) {
    let minIdx = i;
    for (let j = i + 1; j < n; j++) {
      if (arr[j] < arr[minIdx]) minIdx = j;
    }
    if (minIdx !== i) [arr[i], arr[minIdx]] = [arr[minIdx], arr[i]];
  }
  return arr;
}
```

```go
func selectionSort(arr []int) []int {
    n := len(arr)
    for i := 0; i < n-1; i++ {
        minIdx := i
        for j := i + 1; j < n; j++ {
            if arr[j] < arr[minIdx] {
                minIdx = j
            }
        }
        if minIdx != i {
            arr[i], arr[minIdx] = arr[minIdx], arr[i]
        }
    }
    return arr
}
```

### 插入排序（Insertion Sort）

将每个元素插入到前面已排序部分的正确位置，类似扑克牌整理。

- **时间复杂度**：平均 O(n²)，最好 O(n)，最坏 O(n²)
- **空间复杂度**：O(1)
- **稳定性**：稳定

```javascript
function insertionSort(arr) {
  for (let i = 1; i < arr.length; i++) {
    const key = arr[i];
    let j = i - 1;
    while (j >= 0 && arr[j] > key) {
      arr[j + 1] = arr[j];
      j--;
    }
    arr[j + 1] = key;
  }
  return arr;
}
```

```go
func insertionSort(arr []int) []int {
    for i := 1; i < len(arr); i++ {
        key := arr[i]
        j := i - 1
        for j >= 0 && arr[j] > key {
            arr[j+1] = arr[j]
            j--
        }
        arr[j+1] = key
    }
    return arr
}
```

### 归并排序（Merge Sort）

分治法：将数组不断对半分割直到单个元素，再两两合并为有序数组。

- **时间复杂度**：O(n log n)（所有情况）
- **空间复杂度**：O(n)
- **稳定性**：稳定

```javascript
function mergeSort(arr) {
  if (arr.length <= 1) return arr;
  const mid = arr.length >> 1;
  const left = mergeSort(arr.slice(0, mid));
  const right = mergeSort(arr.slice(mid));
  return merge(left, right);
}

function merge(l, r) {
  const res = [];
  let i = 0, j = 0;
  while (i < l.length && j < r.length) {
    if (l[i] <= r[j]) res.push(l[i++]);
    else res.push(r[j++]);
  }
  return res.concat(l.slice(i), r.slice(j));
}
```

```go
func mergeSort(arr []int) []int {
    if len(arr) <= 1 {
        return arr
    }
    mid := len(arr) / 2
    left := mergeSort(arr[:mid])
    right := mergeSort(arr[mid:])
    return mergeTwoSlices(left, right)
}

func mergeTwoSlices(l, r []int) []int {
    res := make([]int, 0, len(l)+len(r))
    i, j := 0, 0
    for i < len(l) && j < len(r) {
        if l[i] <= r[j] {
            res = append(res, l[i])
            i++
        } else {
            res = append(res, r[j])
            j++
        }
    }
    res = append(res, l[i:]...)
    res = append(res, r[j:]...)
    return res
}
```

### 快速排序（Quick Sort）

分治法：选定基准值（pivot），将小于 pivot 的放左边，大于的放右边，递归排序两侧。

- **时间复杂度**：平均 O(n log n)，最坏 O(n²)（已有序时取首元素作 pivot）
- **空间复杂度**：O(log n)（递归栈）
- **稳定性**：不稳定

```javascript
function quickSort(arr, lo = 0, hi = arr.length - 1) {
  if (lo >= hi) return arr;
  const pivot = arr[lo + ((hi - lo) >> 1)];
  let i = lo, j = hi;
  while (i <= j) {
    while (arr[i] < pivot) i++;
    while (arr[j] > pivot) j--;
    if (i <= j) {
      [arr[i], arr[j]] = [arr[j], arr[i]];
      i++;
      j--;
    }
  }
  quickSort(arr, lo, j);
  quickSort(arr, i, hi);
  return arr;
}
```

```go
func quickSort(arr []int, lo, hi int) {
    if lo >= hi {
        return
    }
    pivot := arr[lo+(hi-lo)/2]
    i, j := lo, hi
    for i <= j {
        for arr[i] < pivot {
            i++
        }
        for arr[j] > pivot {
            j--
        }
        if i <= j {
            arr[i], arr[j] = arr[j], arr[i]
            i++
            j--
        }
    }
    quickSort(arr, lo, j)
    quickSort(arr, i, hi)
}
```

### 堆排序（Heap Sort）

利用最大堆的性质：建堆后反复将堆顶（最大值）与末尾交换，缩小堆范围并调整。

- **时间复杂度**：O(n log n)（所有情况）
- **空间复杂度**：O(1)（原地排序）
- **稳定性**：不稳定

```javascript
function heapSort(arr) {
  const n = arr.length;

  function siftDown(i, size) {
    let largest = i;
    const l = 2 * i + 1, r = 2 * i + 2;
    if (l < size && arr[l] > arr[largest]) largest = l;
    if (r < size && arr[r] > arr[largest]) largest = r;
    if (largest !== i) {
      [arr[i], arr[largest]] = [arr[largest], arr[i]];
      siftDown(largest, size);
    }
  }

  // 建堆
  for (let i = (n >> 1) - 1; i >= 0; i--) siftDown(i, n);
  // 排序
  for (let i = n - 1; i > 0; i--) {
    [arr[0], arr[i]] = [arr[i], arr[0]];
    siftDown(0, i);
  }
  return arr;
}
```

```go
func heapSort(arr []int) {
    n := len(arr)

    var siftDown func(i, size int)
    siftDown = func(i, size int) {
        largest := i
        l, r := 2*i+1, 2*i+2
        if l < size && arr[l] > arr[largest] {
            largest = l
        }
        if r < size && arr[r] > arr[largest] {
            largest = r
        }
        if largest != i {
            arr[i], arr[largest] = arr[largest], arr[i]
            siftDown(largest, size)
        }
    }

    for i := n/2 - 1; i >= 0; i-- {
        siftDown(i, n)
    }
    for i := n - 1; i > 0; i-- {
        arr[0], arr[i] = arr[i], arr[0]
        siftDown(0, i)
    }
}
```

### 计数排序（Counting Sort）

适用于整数且范围有限的场景。统计每个值的出现次数，再按序输出。

- **时间复杂度**：O(n + k)，k 为值域范围
- **空间复杂度**：O(k)
- **稳定性**：稳定

```javascript
function countingSort(arr) {
  if (arr.length === 0) return arr;
  const minVal = Math.min(...arr);
  const maxVal = Math.max(...arr);
  const count = new Array(maxVal - minVal + 1).fill(0);
  for (const v of arr) count[v - minVal]++;
  let idx = 0;
  for (let i = 0; i < count.length; i++) {
    while (count[i]-- > 0) arr[idx++] = i + minVal;
  }
  return arr;
}
```

```go
func countingSort(arr []int) []int {
    if len(arr) == 0 {
        return arr
    }
    minVal, maxVal := arr[0], arr[0]
    for _, v := range arr {
        if v < minVal {
            minVal = v
        }
        if v > maxVal {
            maxVal = v
        }
    }
    count := make([]int, maxVal-minVal+1)
    for _, v := range arr {
        count[v-minVal]++
    }
    idx := 0
    for i, c := range count {
        for c > 0 {
            arr[idx] = i + minVal
            idx++
            c--
        }
    }
    return arr
}
```

### 基数排序（Radix Sort）

按位排序（从最低位到最高位），每一位使用计数排序。适用于非负整数。

- **时间复杂度**：O(d*(n+k))，d 为最大位数，k 为基数（通常取 10）
- **空间复杂度**：O(n + k)
- **稳定性**：稳定

```javascript
function radixSort(arr) {
  if (arr.length === 0) return arr;
  let maxVal = Math.max(...arr);
  for (let exp = 1; maxVal / exp >= 1; exp *= 10) {
    const output = new Array(arr.length);
    const count = new Array(10).fill(0);
    for (const v of arr) count[Math.floor(v / exp) % 10]++;
    for (let i = 1; i < 10; i++) count[i] += count[i - 1];
    for (let i = arr.length - 1; i >= 0; i--) {
      const d = Math.floor(arr[i] / exp) % 10;
      output[count[d] - 1] = arr[i];
      count[d]--;
    }
    for (let i = 0; i < arr.length; i++) arr[i] = output[i];
  }
  return arr;
}
```

```go
func radixSort(arr []int) []int {
    if len(arr) == 0 {
        return arr
    }
    maxVal := arr[0]
    for _, v := range arr {
        if v > maxVal {
            maxVal = v
        }
    }
    for exp := 1; maxVal/exp >= 1; exp *= 10 {
        output := make([]int, len(arr))
        count := make([]int, 10)
        for _, v := range arr {
            count[(v/exp)%10]++
        }
        for i := 1; i < 10; i++ {
            count[i] += count[i-1]
        }
        for i := len(arr) - 1; i >= 0; i-- {
            d := (arr[i] / exp) % 10
            output[count[d]-1] = arr[i]
            count[d]--
        }
        copy(arr, output)
    }
    return arr
}
```

---

## 排序算法复杂度对比

| 算法 | 平均时间 | 最好时间 | 最坏时间 | 空间 | 稳定性 |
|------|---------|---------|---------|------|--------|
| 冒泡排序 | O(n²) | O(n) | O(n²) | O(1) | 稳定 |
| 选择排序 | O(n²) | O(n²) | O(n²) | O(1) | 不稳定 |
| 插入排序 | O(n²) | O(n) | O(n²) | O(1) | 稳定 |
| 归并排序 | O(n log n) | O(n log n) | O(n log n) | O(n) | 稳定 |
| 快速排序 | O(n log n) | O(n log n) | O(n²) | O(log n) | 不稳定 |
| 堆排序 | O(n log n) | O(n log n) | O(n log n) | O(1) | 不稳定 |
| 计数排序 | O(n+k) | O(n+k) | O(n+k) | O(k) | 稳定 |
| 基数排序 | O(d(n+k)) | O(d(n+k)) | O(d(n+k)) | O(n+k) | 稳定 |

---

## 二分查找（Binary Search）

### 基本二分查找

在**有序数组**中查找目标值。

```javascript
function binarySearch(nums, target) {
  let lo = 0, hi = nums.length - 1;
  while (lo <= hi) {
    const mid = lo + ((hi - lo) >> 1);
    if (nums[mid] === target) return mid;
    else if (nums[mid] < target) lo = mid + 1;
    else hi = mid - 1;
  }
  return -1;
}
```

```go
func binarySearch(nums []int, target int) int {
    lo, hi := 0, len(nums)-1
    for lo <= hi {
        mid := lo + (hi-lo)/2
        if nums[mid] == target {
            return mid
        } else if nums[mid] < target {
            lo = mid + 1
        } else {
            hi = mid - 1
        }
    }
    return -1
}
```

### 查找左边界（第一个等于 target 的位置）

```javascript
function lowerBound(nums, target) {
  let lo = 0, hi = nums.length;
  while (lo < hi) {
    const mid = lo + ((hi - lo) >> 1);
    if (nums[mid] < target) lo = mid + 1;
    else hi = mid;
  }
  return lo;
}
```

```go
func lowerBound(nums []int, target int) int {
    lo, hi := 0, len(nums)
    for lo < hi {
        mid := lo + (hi-lo)/2
        if nums[mid] < target {
            lo = mid + 1
        } else {
            hi = mid
        }
    }
    return lo
}
```

### 查找右边界（最后一个等于 target 的位置）

```javascript
function upperBound(nums, target) {
  let lo = 0, hi = nums.length;
  while (lo < hi) {
    const mid = lo + ((hi - lo) >> 1);
    if (nums[mid] <= target) lo = mid + 1;
    else hi = mid;
  }
  return lo - 1;
}
```

```go
func upperBound(nums []int, target int) int {
    lo, hi := 0, len(nums)
    for lo < hi {
        mid := lo + (hi-lo)/2
        if nums[mid] <= target {
            lo = mid + 1
        } else {
            hi = mid
        }
    }
    return lo - 1
}
```

---

## 搜索旋转排序数组（Search in Rotated Sorted Array）

### 题目描述

整数数组 `nums` 按升序排列后在某个点旋转（如 `[4,5,6,7,0,1,2]`），给定一个目标值 `target`，若存在则返回索引，否则返回 -1。要求时间复杂度 O(log n)。

### 思路分析

二分查找时，`[lo, mid]` 或 `[mid, hi]` 中至少有一半是有序的。先判断哪一半有序，再决定 target 在有序半边还是另一半。

```javascript
function search(nums, target) {
  let lo = 0, hi = nums.length - 1;
  while (lo <= hi) {
    const mid = lo + ((hi - lo) >> 1);
    if (nums[mid] === target) return mid;
    if (nums[lo] <= nums[mid]) {
      // 左半有序
      if (nums[lo] <= target && target < nums[mid]) hi = mid - 1;
      else lo = mid + 1;
    } else {
      // 右半有序
      if (nums[mid] < target && target <= nums[hi]) lo = mid + 1;
      else hi = mid - 1;
    }
  }
  return -1;
}
```

```go
func search(nums []int, target int) int {
    lo, hi := 0, len(nums)-1
    for lo <= hi {
        mid := lo + (hi-lo)/2
        if nums[mid] == target {
            return mid
        }
        if nums[lo] <= nums[mid] {
            if nums[lo] <= target && target < nums[mid] {
                hi = mid - 1
            } else {
                lo = mid + 1
            }
        } else {
            if nums[mid] < target && target <= nums[hi] {
                lo = mid + 1
            } else {
                hi = mid - 1
            }
        }
    }
    return -1
}
```

---

## 寻找两个正序数组的中位数（Median of Two Sorted Arrays）

### 题目描述

给定两个大小分别为 `m` 和 `n` 的正序数组 `nums1` 和 `nums2`，返回这两个数组的中位数。要求时间复杂度 O(log(m+n))。

### 思路分析

对较短数组进行二分查找。将两数组各自分成左右两部分，满足 `maxLeftA <= minRightB` 且 `maxLeftB <= minRightA` 时即找到了正确的分割点。

```javascript
function findMedianSortedArrays(nums1, nums2) {
  if (nums1.length > nums2.length) return findMedianSortedArrays(nums2, nums1);
  const m = nums1.length, n = nums2.length;
  let lo = 0, hi = m;
  while (lo <= hi) {
    const i = (lo + hi) >> 1;
    const j = ((m + n + 1) >> 1) - i;
    const maxLeftA = i === 0 ? -Infinity : nums1[i - 1];
    const minRightA = i === m ? Infinity : nums1[i];
    const maxLeftB = j === 0 ? -Infinity : nums2[j - 1];
    const minRightB = j === n ? Infinity : nums2[j];
    if (maxLeftA <= minRightB && maxLeftB <= minRightA) {
      if ((m + n) % 2 === 1) return Math.max(maxLeftA, maxLeftB);
      return (Math.max(maxLeftA, maxLeftB) + Math.min(minRightA, minRightB)) / 2;
    } else if (maxLeftA > minRightB) {
      hi = i - 1;
    } else {
      lo = i + 1;
    }
  }
  return 0;
}
```

```go
func findMedianSortedArrays(nums1 []int, nums2 []int) float64 {
    if len(nums1) > len(nums2) {
        return findMedianSortedArrays(nums2, nums1)
    }
    m, n := len(nums1), len(nums2)
    lo, hi := 0, m
    for lo <= hi {
        i := (lo + hi) / 2
        j := (m+n+1)/2 - i
        maxLeftA := -1 << 31
        if i > 0 {
            maxLeftA = nums1[i-1]
        }
        minRightA := 1<<31 - 1
        if i < m {
            minRightA = nums1[i]
        }
        maxLeftB := -1 << 31
        if j > 0 {
            maxLeftB = nums2[j-1]
        }
        minRightB := 1<<31 - 1
        if j < n {
            minRightB = nums2[j]
        }
        if maxLeftA <= minRightB && maxLeftB <= minRightA {
            if (m+n)%2 == 1 {
                return float64(max(maxLeftA, maxLeftB))
            }
            return float64(max(maxLeftA, maxLeftB)+min(minRightA, minRightB)) / 2.0
        } else if maxLeftA > minRightB {
            hi = i - 1
        } else {
            lo = i + 1
        }
    }
    return 0.0
}
```

---

## 前 K 个高频元素（Top K Frequent Elements）

### 题目描述

给定一个整数数组 `nums` 和一个整数 `k`，返回出现频率前 `k` 高的元素。

### 思路分析

**方法一：小顶堆**。用哈希表统计频率，维护大小为 `k` 的小顶堆，遍历所有频率，堆满后若当前频率大于堆顶则替换。时间 O(n log k)。

**方法二：桶排序**。频率范围为 `[1, n]`，创建 `n+1` 个桶，将元素按频率放入对应桶中，从高频桶向低频桶收集 `k` 个元素。时间 O(n)。

```javascript
// 桶排序法 O(n)
function topKFrequent(nums, k) {
  const freqMap = new Map();
  for (const n of nums) freqMap.set(n, (freqMap.get(n) || 0) + 1);

  const buckets = new Array(nums.length + 1).fill(null).map(() => []);
  for (const [num, freq] of freqMap) {
    buckets[freq].push(num);
  }

  const res = [];
  for (let i = buckets.length - 1; i >= 0 && res.length < k; i--) {
    for (const num of buckets[i]) {
      res.push(num);
      if (res.length === k) return res;
    }
  }
  return res;
}
```

```go
func topKFrequent(nums []int, k int) []int {
    freqMap := make(map[int]int)
    for _, v := range nums {
        freqMap[v]++
    }
    buckets := make([][]int, len(nums)+1)
    for num, freq := range freqMap {
        buckets[freq] = append(buckets[freq], num)
    }
    res := []int{}
    for i := len(buckets) - 1; i >= 0 && len(res) < k; i-- {
        for _, num := range buckets[i] {
            res = append(res, num)
            if len(res) == k {
                return res
            }
        }
    }
    return res
}
```

---

## 数组中的第 K 个最大元素（Kth Largest Element）

### 题目描述

在未排序的数组中找到第 `k` 个最大的元素。

### 思路分析

**快速选择算法（Quick Select）**：基于快速排序的 partition，每次只递归一侧，平均时间 O(n)，最坏 O(n²)。随机选择 pivot 可优化期望复杂度。

```javascript
function findKthLargest(nums, k) {
  const target = nums.length - k; // 转换为第 target 小

  function quickSelect(lo, hi) {
    const pivotIdx = lo + Math.floor(Math.random() * (hi - lo + 1));
    [nums[pivotIdx], nums[hi]] = [nums[hi], nums[pivotIdx]];
    const pivot = nums[hi];
    let store = lo;
    for (let i = lo; i < hi; i++) {
      if (nums[i] < pivot) {
        [nums[i], nums[store]] = [nums[store], nums[i]];
        store++;
      }
    }
    [nums[store], nums[hi]] = [nums[hi], nums[store]];

    if (store === target) return nums[store];
    else if (store < target) return quickSelect(store + 1, hi);
    else return quickSelect(lo, store - 1);
  }

  return quickSelect(0, nums.length - 1);
}
```

```go
func findKthLargest(nums []int, k int) int {
    target := len(nums) - k
    rand.Seed(time.Now().UnixNano())

    var quickSelect func(lo, hi int) int
    quickSelect = func(lo, hi int) int {
        pivotIdx := lo + rand.Intn(hi-lo+1)
        nums[pivotIdx], nums[hi] = nums[hi], nums[pivotIdx]
        pivot := nums[hi]
        store := lo
        for i := lo; i < hi; i++ {
            if nums[i] < pivot {
                nums[i], nums[store] = nums[store], nums[i]
                store++
            }
        }
        nums[store], nums[hi] = nums[hi], nums[store]

        if store == target {
            return nums[store]
        } else if store < target {
            return quickSelect(store+1, hi)
        }
        return quickSelect(lo, store-1)
    }

    return quickSelect(0, len(nums)-1)
}
```

---

## 合并两个有序数组（Merge Sorted Array）

### 题目描述

给定两个按非递减顺序排列的整数数组 `nums1` 和 `nums2`，以及 `nums1` 和 `nums2` 的元素数量 `m` 和 `n`。将 `nums2` 合并到 `nums1` 中，使其按非递减顺序排列。`nums1` 的长度为 `m + n`。

### 思路分析

**逆向双指针**：从 `nums1` 和 `nums2` 的末尾开始比较，将较大的放在 `nums1` 的末尾位置。这样不需要额外空间，且不会覆盖未处理的元素。时间 O(m+n)，空间 O(1)。

```javascript
function merge(nums1, m, nums2, n) {
  let p1 = m - 1, p2 = n - 1, p = m + n - 1;
  while (p1 >= 0 && p2 >= 0) {
    if (nums1[p1] > nums2[p2]) {
      nums1[p--] = nums1[p1--];
    } else {
      nums1[p--] = nums2[p2--];
    }
  }
  while (p2 >= 0) {
    nums1[p--] = nums2[p2--];
  }
}
```

```go
func merge(nums1 []int, m int, nums2 []int, n int) {
    p1, p2, p := m-1, n-1, m+n-1
    for p1 >= 0 && p2 >= 0 {
        if nums1[p1] > nums2[p2] {
            nums1[p] = nums1[p1]
            p1--
        } else {
            nums1[p] = nums2[p2]
            p2--
        }
        p--
    }
    for p2 >= 0 {
        nums1[p] = nums2[p2]
        p2--
        p--
    }
}
```

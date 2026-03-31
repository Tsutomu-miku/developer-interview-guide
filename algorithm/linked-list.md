# 链表经典算法题

链表是面试中的高频考点，重点考查指针操作、边界处理和经典技巧（快慢指针、虚拟头节点等）。本章覆盖链表领域最常见的面试题，每道题均给出 JavaScript 和 Go 两种语言的完整实现。

---

## 反转链表

**题目描述：** 给你单链表的头节点 `head`，请你反转链表，并返回反转后的链表头节点。

**思路分析：**

**迭代法：** 维护三个指针 `prev`、`curr`、`next`。遍历链表，每次先保存 `curr.next`，然后将 `curr.next` 指向 `prev`，再将 `prev` 和 `curr` 各前进一步。遍历结束后 `prev` 即为新的头节点。

**递归法：** 递归地反转从第二个节点开始的子链表，然后将当前节点接到反转后子链表的尾部。递归的 base case 是链表为空或只有一个节点。

**时间复杂度：** O(n)，空间复杂度迭代 O(1)，递归 O(n)。

```javascript
// 迭代法
function reverseList(head) {
  let prev = null, curr = head;
  while (curr !== null) {
    const next = curr.next;
    curr.next = prev;
    prev = curr;
    curr = next;
  }
  return prev;
}

// 递归法
function reverseListRecursive(head) {
  if (head === null || head.next === null) return head;
  const newHead = reverseListRecursive(head.next);
  head.next.next = head;
  head.next = null;
  return newHead;
}
```

```go
// 迭代法
func reverseList(head *ListNode) *ListNode {
    var prev *ListNode
    curr := head
    for curr != nil {
        next := curr.Next
        curr.Next = prev
        prev = curr
        curr = next
    }
    return prev
}

// 递归法
func reverseListRecursive(head *ListNode) *ListNode {
    if head == nil || head.Next == nil {
        return head
    }
    newHead := reverseListRecursive(head.Next)
    head.Next.Next = head
    head.Next = nil
    return newHead
}
```

---

## 合并两个有序链表

**题目描述：** 将两个升序链表合并为一个新的升序链表并返回。新链表是通过拼接给定的两个链表的所有节点组成的。

**思路分析：** 使用虚拟头节点 `dummy` 简化边界处理。维护一个当前指针 `curr`，每次比较两个链表当前节点的值，将较小的节点接到 `curr` 后面，然后移动对应链表的指针。当其中一个链表遍历完后，将另一个链表的剩余部分直接接上。

**时间复杂度：** O(m + n)，空间复杂度 O(1)。

```javascript
function mergeTwoLists(l1, l2) {
  const dummy = new ListNode(0);
  let curr = dummy;
  while (l1 !== null && l2 !== null) {
    if (l1.val <= l2.val) {
      curr.next = l1;
      l1 = l1.next;
    } else {
      curr.next = l2;
      l2 = l2.next;
    }
    curr = curr.next;
  }
  curr.next = l1 !== null ? l1 : l2;
  return dummy.next;
}
```

```go
func mergeTwoLists(l1 *ListNode, l2 *ListNode) *ListNode {
    dummy := &ListNode{}
    curr := dummy
    for l1 != nil && l2 != nil {
        if l1.Val <= l2.Val {
            curr.Next = l1
            l1 = l1.Next
        } else {
            curr.Next = l2
            l2 = l2.Next
        }
        curr = curr.Next
    }
    if l1 != nil {
        curr.Next = l1
    } else {
        curr.Next = l2
    }
    return dummy.Next
}
```

---

## 环形链表

**题目描述：** 给你一个链表的头节点 `head`，判断链表中是否有环。

**思路分析：** 使用快慢指针（Floyd 判圈算法）。慢指针每次走一步，快指针每次走两步。如果链表中存在环，快指针最终会追上慢指针（两者相遇）；如果没有环，快指针会先到达链表末尾。

**时间复杂度：** O(n)，空间复杂度 O(1)。

```javascript
function hasCycle(head) {
  let slow = head, fast = head;
  while (fast !== null && fast.next !== null) {
    slow = slow.next;
    fast = fast.next.next;
    if (slow === fast) return true;
  }
  return false;
}
```

```go
func hasCycle(head *ListNode) bool {
    slow, fast := head, head
    for fast != nil && fast.Next != nil {
        slow = slow.Next
        fast = fast.Next.Next
        if slow == fast {
            return true
        }
    }
    return false
}
```

---

## 环形链表 II（找入环点）

**题目描述：** 给定一个链表的头节点 `head`，如果链表中有环，返回环的入口节点；否则返回 `null`。

**思路分析：** 首先使用快慢指针判断是否有环，找到相遇点。设链表头到入环点距离为 a，入环点到相遇点距离为 b，相遇点再走到入环点距离为 c。快指针走的路程是慢指针的两倍：`2(a + b) = a + b + n(b + c)`，化简得 `a = c + (n-1)(b+c)`。这意味着从链表头和相遇点同时出发，每次各走一步，两者会在入环点相遇。

**时间复杂度：** O(n)，空间复杂度 O(1)。

```javascript
function detectCycle(head) {
  let slow = head, fast = head;
  while (fast !== null && fast.next !== null) {
    slow = slow.next;
    fast = fast.next.next;
    if (slow === fast) {
      let ptr = head;
      while (ptr !== slow) {
        ptr = ptr.next;
        slow = slow.next;
      }
      return ptr;
    }
  }
  return null;
}
```

```go
func detectCycle(head *ListNode) *ListNode {
    slow, fast := head, head
    for fast != nil && fast.Next != nil {
        slow = slow.Next
        fast = fast.Next.Next
        if slow == fast {
            ptr := head
            for ptr != slow {
                ptr = ptr.Next
                slow = slow.Next
            }
            return ptr
        }
    }
    return nil
}
```

---

## 删除链表倒数第 N 个节点

**题目描述：** 给你一个链表，删除链表的倒数第 `n` 个结点，并且返回链表的头结点。

**思路分析：** 使用双指针（快慢指针）配合虚拟头节点。先让快指针走 n 步，然后快慢指针同时走，当快指针到达链表末尾时，慢指针正好指向倒数第 n+1 个节点（即待删除节点的前驱）。使用虚拟头节点可以统一处理删除头节点的情况。

**时间复杂度：** O(n)，空间复杂度 O(1)。

```javascript
function removeNthFromEnd(head, n) {
  const dummy = new ListNode(0, head);
  let fast = dummy, slow = dummy;
  for (let i = 0; i <= n; i++) {
    fast = fast.next;
  }
  while (fast !== null) {
    fast = fast.next;
    slow = slow.next;
  }
  slow.next = slow.next.next;
  return dummy.next;
}
```

```go
func removeNthFromEnd(head *ListNode, n int) *ListNode {
    dummy := &ListNode{Next: head}
    fast, slow := dummy, dummy
    for i := 0; i <= n; i++ {
        fast = fast.Next
    }
    for fast != nil {
        fast = fast.Next
        slow = slow.Next
    }
    slow.Next = slow.Next.Next
    return dummy.Next
}
```

---

## 两两交换链表节点

**题目描述：** 给你一个链表，两两交换其中相邻的节点，并返回交换后链表的头节点。你必须在不修改节点值的情况下完成交换（即只进行节点交换）。

**思路分析：** 使用虚拟头节点。设当前节点为 `prev`，需要交换 `prev.next`（节点 A）和 `prev.next.next`（节点 B）。操作步骤：1) `prev.next = B`；2) `A.next = B.next`；3) `B.next = A`；4) `prev = A`（移动到下一对的前驱位置）。

**时间复杂度：** O(n)，空间复杂度 O(1)。

```javascript
function swapPairs(head) {
  const dummy = new ListNode(0, head);
  let prev = dummy;
  while (prev.next !== null && prev.next.next !== null) {
    const a = prev.next;
    const b = prev.next.next;
    prev.next = b;
    a.next = b.next;
    b.next = a;
    prev = a;
  }
  return dummy.next;
}
```

```go
func swapPairs(head *ListNode) *ListNode {
    dummy := &ListNode{Next: head}
    prev := dummy
    for prev.Next != nil && prev.Next.Next != nil {
        a := prev.Next
        b := prev.Next.Next
        prev.Next = b
        a.Next = b.Next
        b.Next = a
        prev = a
    }
    return dummy.Next
}
```

---

## K 个一组翻转链表

**题目描述：** 给你链表的头节点 `head`，每 `k` 个节点一组进行翻转，请返回修改后的链表。如果节点总数不是 k 的整数倍，那么将最后剩余的节点保持原有顺序。

**思路分析：** 先统计链表长度或逐段检测是否够 k 个节点。对于每组 k 个节点，执行组内反转（类似反转链表的迭代法），然后将反转后的子链表与前后部分正确连接。使用虚拟头节点简化连接操作。关键是维护好每组反转前后的首尾指针。

**时间复杂度：** O(n)，空间复杂度 O(1)。

```javascript
function reverseKGroup(head, k) {
  const dummy = new ListNode(0, head);
  let prevGroupEnd = dummy;

  while (true) {
    // 检查剩余节点是否足够 k 个
    let kth = prevGroupEnd;
    for (let i = 0; i < k; i++) {
      kth = kth.next;
      if (kth === null) return dummy.next;
    }

    const groupStart = prevGroupEnd.next;
    const nextGroupStart = kth.next;

    // 反转 k 个节点
    let prev = nextGroupStart, curr = groupStart;
    for (let i = 0; i < k; i++) {
      const next = curr.next;
      curr.next = prev;
      prev = curr;
      curr = next;
    }

    prevGroupEnd.next = kth;
    prevGroupEnd = groupStart;
  }
}
```

```go
func reverseKGroup(head *ListNode, k int) *ListNode {
    dummy := &ListNode{Next: head}
    prevGroupEnd := dummy

    for {
        kth := prevGroupEnd
        for i := 0; i < k; i++ {
            kth = kth.Next
            if kth == nil {
                return dummy.Next
            }
        }

        groupStart := prevGroupEnd.Next
        nextGroupStart := kth.Next

        prev := nextGroupStart
        curr := groupStart
        for i := 0; i < k; i++ {
            next := curr.Next
            curr.Next = prev
            prev = curr
            curr = next
        }

        prevGroupEnd.Next = kth
        prevGroupEnd = groupStart
    }
}
```

---

## 合并 K 个升序链表

**题目描述：** 给你一个链表数组，每个链表都已经按升序排列。请将所有链表合并到一个升序链表中，返回合并后的链表。

**思路分析：** 使用优先队列（最小堆）。将所有链表的头节点放入最小堆中，每次取出堆顶（最小值）节点接到结果链表，然后将该节点的下一个节点（如果存在）放入堆中。也可以使用分治法，两两合并链表，复杂度相同。

**时间复杂度：** O(N log k)，N 为所有节点总数，k 为链表个数。空间复杂度 O(k)。

```javascript
// 使用分治法（JavaScript 中实现最小堆较冗长，分治更简洁）
function mergeKLists(lists) {
  if (lists.length === 0) return null;
  return divideAndMerge(lists, 0, lists.length - 1);
}

function divideAndMerge(lists, left, right) {
  if (left === right) return lists[left];
  const mid = Math.floor((left + right) / 2);
  const l1 = divideAndMerge(lists, left, mid);
  const l2 = divideAndMerge(lists, mid + 1, right);
  return mergeTwoLists(l1, l2);
}

function mergeTwoLists(l1, l2) {
  const dummy = new ListNode(0);
  let curr = dummy;
  while (l1 !== null && l2 !== null) {
    if (l1.val <= l2.val) {
      curr.next = l1;
      l1 = l1.next;
    } else {
      curr.next = l2;
      l2 = l2.next;
    }
    curr = curr.next;
  }
  curr.next = l1 !== null ? l1 : l2;
  return dummy.next;
}
```

```go
// 使用最小堆
import "container/heap"

type MinHeap []*ListNode

func (h MinHeap) Len() int            { return len(h) }
func (h MinHeap) Less(i, j int) bool   { return h[i].Val < h[j].Val }
func (h MinHeap) Swap(i, j int)        { h[i], h[j] = h[j], h[i] }
func (h *MinHeap) Push(x interface{})  { *h = append(*h, x.(*ListNode)) }
func (h *MinHeap) Pop() interface{} {
    old := *h
    n := len(old)
    x := old[n-1]
    *h = old[:n-1]
    return x
}

func mergeKLists(lists []*ListNode) *ListNode {
    h := &MinHeap{}
    heap.Init(h)
    for _, node := range lists {
        if node != nil {
            heap.Push(h, node)
        }
    }
    dummy := &ListNode{}
    curr := dummy
    for h.Len() > 0 {
        node := heap.Pop(h).(*ListNode)
        curr.Next = node
        curr = curr.Next
        if node.Next != nil {
            heap.Push(h, node.Next)
        }
    }
    return dummy.Next
}
```

---

## LRU 缓存

**题目描述：** 请你设计并实现一个满足 LRU（最近最少使用）缓存约束的数据结构。实现 `LRUCache` 类：`LRUCache(int capacity)` 以正整数作为容量初始化；`int get(int key)` 如果关键字存在缓存中则返回值，否则返回 -1；`void put(int key, int value)` 如果关键字已经存在则变更其值，如果不存在则插入。当缓存容量达到上限时应淘汰最久未使用的关键字。要求 get 和 put 的时间复杂度均为 O(1)。

**思路分析：** 使用哈希表 + 双向链表。哈希表提供 O(1) 的键值查找，双向链表维护访问顺序——最近使用的在链表头部，最久未使用的在尾部。get 操作时将节点移到链表头部；put 操作时若 key 存在则更新值并移到头部，若不存在则创建新节点插入头部，若超出容量则删除尾部节点。

**时间复杂度：** get 和 put 均为 O(1)。

```javascript
class LRUCache {
  constructor(capacity) {
    this.capacity = capacity;
    this.map = new Map();
    // 双向链表的虚拟头尾节点
    this.head = { key: 0, val: 0, prev: null, next: null };
    this.tail = { key: 0, val: 0, prev: null, next: null };
    this.head.next = this.tail;
    this.tail.prev = this.head;
  }

  _addToHead(node) {
    node.prev = this.head;
    node.next = this.head.next;
    this.head.next.prev = node;
    this.head.next = node;
  }

  _removeNode(node) {
    node.prev.next = node.next;
    node.next.prev = node.prev;
  }

  _moveToHead(node) {
    this._removeNode(node);
    this._addToHead(node);
  }

  get(key) {
    if (!this.map.has(key)) return -1;
    const node = this.map.get(key);
    this._moveToHead(node);
    return node.val;
  }

  put(key, value) {
    if (this.map.has(key)) {
      const node = this.map.get(key);
      node.val = value;
      this._moveToHead(node);
    } else {
      const node = { key, val: value, prev: null, next: null };
      this.map.set(key, node);
      this._addToHead(node);
      if (this.map.size > this.capacity) {
        const tail = this.tail.prev;
        this._removeNode(tail);
        this.map.delete(tail.key);
      }
    }
  }
}
```

```go
type LRUCache struct {
    capacity int
    cache    map[int]*DLinkedNode
    head     *DLinkedNode
    tail     *DLinkedNode
}

type DLinkedNode struct {
    key, value int
    prev, next *DLinkedNode
}

func Constructor(capacity int) LRUCache {
    head := &DLinkedNode{}
    tail := &DLinkedNode{}
    head.next = tail
    tail.prev = head
    return LRUCache{
        capacity: capacity,
        cache:    make(map[int]*DLinkedNode),
        head:     head,
        tail:     tail,
    }
}

func (l *LRUCache) addToHead(node *DLinkedNode) {
    node.prev = l.head
    node.next = l.head.next
    l.head.next.prev = node
    l.head.next = node
}

func (l *LRUCache) removeNode(node *DLinkedNode) {
    node.prev.next = node.next
    node.next.prev = node.prev
}

func (l *LRUCache) moveToHead(node *DLinkedNode) {
    l.removeNode(node)
    l.addToHead(node)
}

func (l *LRUCache) Get(key int) int {
    if node, ok := l.cache[key]; ok {
        l.moveToHead(node)
        return node.value
    }
    return -1
}

func (l *LRUCache) Put(key int, value int) {
    if node, ok := l.cache[key]; ok {
        node.value = value
        l.moveToHead(node)
    } else {
        node := &DLinkedNode{key: key, value: value}
        l.cache[key] = node
        l.addToHead(node)
        if len(l.cache) > l.capacity {
            tail := l.tail.prev
            l.removeNode(tail)
            delete(l.cache, tail.key)
        }
    }
}
```

---

## 相交链表

**题目描述：** 给你两个单链表的头节点 `headA` 和 `headB`，请找出并返回两个单链表相交的起始节点。如果没有相交则返回 `null`。

**思路分析：** 设链表 A 长度为 a，链表 B 长度为 b，公共部分长度为 c。指针 pA 从 A 出发，走完 A 后从 B 头继续走；指针 pB 从 B 出发，走完 B 后从 A 头继续走。当两者相遇时，各自走了 `a + (b - c)` 和 `b + (a - c)` 步，这两个值相等，因此会在交点相遇。如果不相交，两者会同时到达 null。

**时间复杂度：** O(m + n)，空间复杂度 O(1)。

```javascript
function getIntersectionNode(headA, headB) {
  let pA = headA, pB = headB;
  while (pA !== pB) {
    pA = pA === null ? headB : pA.next;
    pB = pB === null ? headA : pB.next;
  }
  return pA;
}
```

```go
func getIntersectionNode(headA, headB *ListNode) *ListNode {
    pA, pB := headA, headB
    for pA != pB {
        if pA == nil {
            pA = headB
        } else {
            pA = pA.Next
        }
        if pB == nil {
            pB = headA
        } else {
            pB = pB.Next
        }
    }
    return pA
}
```

---

## 总结

| 题目 | 核心技巧 | 时间复杂度 |
|------|----------|-----------|
| 反转链表 | 迭代 / 递归 | O(n) |
| 合并两个有序链表 | 虚拟头节点 + 归并 | O(m+n) |
| 环形链表 | 快慢指针 | O(n) |
| 环形链表 II | 快慢指针 + 数学推导 | O(n) |
| 删除倒数第 N 个节点 | 双指针 + 虚拟头 | O(n) |
| 两两交换节点 | 虚拟头节点 | O(n) |
| K 个一组翻转 | 分组反转 | O(n) |
| 合并 K 个升序链表 | 最小堆 / 分治 | O(N log k) |
| LRU 缓存 | 哈希表 + 双向链表 | O(1) |
| 相交链表 | 双指针等距法 | O(m+n) |

链表题的核心在于熟练运用**虚拟头节点**统一边界处理、**快慢指针**解决环和距离相关问题、以及清晰地管理指针的指向关系。面试中务必注意空指针检查和边界条件。
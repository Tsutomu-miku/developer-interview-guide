# 前端状态管理深度解析

> 本文系统梳理前端状态管理的核心概念、主流方案、最佳实践与高频面试题，覆盖 Redux、Zustand、Jotai、Recoil、Valtio、Pinia、Signals、TanStack Query、XState 等方案，适合中高级前端工程师面试准备与技术选型参考。

---

## 目录

1. [状态管理概述](#一状态管理概述)
2. [Redux 生态系统](#二redux-生态系统)
3. [新一代 React 状态管理](#三新一代-react-状态管理)
4. [Vue 状态管理](#四vue-状态管理)
5. [跨框架方案](#五跨框架方案)
6. [Server State 管理](#六server-state-管理)
7. [最佳实践与架构设计](#七最佳实践与架构设计)
8. [高频面试题精选](#八高频面试题精选)

---

## 一、状态管理概述

### 1.1 为什么需要状态管理

在现代前端应用中，"状态"无处不在：UI 的展开/折叠、表单的输入值、从服务端获取的数据列表、用户的登录信息、路由参数等。当应用规模增长，状态的数量和复杂度也在增长，如果没有良好的管理策略，会面临以下问题：

- **数据流混乱（Spaghetti Data Flow）**：父子组件、兄弟组件、跨层级组件之间的数据传递变得难以追踪。
- **Props Drilling**：为了让深层子组件获取数据，需要逐层传递 props，导致中间组件被迫接收与自身无关的属性。
- **状态同步困难**：多个组件依赖同一份数据时，如何保证修改后各处 UI 同步更新？
- **可预测性差**：缺乏统一的状态变更机制，难以复现问题、做时间旅行调试。
- **服务端数据缓存**：接口数据的缓存、过期、重新验证、乐观更新等需求，纯粹靠组件本地状态难以优雅处理。

### 1.2 Server State vs Client State

面试中经常被问到的核心区分：

| 维度 | Client State（客户端状态） | Server State（服务端状态） |
|------|---------------------------|---------------------------|
| 数据来源 | 用户交互产生（UI 状态、表单值） | 来自远程服务器的异步数据 |
| 所有权 | 前端完全拥有 | 前端只是"缓存"了一份快照 |
| 生命周期 | 随组件/页面生命周期 | 可能随时因其他客户端操作而"过期" |
| 同步策略 | 无需同步 | 需要 refetch / revalidate / 乐观更新 |
| 典型工具 | Redux, Zustand, Jotai, Pinia | TanStack Query, SWR, Apollo Client |

**面试要点**：很多团队的痛点在于把 Server State 放进 Redux 等客户端状态管理工具中，导致大量样板代码处理 loading / error / caching，而这些恰好是 TanStack Query 等工具的专长。现代最佳实践是 **Client State 与 Server State 分离管理**。

### 1.3 状态管理演进历史

```
jQuery 时代（DOM 即状态）
    ↓
Backbone.js（Model-View 分离）
    ↓
Flux 架构（Facebook, 2014）—— 单向数据流思想
    ↓
Redux（Dan Abramov, 2015）—— 单一状态树 + 纯函数 reducer
    ↓
MobX（响应式）/ Vuex（Vue 生态）
    ↓
Context API + useReducer（React 内置方案）
    ↓
新一代：Zustand / Jotai / Recoil / Valtio / Pinia
    ↓
Server State 工具兴起：React Query / SWR / Apollo
    ↓
跨框架：Signals（Preact / Solid / Angular / TC39 提案）
```

---

## 二、Redux 生态系统

### 2.1 Redux 核心原理

Redux 遵循三大原则：

1. **Single Source of Truth**：整个应用的状态存储在单一的 store 中。
2. **State is Read-Only**：唯一改变状态的方式是 dispatch 一个 action。
3. **Changes are Made with Pure Functions**：用纯函数 reducer 来描述状态如何变化。

#### 手写 Mini-Redux

```javascript
// mini-redux.js —— 核心不到 50 行
function createStore(reducer, preloadedState, enhancer) {
  // 如果传入了 enhancer（如 applyMiddleware），则由 enhancer 来增强 createStore
  if (typeof enhancer === 'function') {
    return enhancer(createStore)(reducer, preloadedState);
  }

  let currentState = preloadedState;
  let currentReducer = reducer;
  let listeners = [];
  let isDispatching = false;

  function getState() {
    if (isDispatching) {
      throw new Error('不允许在 reducer 执行过程中调用 getState');
    }
    return currentState;
  }

  function subscribe(listener) {
    if (typeof listener !== 'function') {
      throw new Error('listener 必须是函数');
    }
    let isSubscribed = true;
    listeners.push(listener);

    // 返回取消订阅函数
    return function unsubscribe() {
      if (!isSubscribed) return;
      isSubscribed = false;
      const index = listeners.indexOf(listener);
      listeners.splice(index, 1);
    };
  }

  function dispatch(action) {
    if (typeof action.type === 'undefined') {
      throw new Error('action 必须有 type 属性');
    }
    if (isDispatching) {
      throw new Error('reducer 中不允许 dispatch');
    }

    try {
      isDispatching = true;
      currentState = currentReducer(currentState, action);
    } finally {
      isDispatching = false;
    }

    // 通知所有订阅者
    listeners.forEach(listener => listener());
    return action;
  }

  // 初始化状态树
  dispatch({ type: '@@INIT' });

  return { getState, subscribe, dispatch };
}
```

#### 手写 combineReducers

```javascript
function combineReducers(reducers) {
  const reducerKeys = Object.keys(reducers);

  return function combination(state = {}, action) {
    let hasChanged = false;
    const nextState = {};

    for (const key of reducerKeys) {
      const reducer = reducers[key];
      const previousStateForKey = state[key];
      const nextStateForKey = reducer(previousStateForKey, action);

      nextState[key] = nextStateForKey;
      hasChanged = hasChanged || nextStateForKey !== previousStateForKey;
    }

    // 检查 key 的数量是否变化
    hasChanged = hasChanged || reducerKeys.length !== Object.keys(state).length;
    return hasChanged ? nextState : state;
  };
}
```

### 2.2 中间件机制

Redux 中间件是对 dispatch 的增强，采用洋葱模型。

#### 手写 applyMiddleware

```javascript
function applyMiddleware(...middlewares) {
  return (createStore) => (reducer, preloadedState) => {
    const store = createStore(reducer, preloadedState);
    let dispatch = () => {
      throw new Error('不允许在中间件构建阶段 dispatch');
    };

    // 暴露给中间件的 API
    const middlewareAPI = {
      getState: store.getState,
      dispatch: (action, ...args) => dispatch(action, ...args),
    };

    // 组装中间件链
    const chain = middlewares.map(middleware => middleware(middlewareAPI));
    dispatch = compose(...chain)(store.dispatch);

    return { ...store, dispatch };
  };
}

// compose 函数：从右到左组合函数
function compose(...funcs) {
  if (funcs.length === 0) return (arg) => arg;
  if (funcs.length === 1) return funcs[0];
  return funcs.reduce((a, b) => (...args) => a(b(...args)));
}
```

#### 手写 redux-logger 中间件

```javascript
const logger = (store) => (next) => (action) => {
  console.group(action.type);
  console.log('prev state:', store.getState());
  console.log('action:', action);
  const result = next(action);
  console.log('next state:', store.getState());
  console.groupEnd();
  return result;
};
```

### 2.3 redux-thunk vs redux-saga

#### redux-thunk

thunk 的核心极其简洁——让 dispatch 可以接受函数：

```javascript
// redux-thunk 核心源码（简化版）
function createThunkMiddleware(extraArgument) {
  return ({ dispatch, getState }) => (next) => (action) => {
    if (typeof action === 'function') {
      return action(dispatch, getState, extraArgument);
    }
    return next(action);
  };
}

const thunk = createThunkMiddleware();

// 使用示例
const fetchUser = (userId) => async (dispatch, getState) => {
  dispatch({ type: 'FETCH_USER_PENDING' });
  try {
    const response = await fetch(`/api/users/${userId}`);
    const data = await response.json();
    dispatch({ type: 'FETCH_USER_FULFILLED', payload: data });
  } catch (error) {
    dispatch({ type: 'FETCH_USER_REJECTED', payload: error.message });
  }
};
```

#### redux-saga

saga 基于 Generator 函数，用声明式的 Effect 来描述副作用：

```javascript
import { call, put, takeLatest, all, fork, delay } from 'redux-saga/effects';

// Worker Saga
function* fetchUserSaga(action) {
  try {
    yield put({ type: 'FETCH_USER_PENDING' });
    const user = yield call(api.fetchUser, action.payload.userId);
    yield put({ type: 'FETCH_USER_FULFILLED', payload: user });
  } catch (error) {
    yield put({ type: 'FETCH_USER_REJECTED', payload: error.message });
  }
}

// Watcher Saga —— takeLatest 自动取消之前未完成的请求
function* watchFetchUser() {
  yield takeLatest('FETCH_USER_REQUEST', fetchUserSaga);
}

// 防抖示例
function* debouncedSearch() {
  yield delay(300);
  yield call(performSearch);
}

function* watchSearch() {
  yield takeLatest('SEARCH_INPUT_CHANGED', debouncedSearch);
}

// Root Saga
export default function* rootSaga() {
  yield all([fork(watchFetchUser), fork(watchSearch)]);
}
```

| 对比维度 | redux-thunk | redux-saga |
|---------|-------------|------------|
| 学习成本 | 低，就是函数 | 高，需要掌握 Generator 和 Effects |
| 可测试性 | 需要 mock API | Effect 声明式，易于断言 |
| 复杂异步流 | 需要手动管理 | takeLatest/race/all 开箱即用 |
| 包体积 | ~1KB | ~25KB |
| 适用场景 | 简单异步 | 复杂业务流程编排 |

### 2.4 Redux Toolkit (RTK)

RTK 是 Redux 官方推荐的标准化工具集，大幅减少样板代码。

#### createSlice

```javascript
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

// createAsyncThunk 自动生成 pending/fulfilled/rejected action types
export const fetchTodos = createAsyncThunk(
  'todos/fetchTodos',
  async (_, { rejectWithValue }) => {
    try {
      const response = await fetch('/api/todos');
      if (!response.ok) throw new Error('Network error');
      return await response.json();
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

const todosSlice = createSlice({
  name: 'todos',
  initialState: {
    items: [],
    status: 'idle', // 'idle' | 'loading' | 'succeeded' | 'failed'
    error: null,
  },
  reducers: {
    // RTK 内部使用 Immer，可以直接"修改"状态
    addTodo(state, action) {
      state.items.push({
        id: Date.now(),
        text: action.payload,
        completed: false,
      });
    },
    toggleTodo(state, action) {
      const todo = state.items.find(t => t.id === action.payload);
      if (todo) {
        todo.completed = !todo.completed;
      }
    },
    removeTodo(state, action) {
      state.items = state.items.filter(t => t.id !== action.payload);
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchTodos.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchTodos.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.items = action.payload;
      })
      .addCase(fetchTodos.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload;
      });
  },
});

export const { addTodo, toggleTodo, removeTodo } = todosSlice.actions;
export default todosSlice.reducer;
```

#### RTK Query

RTK Query 是 Redux Toolkit 内置的数据获取和缓存方案，大幅简化 Server State 管理：

```javascript
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export const apiSlice = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({ baseUrl: '/api' }),
  tagTypes: ['Post', 'User'],
  endpoints: (builder) => ({
    // 查询端点
    getPosts: builder.query({
      query: (page = 1) => `/posts?page=${page}&limit=10`,
      providesTags: (result) =>
        result
          ? [
              ...result.map(({ id }) => ({ type: 'Post', id })),
              { type: 'Post', id: 'LIST' },
            ]
          : [{ type: 'Post', id: 'LIST' }],
    }),
    getPostById: builder.query({
      query: (id) => `/posts/${id}`,
      providesTags: (result, error, id) => [{ type: 'Post', id }],
    }),
    // 变更端点
    addPost: builder.mutation({
      query: (newPost) => ({
        url: '/posts',
        method: 'POST',
        body: newPost,
      }),
      invalidatesTags: [{ type: 'Post', id: 'LIST' }],
    }),
    updatePost: builder.mutation({
      query: ({ id, ...patch }) => ({
        url: `/posts/${id}`,
        method: 'PATCH',
        body: patch,
      }),
      // 乐观更新
      async onQueryStarted({ id, ...patch }, { dispatch, queryFulfilled }) {
        const patchResult = dispatch(
          apiSlice.util.updateQueryData('getPostById', id, (draft) => {
            Object.assign(draft, patch);
          })
        );
        try {
          await queryFulfilled;
        } catch {
          patchResult.undo(); // 失败时回滚
        }
      },
      invalidatesTags: (result, error, { id }) => [{ type: 'Post', id }],
    }),
  }),
});

export const {
  useGetPostsQuery,
  useGetPostByIdQuery,
  useAddPostMutation,
  useUpdatePostMutation,
} = apiSlice;
```

### 2.5 Immer 原理解析

RTK 内部使用 Immer 实现"可变式写法，不可变式结果"。其核心原理是 **Proxy + Copy-on-Write**：

```javascript
// 简化版 Immer 原理
function produce(baseState, recipe) {
  // 1. 创建草稿（draft）—— 基于 Proxy
  const drafts = new Map();

  function createDraft(base) {
    if (typeof base !== 'object' || base === null) return base;

    const draft = { base, copy: undefined, modified: false };

    const proxy = new Proxy(base, {
      get(target, prop) {
        // 如果已修改，从 copy 中读取
        if (draft.copy) {
          const value = draft.copy[prop];
          // 对子对象也创建 draft（惰性代理）
          if (typeof value === 'object' && value !== null && !drafts.has(value)) {
            const childDraft = createDraft(value);
            draft.copy[prop] = childDraft;
            return childDraft;
          }
          return value;
        }
        return target[prop];
      },
      set(target, prop, value) {
        if (!draft.modified) {
          // Copy-on-Write：首次修改时浅拷贝
          draft.copy = Array.isArray(base) ? [...base] : { ...base };
          draft.modified = true;
        }
        draft.copy[prop] = value;
        return true;
      },
    });

    drafts.set(proxy, draft);
    return proxy;
  }

  // 2. 将草稿传给用户的 recipe 函数
  const draftState = createDraft(baseState);
  recipe(draftState);

  // 3. 从草稿中生成最终的不可变状态
  function finalize(draft) {
    const info = drafts.get(draft);
    if (!info) return draft;
    if (!info.modified) return info.base; // 未修改，返回原对象（结构共享）
    const result = info.copy;
    for (const key in result) {
      if (drafts.has(result[key])) {
        result[key] = finalize(result[key]);
      }
    }
    return Object.freeze(result);
  }

  return finalize(draftState);
}

// 使用示例
const state = { users: [{ name: 'Alice', age: 25 }], settings: { theme: 'dark' } };
const nextState = produce(state, (draft) => {
  draft.users[0].age = 26;
});

console.log(nextState.users[0].age); // 26（新对象）
console.log(nextState.settings === state.settings); // true（结构共享，未修改的部分引用不变）
```

---

## 三、新一代 React 状态管理

### 3.1 Zustand

Zustand（德语"状态"）是基于发布订阅模式的极简状态管理库，包体积仅约 1KB。

#### 核心原理

```javascript
// Zustand 核心原理简化版
function createStore(createState) {
  let state;
  const listeners = new Set();

  const getState = () => state;

  const setState = (partial, replace) => {
    const nextState = typeof partial === 'function' ? partial(state) : partial;
    if (!Object.is(nextState, state)) {
      const previousState = state;
      state = replace ? nextState : Object.assign({}, state, nextState);
      listeners.forEach((listener) => listener(state, previousState));
    }
  };

  const subscribe = (listener) => {
    listeners.add(listener);
    return () => listeners.delete(listener);
  };

  const destroy = () => listeners.clear();

  const api = { getState, setState, subscribe, destroy };
  state = createState(setState, getState, api);

  return api;
}

// React Hook 绑定（简化版）
function useStore(api, selector = (s) => s, equalityFn = Object.is) {
  const [, forceUpdate] = React.useReducer((c) => c + 1, 0);
  const selectorRef = React.useRef(selector);
  const stateRef = React.useRef(api.getState());
  const selectedRef = React.useRef(selector(api.getState()));

  React.useEffect(() => {
    const unsubscribe = api.subscribe((nextState) => {
      const nextSelected = selectorRef.current(nextState);
      if (!equalityFn(selectedRef.current, nextSelected)) {
        selectedRef.current = nextSelected;
        stateRef.current = nextState;
        forceUpdate();
      }
    });
    return unsubscribe;
  }, [api, equalityFn]);

  return selectedRef.current;
}
```

#### 实际使用：中间件与持久化

```javascript
import { create } from 'zustand';
import { devtools, persist, subscribeWithSelector } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

// 完整示例：带中间件的 Store
const useAuthStore = create(
  devtools(
    persist(
      immer(
        subscribeWithSelector((set, get) => ({
          // 状态
          user: null,
          token: null,
          isLoading: false,
          error: null,

          // 操作
          login: async (credentials) => {
            set((state) => { state.isLoading = true; state.error = null; });
            try {
              const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(credentials),
              });
              const data = await response.json();
              set((state) => {
                state.user = data.user;
                state.token = data.token;
                state.isLoading = false;
              });
            } catch (error) {
              set((state) => {
                state.error = error.message;
                state.isLoading = false;
              });
            }
          },

          logout: () => {
            set((state) => {
              state.user = null;
              state.token = null;
            });
          },

          // 计算属性
          get isAuthenticated() {
            return get().token !== null;
          },
        }))
      ),
      {
        name: 'auth-storage',
        partialize: (state) => ({ token: state.token, user: state.user }),
      }
    ),
    { name: 'AuthStore' }
  )
);

// 订阅特定状态变化
useAuthStore.subscribe(
  (state) => state.token,
  (token, prevToken) => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }
);
```

#### Slice 模式（大型应用拆分）

```javascript
const createUserSlice = (set) => ({
  user: null,
  setUser: (user) => set({ user }),
});

const createThemeSlice = (set) => ({
  theme: 'light',
  toggleTheme: () =>
    set((state) => ({
      theme: state.theme === 'light' ? 'dark' : 'light',
    })),
});

const useBoundStore = create((...args) => ({
  ...createUserSlice(...args),
  ...createThemeSlice(...args),
}));
```

### 3.2 Jotai —— 原子化状态管理

Jotai（日语"状态"）采用自底向上的原子化方案，灵感来自 Recoil。

```javascript
import { atom, useAtom, useAtomValue, useSetAtom } from 'jotai';
import { atomWithStorage, atomWithQuery } from 'jotai/utils';
import { atomEffect } from 'jotai-effect';

// 基础原子
const countAtom = atom(0);
const nameAtom = atom('');

// 派生原子（只读）—— 类似 computed
const doubleCountAtom = atom((get) => get(countAtom) * 2);

// 可写派生原子
const decrementAtom = atom(
  null, // 读取值为 null（只写）
  (get, set) => {
    const current = get(countAtom);
    set(countAtom, current > 0 ? current - 1 : 0);
  }
);

// 异步原子
const userAtom = atom(async () => {
  const response = await fetch('/api/user');
  return response.json();
});

// 依赖其他原子的异步原子
const userPostsAtom = atom(async (get) => {
  const user = await get(userAtom);
  const response = await fetch(`/api/users/${user.id}/posts`);
  return response.json();
});

// 持久化原子
const themeAtom = atomWithStorage('theme', 'light');

// 使用示例
function Counter() {
  const [count, setCount] = useAtom(countAtom);
  const doubleCount = useAtomValue(doubleCountAtom);
  const decrement = useSetAtom(decrementAtom);

  return (
    <div>
      <p>Count: {count} (Double: {doubleCount})</p>
      <button onClick={() => setCount((c) => c + 1)}>+1</button>
      <button onClick={decrement}>-1 (min 0)</button>
    </div>
  );
}

// 带 Suspense 的异步数据
function UserPosts() {
  const posts = useAtomValue(userPostsAtom); // 自动触发 Suspense
  return (
    <ul>
      {posts.map((post) => (
        <li key={post.id}>{post.title}</li>
      ))}
    </ul>
  );
}
```

### 3.3 Recoil

Facebook 出品，引入了原子（Atom）和选择器（Selector）的概念：

```javascript
import { atom, selector, useRecoilState, useRecoilValue } from 'recoil';

// Atom —— 最小状态单元
const todoListState = atom({
  key: 'todoListState', // 全局唯一 key
  default: [],
});

const filterState = atom({
  key: 'filterState',
  default: 'all', // 'all' | 'completed' | 'active'
});

// Selector —— 派生状态
const filteredTodoListState = selector({
  key: 'filteredTodoListState',
  get: ({ get }) => {
    const list = get(todoListState);
    const filter = get(filterState);
    switch (filter) {
      case 'completed':
        return list.filter((item) => item.completed);
      case 'active':
        return list.filter((item) => !item.completed);
      default:
        return list;
    }
  },
});

// 统计信息的 Selector
const todoStatsState = selector({
  key: 'todoStatsState',
  get: ({ get }) => {
    const list = get(todoListState);
    const total = list.length;
    const completed = list.filter((item) => item.completed).length;
    const active = total - completed;
    const percent = total === 0 ? 0 : Math.round((completed / total) * 100);
    return { total, completed, active, percent };
  },
});
```

### 3.4 Valtio —— Proxy-based 响应式

Valtio 利用 ES6 Proxy 实现自动追踪和精细化更新：

```javascript
import { proxy, useSnapshot, subscribe, ref } from 'valtio';
import { derive, proxyWithComputed } from 'valtio/utils';

// 创建响应式状态
const store = proxy({
  count: 0,
  users: [],
  // ref() 包裹的值不会被 proxy 代理（适合存 DOM 节点、类实例等）
  mapInstance: ref(new Map()),
});

// 派生状态
const derived = derive({
  doubleCount: (get) => get(store).count * 2,
});

// 带计算属性的 proxy
const storeWithComputed = proxyWithComputed(
  { firstName: 'John', lastName: 'Doe' },
  {
    fullName: (snap) => `${snap.firstName} ${snap.lastName}`,
  }
);

// 直接修改——Valtio 的魅力所在
function increment() {
  store.count++; // 就像操作普通对象一样
}

async function fetchUsers() {
  const response = await fetch('/api/users');
  store.users = await response.json();
}

// React 组件中使用 useSnapshot 获取不可变快照
function UserList() {
  const snap = useSnapshot(store);
  return (
    <div>
      <p>Count: {snap.count}</p>
      <button onClick={increment}>+1</button>
      <ul>
        {snap.users.map((user) => (
          <li key={user.id}>{user.name}</li>
        ))}
      </ul>
    </div>
  );
}

// 在 React 外部订阅变化
subscribe(store, () => {
  console.log('store changed:', store.count);
});
```

### 3.5 方案对比与选型

| 维度 | Zustand | Jotai | Recoil | Valtio |
|------|---------|-------|--------|--------|
| 心智模型 | 类 Redux（单一 store） | 原子化（自底向上） | 原子化（自底向上） | Proxy 响应式 |
| 包体积 | ~1KB | ~2KB | ~20KB | ~3KB |
| TypeScript | 优秀 | 优秀 | 一般 | 优秀 |
| React 外使用 | 原生支持 | 需要额外设置 | 不支持 | 原生支持 |
| DevTools | Redux DevTools | 自有 | 自有 | Valtio DevTools |
| 学习曲线 | 极低 | 低 | 中 | 极低 |
| 适用场景 | 通用，中大型应用 | 细粒度更新 | Facebook 系 | 快速原型、简单状态 |

**选型建议**：
- 需要类 Redux 但更简洁 → **Zustand**
- 需要极细粒度的更新控制 → **Jotai**
- 喜欢直接修改对象的直觉 → **Valtio**
- 团队从 Redux 迁移 → **Zustand**（最小认知迁移成本）

---

## 四、Vue 状态管理

### 4.1 Vuex 核心概念

Vuex 是 Vue 2 时代的官方状态管理方案：

```javascript
// store/index.js
import { createStore } from 'vuex';

export default createStore({
  // 状态
  state() {
    return {
      count: 0,
      todos: [],
      user: null,
    };
  },

  // 同步变更（唯一可以修改 state 的地方）
  mutations: {
    INCREMENT(state) {
      state.count++;
    },
    SET_TODOS(state, todos) {
      state.todos = todos;
    },
    ADD_TODO(state, todo) {
      state.todos.push(todo);
    },
    SET_USER(state, user) {
      state.user = user;
    },
  },

  // 异步操作
  actions: {
    async fetchTodos({ commit }) {
      const response = await fetch('/api/todos');
      const todos = await response.json();
      commit('SET_TODOS', todos);
    },
    async login({ commit }, credentials) {
      const response = await fetch('/api/login', {
        method: 'POST',
        body: JSON.stringify(credentials),
      });
      const user = await response.json();
      commit('SET_USER', user);
    },
  },

  // 计算属性
  getters: {
    completedTodos: (state) => state.todos.filter((t) => t.completed),
    todoCount: (state) => state.todos.length,
    isAuthenticated: (state) => !!state.user,
  },

  // 模块化
  modules: {
    // 命名空间模块
  },
});
```

### 4.2 Pinia —— Vue 新一代状态管理

Pinia 是 Vue 3 官方推荐的状态管理方案，也兼容 Vue 2。

#### Pinia vs Vuex 对比

| 对比维度 | Vuex 4 | Pinia |
|---------|--------|-------|
| 支持版本 | Vue 2 & 3 | Vue 2 & 3 |
| Mutations | 需要 | 取消，直接修改 state |
| TypeScript | 需要复杂类型标注 | 自动类型推导 |
| 模块嵌套 | 支持深层嵌套 | 扁平化，store 间可引用 |
| Devtools | 支持 | 支持 |
| SSR | 需要额外处理 | 开箱即用 |
| 代码拆分 | 需要动态注册 | 自动代码拆分 |
| 包体积 | ~6KB | ~1.5KB |

#### Options Store 风格

```javascript
// stores/counter.js
import { defineStore } from 'pinia';

export const useCounterStore = defineStore('counter', {
  state: () => ({
    count: 0,
    name: 'Eduardo',
    items: [],
    lastFetched: null,
  }),

  getters: {
    doubleCount: (state) => state.count * 2,
    // 使用 this 访问其他 getter
    doubleCountPlusOne() {
      return this.doubleCount + 1;
    },
    // 接受参数的 getter
    getItemById: (state) => {
      return (id) => state.items.find((item) => item.id === id);
    },
  },

  actions: {
    increment() {
      this.count++;
    },
    async fetchItems() {
      try {
        const response = await fetch('/api/items');
        this.items = await response.json();
        this.lastFetched = Date.now();
      } catch (error) {
        console.error('Failed to fetch items:', error);
        throw error;
      }
    },
    // 可以调用其他 store
    async checkout() {
      const cartStore = useCartStore();
      const orderStore = useOrderStore();
      await orderStore.createOrder(cartStore.items);
      cartStore.clearCart();
    },
  },
});
```

#### Setup Store 风格（组合式 API）

```javascript
// stores/cart.js
import { defineStore } from 'pinia';
import { ref, computed, watch } from 'vue';

export const useCartStore = defineStore('cart', () => {
  // ref() -> state
  const items = ref([]);
  const coupon = ref(null);
  const isLoading = ref(false);

  // computed() -> getters
  const totalItems = computed(() =>
    items.value.reduce((sum, item) => sum + item.quantity, 0)
  );

  const subtotal = computed(() =>
    items.value.reduce((sum, item) => sum + item.price * item.quantity, 0)
  );

  const discount = computed(() => {
    if (!coupon.value) return 0;
    return subtotal.value * (coupon.value.percent / 100);
  });

  const total = computed(() => subtotal.value - discount.value);

  // function() -> actions
  function addItem(product, quantity = 1) {
    const existing = items.value.find((i) => i.id === product.id);
    if (existing) {
      existing.quantity += quantity;
    } else {
      items.value.push({ ...product, quantity });
    }
  }

  function removeItem(productId) {
    const index = items.value.findIndex((i) => i.id === productId);
    if (index > -1) {
      items.value.splice(index, 1);
    }
  }

  function clearCart() {
    items.value = [];
    coupon.value = null;
  }

  async function applyCoupon(code) {
    isLoading.value = true;
    try {
      const response = await fetch(`/api/coupons/${code}`);
      coupon.value = await response.json();
    } finally {
      isLoading.value = false;
    }
  }

  // 自动持久化到 localStorage
  watch(items, (newItems) => {
    localStorage.setItem('cart', JSON.stringify(newItems));
  }, { deep: true });

  return {
    items, coupon, isLoading,
    totalItems, subtotal, discount, total,
    addItem, removeItem, clearCart, applyCoupon,
  };
});
```

#### Pinia 插件系统

```javascript
// plugins/piniaLogger.js
export function piniaLogger({ store }) {
  store.$onAction(({ name, args, after, onError }) => {
    const startTime = Date.now();
    console.log(`[Pinia] Action "${store.$id}.${name}" started`, args);

    after((result) => {
      console.log(
        `[Pinia] Action "${store.$id}.${name}" finished in ${Date.now() - startTime}ms`,
        result
      );
    });

    onError((error) => {
      console.error(`[Pinia] Action "${store.$id}.${name}" failed`, error);
    });
  });

  // 监听状态变化
  store.$subscribe((mutation, state) => {
    console.log(`[Pinia] "${store.$id}" state changed`, mutation.type);
  });
}

// 持久化插件
export function piniaPersist({ store }) {
  const savedState = localStorage.getItem(`pinia-${store.$id}`);
  if (savedState) {
    store.$patch(JSON.parse(savedState));
  }

  store.$subscribe((mutation, state) => {
    localStorage.setItem(`pinia-${store.$id}`, JSON.stringify(state));
  });
}

// 注册插件
const pinia = createPinia();
pinia.use(piniaLogger);
pinia.use(piniaPersist);
```

#### 在 Vue 组件中使用

```html
{% raw %}
<template>
  <div class="cart">
    <h2>购物车 ({{ cartStore.totalItems }} 件)</h2>
    <ul>
      <li v-for="item in cartStore.items" :key="item.id">
        {{ item.name }} × {{ item.quantity }} = ¥{{ item.price * item.quantity }}
        <button @click="cartStore.removeItem(item.id)">移除</button>
      </li>
    </ul>
    <div class="summary">
      <p>小计: ¥{{ cartStore.subtotal }}</p>
      <p v-if="cartStore.discount">优惠: -¥{{ cartStore.discount }}</p>
      <p class="total">合计: ¥{{ cartStore.total }}</p>
    </div>
  </div>
</template>
{% endraw %}

<script setup>
import { useCartStore } from '@/stores/cart';
import { storeToRefs } from 'pinia';

const cartStore = useCartStore();

// 如果需要解构且保持响应性
const { items, totalItems, total } = storeToRefs(cartStore);
// 注意：actions 可以直接解构，不需要 storeToRefs
const { addItem, removeItem } = cartStore;
</script>
```

### 4.3 Vue 组合式函数作为轻量状态管理

对于简单场景，Vue 3 的组合式函数本身就是强大的状态管理方案：

```javascript
// composables/useAuth.js
import { ref, computed, readonly } from 'vue';

// 模块级别的状态（单例，所有组件共享）
const user = ref(null);
const token = ref(localStorage.getItem('token'));
const loading = ref(false);

export function useAuth() {
  const isAuthenticated = computed(() => !!token.value);
  const userName = computed(() => user.value?.name ?? 'Guest');

  async function login(credentials) {
    loading.value = true;
    try {
      const res = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
      });
      const data = await res.json();
      user.value = data.user;
      token.value = data.token;
      localStorage.setItem('token', data.token);
    } finally {
      loading.value = false;
    }
  }

  function logout() {
    user.value = null;
    token.value = null;
    localStorage.removeItem('token');
  }

  return {
    user: readonly(user),
    token: readonly(token),
    loading: readonly(loading),
    isAuthenticated,
    userName,
    login,
    logout,
  };
}
```

---

## 五、跨框架方案

### 5.1 Signals

Signals 是一种细粒度的响应式原语，正在被多个框架采纳，TC39 也有相关提案。

#### Preact Signals

```javascript
import { signal, computed, effect, batch } from '@preact/signals';

// 创建 Signal（类似 ref）
const count = signal(0);
const name = signal('World');

// 计算 Signal
const greeting = computed(() => `Hello, ${name.value}! Count: ${count.value}`);

// 副作用
const dispose = effect(() => {
  console.log(greeting.value);
  // 自动追踪依赖：当 count 或 name 变化时重新执行
});

// 批量更新（避免中间状态触发重渲染）
batch(() => {
  count.value = 1;
  name.value = 'Preact';
});

// 在 Preact/React 组件中直接使用
function App() {
  return (
    <div>
      <p>{greeting}</p>
      <button onClick={() => count.value++}>+1</button>
    </div>
  );
}
```

#### Solid.js Signals

```javascript
import { createSignal, createMemo, createEffect, batch } from 'solid-js';

function Counter() {
  const [count, setCount] = createSignal(0);
  const [name, setName] = createSignal('Solid');

  // Memo（computed）
  const doubleCount = createMemo(() => count() * 2);

  // Effect
  createEffect(() => {
    console.log(`${name()} count is: ${count()}`);
  });

  return (
    <div>
      <p>{name()} Count: {count()} (Double: {doubleCount()})</p>
      <button onClick={() => setCount(c => c + 1)}>+1</button>
    </div>
  );
}
```

#### Angular Signals

```typescript
import { Component, signal, computed, effect } from '@angular/core';

@Component({
  selector: 'app-counter',
  template: `
    {% raw %}
    <div>
      <p>Count: {{ count() }} (Double: {{ doubleCount() }})</p>
      <button (click)="increment()">+1</button>
    </div>
    {% endraw %}
  `,
})
export class CounterComponent {
  count = signal(0);
  doubleCount = computed(() => this.count() * 2);

  constructor() {
    effect(() => {
      console.log('Count changed:', this.count());
    });
  }

  increment() {
    this.count.update(c => c + 1);
  }
}
```

#### TC39 Signals 提案

```javascript
// TC39 提案草案（Stage 1）——统一各框架的 Signal 原语
const counter = new Signal.State(0);
const isEven = new Signal.Computed(() => (counter.get() & 1) === 0);
const parity = new Signal.Computed(() => isEven.get() ? 'even' : 'odd');

// Watcher 用于调度副作用
const watcher = new Signal.subtle.Watcher(() => {
  // 当被观察的 signal 变化时被调用
  // 这里安排实际的副作用在微任务中执行
  queueMicrotask(processPending);
});

watcher.watch(parity);
counter.set(1);
```

### 5.2 RxJS 响应式状态管理

```javascript
import { BehaviorSubject, combineLatest, map, distinctUntilChanged } from 'rxjs';

class Store {
  constructor(initialState) {
    this._state$ = new BehaviorSubject(initialState);
  }

  get state$() {
    return this._state$.asObservable();
  }

  get state() {
    return this._state$.getValue();
  }

  select(selector) {
    return this._state$.pipe(
      map(selector),
      distinctUntilChanged()
    );
  }

  setState(partialState) {
    const currentState = this._state$.getValue();
    this._state$.next({
      ...currentState,
      ...(typeof partialState === 'function' ? partialState(currentState) : partialState),
    });
  }
}

// 使用
const store = new Store({
  users: [],
  filter: '',
  loading: false,
});

// 选择特定状态切片
const users$ = store.select((s) => s.users);
const filter$ = store.select((s) => s.filter);

// 组合派生状态
const filteredUsers$ = combineLatest([users$, filter$]).pipe(
  map(([users, filter]) =>
    users.filter((u) => u.name.toLowerCase().includes(filter.toLowerCase()))
  )
);
```

### 5.3 XState 状态机

XState 用有限状态机和状态图来建模复杂业务逻辑：

```javascript
import { createMachine, assign, interpret } from 'xstate';

// 定义认证状态机
const authMachine = createMachine({
  id: 'auth',
  initial: 'idle',
  context: {
    user: null,
    error: null,
    retryCount: 0,
  },
  states: {
    idle: {
      on: {
        LOGIN: 'authenticating',
      },
    },
    authenticating: {
      invoke: {
        id: 'loginService',
        src: (context, event) =>
          fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(event.credentials),
          }).then((r) => {
            if (!r.ok) throw new Error('Login failed');
            return r.json();
          }),
        onDone: {
          target: 'authenticated',
          actions: assign({
            user: (_, event) => event.data.user,
            error: null,
            retryCount: 0,
          }),
        },
        onError: {
          target: 'error',
          actions: assign({
            error: (_, event) => event.data.message,
            retryCount: (ctx) => ctx.retryCount + 1,
          }),
        },
      },
    },
    authenticated: {
      on: {
        LOGOUT: {
          target: 'idle',
          actions: assign({ user: null }),
        },
      },
    },
    error: {
      on: {
        RETRY: {
          target: 'authenticating',
          cond: (ctx) => ctx.retryCount < 3, // 最多重试 3 次
        },
        RESET: 'idle',
      },
    },
  },
});

// 在 React 中使用
import { useMachine } from '@xstate/react';

function LoginPage() {
  const [state, send] = useMachine(authMachine);

  if (state.matches('authenticated')) {
    return <Dashboard user={state.context.user} onLogout={() => send('LOGOUT')} />;
  }

  if (state.matches('authenticating')) {
    return <Spinner />;
  }

  return (
    <div>
      {state.matches('error') && (
        <p className="error">
          {state.context.error} (尝试 {state.context.retryCount}/3)
          <button onClick={() => send('RETRY')}>重试</button>
        </p>
      )}
      <LoginForm
        onSubmit={(credentials) => send({ type: 'LOGIN', credentials })}
      />
    </div>
  );
}
```

### 5.4 nanostores —— 框架无关的原子化方案

```javascript
import { atom, map, computed, onMount } from 'nanostores';

// 原子
const $count = atom(0);

// Map（类似对象状态）
const $profile = map({ name: '', email: '', avatar: '' });

// 计算
const $greeting = computed($profile, (profile) => `Hello, ${profile.name}`);

// 生命周期钩子——只在有订阅者时激活
const $currentUser = atom(null);
onMount($currentUser, () => {
  const unsubscribe = subscribeToUserChanges((user) => {
    $currentUser.set(user);
  });
  return unsubscribe; // 清理
});

// 在 React 中
import { useStore } from '@nanostores/react';

function Profile() {
  const profile = useStore($profile);
  return <p>{profile.name}</p>;
}

// 在 Vue 中
import { useStore } from '@nanostores/vue';

// 在 Svelte 中直接使用 $ 语法
// $: count = $count;
```

---

## 六、Server State 管理

### 6.1 TanStack Query（React Query）

#### 基本查询与缓存

```javascript
import {
  useQuery,
  useMutation,
  useQueryClient,
  QueryClient,
  QueryClientProvider,
} from '@tanstack/react-query';

// 配置 QueryClient
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 分钟内认为数据新鲜，不会自动 refetch
      gcTime: 1000 * 60 * 30,   // 30 分钟后垃圾回收（v5 重命名自 cacheTime）
      retry: 3,
      refetchOnWindowFocus: true,
    },
  },
});

// 查询 Hook
function TodoList() {
  const {
    data: todos,
    isLoading,
    isError,
    error,
    isFetching, // 背景 refetch 时为 true
    isStale,
  } = useQuery({
    queryKey: ['todos'],
    queryFn: async () => {
      const res = await fetch('/api/todos');
      if (!res.ok) throw new Error('Failed to fetch');
      return res.json();
    },
    select: (data) => data.sort((a, b) => b.createdAt - a.createdAt), // 数据转换
  });

  if (isLoading) return <Skeleton />;
  if (isError) return <ErrorDisplay message={error.message} />;

  return (
    <div>
      {isFetching && <RefreshIndicator />}
      {todos.map((todo) => (
        <TodoItem key={todo.id} todo={todo} />
      ))}
    </div>
  );
}

// 带参数的查询
function TodoDetail({ todoId }) {
  const { data: todo } = useQuery({
    queryKey: ['todos', todoId], // 依赖参数变化自动 refetch
    queryFn: () => fetchTodoById(todoId),
    enabled: !!todoId, // 条件查询
  });
  return todo ? <div>{todo.title}</div> : null;
}
```

#### 缓存失效与乐观更新

```javascript
function useCreateTodo() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (newTodo) =>
      fetch('/api/todos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newTodo),
      }).then((r) => r.json()),

    // 乐观更新
    onMutate: async (newTodo) => {
      // 1. 取消正在进行的 refetch（避免覆盖乐观数据）
      await queryClient.cancelQueries({ queryKey: ['todos'] });

      // 2. 保存当前状态的快照
      const previousTodos = queryClient.getQueryData(['todos']);

      // 3. 乐观写入
      queryClient.setQueryData(['todos'], (old) => [
        ...old,
        { ...newTodo, id: Date.now(), createdAt: new Date().toISOString() },
      ]);

      // 4. 返回快照以便回滚
      return { previousTodos };
    },

    onError: (err, newTodo, context) => {
      // 失败时回滚
      queryClient.setQueryData(['todos'], context.previousTodos);
    },

    onSettled: () => {
      // 无论成功失败，重新验证数据
      queryClient.invalidateQueries({ queryKey: ['todos'] });
    },
  });
}

// 使用
function AddTodoForm() {
  const createTodo = useCreateTodo();

  const handleSubmit = (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    createTodo.mutate({ title: formData.get('title') });
  };

  return (
    <form onSubmit={handleSubmit}>
      <input name="title" required />
      <button type="submit" disabled={createTodo.isPending}>
        {createTodo.isPending ? '添加中...' : '添加'}
      </button>
    </form>
  );
}
```

#### 无限滚动（Infinite Query）

```javascript
import { useInfiniteQuery } from '@tanstack/react-query';

function InfinitePostList() {
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
  } = useInfiniteQuery({
    queryKey: ['posts'],
    queryFn: async ({ pageParam = 1 }) => {
      const res = await fetch(`/api/posts?page=${pageParam}&limit=20`);
      return res.json();
    },
    getNextPageParam: (lastPage, allPages) => {
      return lastPage.length === 20 ? allPages.length + 1 : undefined;
    },
    initialPageParam: 1,
  });

  if (isLoading) return <Skeleton />;

  return (
    <div>
      {data.pages.flatMap((page) =>
        page.map((post) => <PostCard key={post.id} post={post} />)
      )}
      {hasNextPage && (
        <button onClick={() => fetchNextPage()} disabled={isFetchingNextPage}>
          {isFetchingNextPage ? '加载中...' : '加载更多'}
        </button>
      )}
    </div>
  );
}
```

### 6.2 SWR

SWR（stale-while-revalidate）是 Vercel 出品的数据获取库，理念来自 HTTP 缓存策略：

```javascript
import useSWR, { mutate, useSWRConfig } from 'swr';

const fetcher = (url) => fetch(url).then((r) => r.json());

function UserProfile({ userId }) {
  const { data, error, isLoading, isValidating, mutate: boundMutate } = useSWR(
    userId ? `/api/users/${userId}` : null, // null key 表示不请求
    fetcher,
    {
      revalidateOnFocus: true,
      revalidateOnReconnect: true,
      dedupingInterval: 2000, // 2 秒内去重
      refreshInterval: 30000, // 每 30 秒轮询
      onSuccess: (data) => console.log('Fetched:', data),
      onError: (error) => console.error('Error:', error),
    }
  );

  // 乐观更新
  const updateName = async (newName) => {
    await boundMutate(
      async (currentData) => {
        await fetch(`/api/users/${userId}`, {
          method: 'PATCH',
          body: JSON.stringify({ name: newName }),
        });
        return { ...currentData, name: newName };
      },
      {
        optimisticData: (current) => ({ ...current, name: newName }),
        rollbackOnError: true,
        revalidate: false,
      }
    );
  };

  if (isLoading) return <Skeleton />;
  if (error) return <Error message={error.message} />;

  return (
    <div>
      <h1>{data.name}</h1>
      {isValidating && <span>刷新中...</span>}
    </div>
  );
}
```

### 6.3 Apollo Client（GraphQL）

```javascript
import { gql, useQuery, useMutation } from '@apollo/client';

const GET_TODOS = gql`
  query GetTodos($filter: TodoFilter) {
    todos(filter: $filter) {
      id
      title
      completed
      createdAt
      author {
        id
        name
      }
    }
  }
`;

const ADD_TODO = gql`
  mutation AddTodo($input: AddTodoInput!) {
    addTodo(input: $input) {
      id
      title
      completed
    }
  }
`;

function TodoList() {
  const { loading, error, data } = useQuery(GET_TODOS, {
    variables: { filter: { completed: false } },
    pollInterval: 30000, // 30 秒轮询
    fetchPolicy: 'cache-and-network', // 先展示缓存，同时发请求更新
  });

  const [addTodo] = useMutation(ADD_TODO, {
    // 方式 1：直接更新缓存
    update(cache, { data: { addTodo } }) {
      const existing = cache.readQuery({ query: GET_TODOS });
      cache.writeQuery({
        query: GET_TODOS,
        data: { todos: [...existing.todos, addTodo] },
      });
    },
    // 方式 2：重新获取查询
    // refetchQueries: [{ query: GET_TODOS }],

    // 乐观更新
    optimisticResponse: {
      addTodo: {
        __typename: 'Todo',
        id: 'temp-id',
        title: '新待办',
        completed: false,
      },
    },
  });

  if (loading) return <Spinner />;
  if (error) return <p>Error: {error.message}</p>;

  return (
    <ul>
      {data.todos.map((todo) => (
        <li key={todo.id}>{todo.title} - by {todo.author.name}</li>
      ))}
    </ul>
  );
}
```

---

## 七、最佳实践与架构设计

### 7.1 状态范式化（Normalization）

大型应用中，嵌套的数据结构会导致更新困难和数据冗余。范式化（类似数据库范式）可以解决这个问题：

```javascript
// 反模式：嵌套结构
const denormalized = {
  posts: [
    {
      id: 1,
      title: '文章标题',
      author: { id: 101, name: 'Alice' }, // 重复存储！
      comments: [
        { id: 201, text: '评论1', author: { id: 102, name: 'Bob' } },
        { id: 202, text: '评论2', author: { id: 101, name: 'Alice' } }, // 重复！
      ],
    },
  ],
};

// 最佳实践：范式化结构
const normalized = {
  entities: {
    users: {
      101: { id: 101, name: 'Alice' },
      102: { id: 102, name: 'Bob' },
    },
    posts: {
      1: { id: 1, title: '文章标题', authorId: 101, commentIds: [201, 202] },
    },
    comments: {
      201: { id: 201, text: '评论1', authorId: 102, postId: 1 },
      202: { id: 202, text: '评论2', authorId: 101, postId: 1 },
    },
  },
  result: { postIds: [1] },
};
```

#### 使用 normalizr 库

```javascript
import { normalize, schema } from 'normalizr';

const userSchema = new schema.Entity('users');
const commentSchema = new schema.Entity('comments', {
  author: userSchema,
});
const postSchema = new schema.Entity('posts', {
  author: userSchema,
  comments: [commentSchema],
});

// API 返回的嵌套数据
const apiResponse = {
  id: 1,
  title: '文章',
  author: { id: 101, name: 'Alice' },
  comments: [
    { id: 201, text: '评论', author: { id: 102, name: 'Bob' } },
  ],
};

const normalizedData = normalize(apiResponse, postSchema);
// 结果：
// {
//   entities: { users: {...}, comments: {...}, posts: {...} },
//   result: 1
// }
```

#### RTK 的 createEntityAdapter

```javascript
import { createEntityAdapter, createSlice } from '@reduxjs/toolkit';

const todosAdapter = createEntityAdapter({
  selectId: (todo) => todo.id,
  sortComparer: (a, b) => b.createdAt.localeCompare(a.createdAt),
});

const todosSlice = createSlice({
  name: 'todos',
  initialState: todosAdapter.getInitialState({
    loading: false,
    filter: 'all',
  }),
  reducers: {
    addTodo: todosAdapter.addOne,
    updateTodo: todosAdapter.updateOne,
    removeTodo: todosAdapter.removeOne,
    setTodos: todosAdapter.setAll,
    upsertTodos: todosAdapter.upsertMany,
  },
});

// 自动生成的 selector
export const {
  selectAll: selectAllTodos,
  selectById: selectTodoById,
  selectIds: selectTodoIds,
  selectTotal: selectTodoTotal,
} = todosAdapter.getSelectors((state) => state.todos);
```

### 7.2 状态粒度设计

```
┌─────────────────────────────────────────────────────┐
│                    粒度设计金字塔                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│     ▲  全局状态（Global State）                      │
│    ╱ ╲  认证、主题、国际化、通知                       │
│   ╱   ╲  工具：Zustand / Pinia / Redux              │
│  ╱─────╲                                            │
│  ╱       ╲                                          │
│ ╱ 服务端状态 ╲ 缓存、同步、失效                        │
│╱  (Server)  ╲ 工具：TanStack Query / SWR            │
│╲─────────────╱                                      │
│ ╲           ╱                                       │
│  ╲ 共享状态  ╱ 多组件共享的业务数据                     │
│   ╲(Shared)╱  工具：Context / 组合式函数               │
│    ╲──────╱                                         │
│     ╲    ╱                                          │
│      ╲  ╱  局部状态（Local State）                    │
│       ╲╱   表单值、UI toggle、动画                    │
│        ▼   工具：useState / ref                      │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**核心原则**：
- **就近原则**：状态应该尽可能靠近使用它的组件。
- **按需提升**：只有当多个不相邻组件需要共享时，才将状态提升到更高层级。
- **分类管理**：不要把所有状态都塞进一个全局 store。

### 7.3 性能优化策略

#### React 中避免不必要的重渲染

```javascript
// Zustand：使用 selector 只订阅需要的状态切片
function UserName() {
  // 只有 name 变化时才重渲染，count 变化不影响
  const name = useStore((state) => state.name);
  return <span>{name}</span>;
}

// 对于复杂 selector，使用 shallow 比较
import { shallow } from 'zustand/shallow';

function UserInfo() {
  const { name, email } = useStore(
    (state) => ({ name: state.name, email: state.email }),
    shallow // 浅比较对象的每个属性
  );
  return <div>{name} - {email}</div>;
}

// Context 优化：拆分 Context + useMemo
const ThemeContext = React.createContext();
const ThemeDispatchContext = React.createContext();

function ThemeProvider({ children }) {
  const [theme, setTheme] = React.useState('light');

  // 将"读"和"写"分到不同的 Context
  const themeValue = React.useMemo(() => ({ theme }), [theme]);
  const dispatchValue = React.useMemo(() => ({ setTheme }), []);

  return (
    <ThemeContext.Provider value={themeValue}>
      <ThemeDispatchContext.Provider value={dispatchValue}>
        {children}
      </ThemeDispatchContext.Provider>
    </ThemeContext.Provider>
  );
}
```

#### Vue 中的性能优化

```javascript
// Pinia：使用 storeToRefs 避免解构丢失响应性
const store = useUserStore();
const { name, email } = storeToRefs(store); // 保持响应性
const { updateUser } = store; // actions 可以直接解构

// 大列表优化：使用 shallowRef
import { shallowRef, triggerRef } from 'vue';

const largeList = shallowRef([]);
function updateItem(index, newItem) {
  largeList.value[index] = newItem;
  triggerRef(largeList); // 手动触发更新
}
```

---

## 八、高频面试题精选

### 题目 1：Redux 单向数据流是如何工作的？

**参考答案**：

Redux 的单向数据流遵循严格的 `View → Action → Reducer → Store → View` 循环：

1. 用户在视图层（View）触发交互。
2. 视图层 dispatch 一个 Action（描述"发生了什么"的普通对象）。
3. Store 将当前 State 和 Action 传给 Reducer。
4. Reducer 是纯函数，基于旧 State 和 Action 计算出新 State 并返回。
5. Store 更新状态，通知所有订阅的组件。
6. 组件根据新 State 重新渲染。

这种单向数据流的好处是：状态变化可预测、易于调试（时间旅行）、变更历史清晰。

---

### 题目 2：为什么 Redux 要求 Reducer 是纯函数？

**参考答案**：

纯函数意味着：相同输入必定产生相同输出，且没有副作用。这带来以下优势：

- **可预测性**：给定相同的 state 和 action，reducer 总是返回相同的新 state。
- **时间旅行调试**：可以回放和撤销 action，因为每次 reducer 调用都是独立的。
- **可测试性**：不依赖外部环境，易于编写单元测试。
- **性能优化**：Redux 通过引用比较（`===`）判断状态是否变化，纯函数保证了不变的数据保持原引用。
- **Hot Reloading**：可以热替换 reducer 而不丢失状态。

---

### 题目 3：Context API 能替代 Redux 吗？

**参考答案**：

不能完全替代，两者解决的问题不同：

**Context API 适合**：
- 低频变化的全局数据（主题、语言、认证信息）。
- 避免 props drilling 的依赖注入场景。

**Context API 的局限**：
- **性能问题**：Context value 变化会导致所有消费者组件重渲染，即使组件只用了 value 中的一个属性。需要手动拆分 Context 或 memo 优化。
- **缺乏中间件机制**：无法像 Redux 那样用中间件统一处理日志、异步、持久化等横切关注点。
- **缺乏 DevTools**：没有内置的时间旅行调试工具。
- **高频更新性能差**：频繁变化的状态（如拖拽坐标、输入框实时值）不适合放在 Context 中。

**现代推荐**：对于中小型应用，Context + useReducer 足够；中大型应用推荐 Zustand / Jotai + TanStack Query 的组合。

---

### 题目 4：Zustand 和 Redux 的核心区别是什么？

**参考答案**：

- **API 简洁度**：Zustand 不需要 action creators、action types、switch/case reducer，一个函数搞定。
- **样板代码**：Redux（即便是 RTK）仍比 Zustand 需要更多模板代码。
- **脱离 React**：Zustand 的 store 天然可以在 React 组件外使用（定时器、WebSocket 回调等），Redux 也可以但更常与 React 绑定。
- **包体积**：Zustand ~1KB vs Redux + React-Redux ~10KB+。
- **中间件**：Redux 中间件生态更成熟（saga, thunk, persist 等），Zustand 的中间件更简洁但功能同样强大。
- **不可变性**：Redux 通过 Immer（RTK 内置）实现，Zustand 可选使用 immer 中间件。
- **适用场景**：大团队、需要严格约束的架构 → Redux；中小团队、追求效率 → Zustand。

---

### 题目 5：Pinia 相比 Vuex 有哪些改进？

**参考答案**：

1. **取消 Mutations**：Vuex 中必须通过 mutation 修改状态，Pinia 中可以在 action 中直接修改，减少了样板代码。
2. **TypeScript 支持**：Pinia 的类型推导是开箱即用的，Vuex 需要大量类型标注。
3. **模块化**：Vuex 使用深层嵌套的 modules，Pinia 采用扁平化的 store，每个 store 独立定义，store 间可以互相引用。
4. **支持 Composition API**：Pinia 的 Setup Store 可以直接使用 `ref`、`computed`、`watch` 等组合式 API。
5. **自动代码拆分**：Pinia store 天然支持 tree-shaking 和动态导入。
6. **更轻量**：~1.5KB vs ~6KB。

---

### 题目 6：什么是原子化状态管理？Jotai 的优势是什么？

**参考答案**：

原子化状态管理是自底向上的方案：每个最小粒度的状态是一个"原子"（atom），更复杂的状态通过组合/派生原子得到。

Jotai 的优势：
- **按需渲染**：组件只订阅自己使用的原子，粒度极细。
- **无需 Provider**（v2+）：全局可用。
- **天然支持异步**：异步原子配合 Suspense，声明式处理加载状态。
- **极小体积**：~2KB。
- **消除不必要的重渲染**：不像 Context 那样对整棵子树 re-render。

---

### 题目 7：手写一个简化版的 Zustand `create` 函数

**参考答案**：

见 [3.1 Zustand 核心原理](#31-zustand) 的 `createStore` 实现。核心是发布订阅 + 闭包持有状态 + React useSyncExternalStore 绑定。

---

### 题目 8：TanStack Query 的 staleTime 和 gcTime 有什么区别？

**参考答案**：

- **staleTime**（新鲜时间）：数据从"新鲜"变为"过时"的时间。在 staleTime 内，即使组件重新挂载或窗口重新聚焦，也不会触发 refetch。默认值为 0（立即过时）。
- **gcTime**（垃圾回收时间，v5 之前叫 cacheTime）：数据从缓存中被移除的时间。当一个 query 没有任何活跃的观察者（所有使用该 query 的组件都卸载了）时，开始计时。超过 gcTime 后缓存被清除。默认值为 5 分钟。

**关键理解**：staleTime 决定"多久重新请求"，gcTime 决定"缓存保留多久"。设置合理的 staleTime 可以大幅减少不必要的网络请求。

---

### 题目 9：什么是乐观更新（Optimistic Update）？如何实现？

**参考答案**：

乐观更新是指在发起变更请求后，不等待服务器响应，立即在 UI 上展示预期的结果。如果请求失败，再回滚到之前的状态。

实现步骤（以 TanStack Query 为例）：
1. **onMutate**：取消正在进行的相关查询，保存当前状态快照，乐观写入缓存。
2. **onError**：请求失败时，用快照回滚。
3. **onSettled**：无论成败，都重新验证（invalidate）相关查询以确保数据一致。

这种模式让用户感知到"即时"的操作反馈，提升用户体验。

---

### 题目 10：Signals 和 React 的 useState 有什么本质区别？

**参考答案**：

- **更新粒度**：useState 变化触发整个组件函数重新执行（re-render），Signals 可以精确到使用该 signal 的 DOM 节点更新，不需要组件级别的 re-render。
- **依赖追踪**：useState 没有自动依赖追踪，需要手动在 useEffect 的依赖数组中声明；Signals 自动追踪，computed/effect 中访问了哪个 signal 就自动订阅。
- **作用域**：useState 是组件级别的，Signals 天然是模块级别/全局的，跨组件共享更自然。
- **性能**：Signals 的细粒度更新在理论上比 React 的 Virtual DOM diff 更高效，尤其是大型列表场景。

---

### 题目 11：XState 状态机在什么场景下使用？

**参考答案**：

XState 适合有明确"状态"和"转换"的复杂业务流程：

- **多步骤表单/向导**：每一步是一个状态，有明确的前进/后退转换。
- **认证流程**：idle → authenticating → authenticated / error，状态转换有严格约束。
- **支付流程**：pending → processing → success / failed / refunding。
- **播放器**：idle → loading → playing → paused → ended。
- **任何需要防止"不可能状态"的场景**：比如 `isLoading: true` 且 `isError: true` 同时为真这种逻辑矛盾。

状态机的核心优势是 **让非法状态不可表示**（Make Impossible States Impossible）。

---

### 题目 12：如何设计一个大型应用的状态管理架构？

**参考答案**：

推荐的分层架构：

1. **UI 状态（Local State）**：useState / ref，不外传。
2. **共享 UI 状态（Shared UI State）**：Zustand / Pinia，如 sidebar 折叠、全局 modal。
3. **服务端缓存（Server Cache）**：TanStack Query / SWR / Apollo，接口数据的获取、缓存、同步。
4. **全局业务状态（Global Business State）**：Zustand / Pinia，如认证、用户偏好、购物车。
5. **URL 状态（URL State）**：React Router / Vue Router，分页、筛选条件等同步到 URL。
6. **表单状态（Form State）**：React Hook Form / VeeValidate / Formik，专业的表单管理。

关键原则：
- 每种状态用最合适的工具管理。
- Server State 和 Client State 分离。
- 状态就近存储，按需提升。
- 使用范式化避免数据冗余。

---

### 题目 13：什么是 Proxy-based 的状态管理？有什么优缺点？

**参考答案**：

Proxy-based 方案（Valtio、MobX、Vue 3 响应式系统）利用 ES6 Proxy 拦截对象的读写操作，自动追踪依赖和通知更新。

**优点**：
- 写法直觉（直接赋值 `state.count++`）。
- 自动依赖追踪，无需手动声明依赖。
- 精细化更新，只有读取了特定属性的组件才会更新。

**缺点**：
- Proxy 不支持 IE11（现在已不是问题）。
- 对原始值（string, number）无法直接代理，需要包裹在对象中。
- 调试时看到的是 Proxy 对象而非原始值，需要 devtools 支持。
- 某些情况下"隐式"的响应性可能导致不可预料的行为。

---

### 题目 14：Redux 中间件的洋葱模型是怎么实现的？

**参考答案**：

Redux 中间件的签名是 `store => next => action => { ... }`，三层柯里化。`applyMiddleware` 通过 `compose` 函数将多个中间件从右到左组合：

```
dispatch → middleware1 → middleware2 → middleware3 → 原始 dispatch
```

调用时从外到内进入（middleware1 → 2 → 3 → dispatch），`next(action)` 返回后从内到外执行后续逻辑（3 → 2 → 1）。这就形成了洋葱模型。本质上和 Koa 的中间件机制类似。

---

### 题目 15：如何解决 React Context 的性能问题？

**参考答案**：

1. **拆分 Context**：将高频变化的状态和低频变化的状态放到不同的 Context 中。
2. **State/Dispatch 分离**：将 state 和 setter/dispatch 分到两个 Context，只需要触发操作的组件不会因 state 变化而重渲染。
3. **使用 useMemo**：Provider 的 value 用 useMemo 包裹，避免父组件 re-render 导致新引用。
4. **React.memo**：对消费者组件使用 memo 包裹。
5. **use-context-selector**：第三方库，实现了类似 Zustand 的 selector 机制。
6. **考虑替代方案**：高频更新的状态直接用 Zustand / Jotai，它们天然支持 selector 精确订阅。

---

### 题目 16：TanStack Query 和 Redux 在数据获取场景下的对比？

**参考答案**：

| 维度 | Redux（传统方式） | TanStack Query |
|------|-------------------|----------------|
| 样板代码 | 大量（action/reducer/thunk/loading/error） | 极少，一个 useQuery 搞定 |
| 缓存 | 手动实现 | 内置，基于 query key 自动缓存 |
| 后台更新 | 手动实现 | stale-while-revalidate 自动后台刷新 |
| 去重 | 手动实现 | 自动去重（deduplication） |
| 垃圾回收 | 手动清理 | gcTime 自动回收 |
| 乐观更新 | 手动实现 | 内置 onMutate/onError/onSettled |
| 分页/无限滚动 | 手动实现 | useInfiniteQuery 开箱即用 |
| DevTools | Redux DevTools | React Query DevTools |
| 离线支持 | 需要额外配置 | 内置 offline 支持 |

**结论**：在数据获取场景下，TanStack Query 是更合适的工具。Redux 更适合管理纯客户端状态（UI 状态、业务逻辑状态）。两者可以共存。

---

### 题目 17：Vue 3 的 ref 和 reactive 在状态管理中应该如何选择？

**参考答案**：

- **ref**：适合原始值（string、number、boolean）和需要整体替换的对象。用 `.value` 访问。
- **reactive**：适合复杂对象/嵌套结构，不需要 `.value`，但不能整体替换（会丢失响应性）。

**Pinia 中的建议**：
- Setup Store 中推荐统一使用 `ref`，因为 `ref` 可以存储任何类型，且 `storeToRefs` 解构后仍然是 ref，心智模型一致。
- 避免在 reactive 中嵌套 ref，会增加理解成本。

---

> **总结**：现代前端状态管理的核心趋势是 **分层管理、职责单一、减少样板代码**。Client State 用 Zustand/Jotai/Pinia 等轻量工具，Server State 用 TanStack Query/SWR 等专业工具，复杂业务流程用 XState 状态机。选型时应结合团队规模、项目复杂度和技术栈综合考虑。

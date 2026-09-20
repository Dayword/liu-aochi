/**
 * 消消乐核心逻辑（纯函数，与 React 无关，可单独测试）。
 *
 * 设计参考开源「开心消消乐」：棋盘就是一个二维数组，所有规则都是数组操作。
 * 先交换、再用同一套检测函数判断有没有消除 —— 有则保留，无则换回去。
 */

export type Special = 'none' | 'line-h' | 'line-v' | 'bird'

export interface Cell {
  id: number
  type: number
  special: Special
}

export type Board = (Cell | null)[][]

let autoId = 1
const newCell = (type: number, special: Special = 'none'): Cell => ({
  id: autoId++,
  type,
  special,
})

const key = (r: number, c: number) => `${r},${c}`
const parse = (k: string): [number, number] => {
  const i = k.indexOf(',')
  return [Number(k.slice(0, i)), Number(k.slice(i + 1))]
}

const rand = (n: number) => Math.floor(Math.random() * n)

// ---------------------------------------------------------------- 棋盘生成

/** 生成「开局没有现成消除、且至少存在一步可行」的棋盘 */
export function createBoard(rows: number, cols: number, types: number): Board {
  for (let attempt = 0; attempt < 50; attempt++) {
    const board: Board = []
    for (let r = 0; r < rows; r++) {
      const row: (Cell | null)[] = []
      for (let c = 0; c < cols; c++) {
        // 避开会立刻形成三连的颜色，保证开局不是白送分
        const forbidden = new Set<number>()
        if (c >= 2 && row[c - 1]?.type === row[c - 2]?.type) forbidden.add(row[c - 1]!.type)
        if (r >= 2 && board[r - 1][c]?.type === board[r - 2][c]?.type) forbidden.add(board[r - 1][c]!.type)
        const pool: number[] = []
        for (let t = 0; t < types; t++) if (!forbidden.has(t)) pool.push(t)
        row.push(newCell(pool[rand(pool.length)]))
      }
      board.push(row)
    }
    if (hasValidMove(board)) return board
  }
  return createBoardFallback(rows, cols, types)
}

function createBoardFallback(rows: number, cols: number, types: number): Board {
  const board: Board = []
  for (let r = 0; r < rows; r++) {
    const row: (Cell | null)[] = []
    for (let c = 0; c < cols; c++) row.push(newCell(rand(types)))
    board.push(row)
  }
  return board
}

// ---------------------------------------------------------------- 匹配检测

export interface Run {
  cells: [number, number][]
  dir: 'h' | 'v'
  len: number
}

/** 扫描全盘，找出所有长度 >= 3 的横/竖连续同色段 */
export function findRuns(board: Board): Run[] {
  const runs: Run[] = []
  const rows = board.length
  const cols = board[0]?.length ?? 0

  // 横向
  for (let r = 0; r < rows; r++) {
    let start = 0
    for (let c = 1; c <= cols; c++) {
      const prev = board[r][c - 1]
      const cur = c < cols ? board[r][c] : null
      if (!(prev && cur && prev.type === cur.type)) {
        const len = c - start
        if (len >= 3 && prev) {
          const cells: [number, number][] = []
          for (let i = 0; i < len; i++) cells.push([r, start + i])
          runs.push({ cells, dir: 'h', len })
        }
        start = c
      }
    }
  }
  // 纵向
  for (let c = 0; c < cols; c++) {
    let start = 0
    for (let r = 1; r <= rows; r++) {
      const prev = board[r - 1]?.[c]
      const cur = r < rows ? board[r]?.[c] : null
      if (!(prev && cur && prev.type === cur.type)) {
        const len = r - start
        if (len >= 3 && prev) {
          const cells: [number, number][] = []
          for (let i = 0; i < len; i++) cells.push([start + i, c])
          runs.push({ cells, dir: 'v', len })
        }
        start = r
      }
    }
  }
  return runs
}

// ---------------------------------------------------------------- 特殊宝石

/** 把被波及到的特殊宝石效果展开进待消除集合（会连锁触发） */
function expandSpecials(board: Board, set: Set<string>): void {
  const rows = board.length
  const cols = board[0]?.length ?? 0
  const queue = [...set]
  while (queue.length) {
    const [r, c] = parse(queue.shift()!)
    const cell = board[r]?.[c]
    if (!cell || cell.special === 'none') continue
    const added: string[] = []
    if (cell.special === 'line-h') {
      for (let i = 0; i < cols; i++) added.push(key(r, i))
    } else if (cell.special === 'line-v') {
      for (let i = 0; i < rows; i++) added.push(key(i, c))
    } else if (cell.special === 'bird') {
      // 魔力鸟：清空全盘同色
      for (let i = 0; i < rows; i++)
        for (let j = 0; j < cols; j++) if (board[i]?.[j]?.type === cell.type) added.push(key(i, j))
    }
    for (const k of added) {
      if (!set.has(k)) {
        set.add(k)
        queue.push(k)
      }
    }
  }
}

export interface ClearResult {
  board: Board
  cleared: number
  specialsCreated: number
  /** 本次被消除的格子坐标（r,c），供前端做消除动画 */
  clearedCells: [number, number][]
}

/**
 * 执行一次消除（不含下落补充）。
 * 4 连 → 生成直线宝石；5 连及以上 → 生成魔力鸟。生成位置取该段中点，
 * 且该格不被消除（它变成特殊宝石留在盘面上）。
 */
export function resolveOnce(board: Board): ClearResult | null {
  const runs = findRuns(board)
  if (!runs.length) return null

  const toClear = new Set<string>()
  const spawns = new Map<string, { type: number; special: Special }>()

  for (const run of runs) {
    let cells = run.cells
    if (run.len >= 5 || run.len === 4) {
      const mid = run.cells[Math.floor(run.cells.length / 2)]
      const src = board[mid[0]]?.[mid[1]]
      if (src) {
        const special: Special = run.len >= 5 ? 'bird' : run.dir === 'h' ? 'line-h' : 'line-v'
        spawns.set(key(mid[0], mid[1]), { type: src.type, special })
        cells = cells.filter(([r, c]) => !(r === mid[0] && c === mid[1]))
      }
    }
    for (const [r, c] of cells) toClear.add(key(r, c))
  }

  expandSpecials(board, toClear)
  for (const k of spawns.keys()) toClear.delete(k)

  const next = board.map((row) => row.slice())
  const clearedCells: [number, number][] = []
  for (const k of toClear) {
    const [r, c] = parse(k)
    if (next[r]?.[c]) {
      next[r][c] = null
      clearedCells.push([r, c])
    }
  }
  const cleared = clearedCells.length
  for (const [k, sp] of spawns) {
    const [r, c] = parse(k)
    const existing = next[r]?.[c]
    next[r][c] = existing ? { ...existing, special: sp.special } : newCell(sp.type, sp.special)
  }
  return { board: next, cleared, specialsCreated: spawns.size, clearedCells }
}

// ---------------------------------------------------------------- 下落与补充

/** 空位上方的宝石下落，顶部补新宝石 */
export function collapse(board: Board, types: number): Board {
  const rows = board.length
  const cols = board[0]?.length ?? 0
  const next = board.map((row) => row.slice())
  for (let c = 0; c < cols; c++) {
    let write = rows - 1
    for (let r = rows - 1; r >= 0; r--) {
      const cell = next[r][c]
      if (cell) {
        next[write][c] = cell
        if (write !== r) next[r][c] = null
        write--
      }
    }
    for (let r = write; r >= 0; r--) next[r][c] = newCell(rand(types))
  }
  return next
}

// ---------------------------------------------------------------- 死局检测

export function hasValidMove(board: Board): boolean {
  const rows = board.length
  const cols = board[0]?.length ?? 0
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      if (!board[r][c]) continue
      for (const [dr, dc] of [
        [0, 1],
        [1, 0],
      ]) {
        const r2 = r + dr
        const c2 = c + dc
        if (r2 >= rows || c2 >= cols || !board[r2][c2]) continue
        const a = board[r][c]
        board[r][c] = board[r2][c2]
        board[r2][c2] = a
        const ok = findRuns(board).length > 0
        const b = board[r][c]
        board[r][c] = board[r2][c2]
        board[r2][c2] = b
        if (ok) return true
      }
    }
  }
  return false
}

/** 死局时重排：保证重排后既没有现成消除，也至少有一 步可走 */
export function shuffleBoard(board: Board): Board {
  const rows = board.length
  const cols = board[0]?.length ?? 0
  const flat: Cell[] = []
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) if (board[r][c]) flat.push(board[r][c]!)
  for (let attempt = 0; attempt < 100; attempt++) {
    for (let i = flat.length - 1; i > 0; i--) {
      const j = rand(i + 1)
      const t = flat[i]
      flat[i] = flat[j]
      flat[j] = t
    }
    const next: Board = []
    let k = 0
    for (let r = 0; r < rows; r++) {
      const row: (Cell | null)[] = []
      for (let c = 0; c < cols; c++) row.push(flat[k++] ?? null)
      next.push(row)
    }
    if (findRuns(next).length === 0 && hasValidMove(next)) return next
  }
  return board
}

// ---------------------------------------------------------------- 对外组合操作

export function swapCells(board: Board, a: [number, number], b: [number, number]): Board {
  const next = board.map((row) => row.slice())
  const tmp = next[a[0]][a[1]]
  next[a[0]][a[1]] = next[b[0]][b[1]]
  next[b[0]][b[1]] = tmp
  return next
}

export function isAdjacent(a: [number, number], b: [number, number]): boolean {
  return Math.abs(a[0] - b[0]) + Math.abs(a[1] - b[1]) === 1
}

/** 把「交换后能否消除」的判断收敛到一个函数：能则回传新盘，不能则回传 null */
export function trySwap(
  board: Board,
  a: [number, number],
  b: [number, number],
): Board | null {
  if (!isAdjacent(a, b)) return null
  const swapped = swapCells(board, a, b)
  return findRuns(swapped).length > 0 ? swapped : null
}

/** 完整跑完一次连锁（消除 → 下落 → 再检测），返回累计数据 */
export function resolveCascade(
  board: Board,
  types: number,
): { board: Board; steps: number; cleared: number; score: number } {
  let cur = board
  let steps = 0
  let cleared = 0
  let score = 0
  for (;;) {
    const res = resolveOnce(cur)
    if (!res) break
    steps++
    cleared += res.cleared
    // 连击倍率：第 1 段 x1，第 2 段 x2 …… 这是这类游戏主要的爽点来源
    score += res.cleared * 10 * steps
    cur = collapse(res.board, types)
  }
  return { board: cur, steps, cleared, score }
}

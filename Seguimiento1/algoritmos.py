# Proyecto/Algoritmos/algoritmos.py
from math import ceil
from typing import List, Callable, Any

def _maybe_reverse(arr, reverse):
    if reverse:
        arr.reverse()
    return arr

# ======================================================
# 1. TimSort (versión educativa simplificada)
# ======================================================

def _binary_insertion(arr, left, right, key):
    for i in range(left + 1, right + 1):
        x = arr[i]
        kx = key(x)
        lo, hi = left, i
        while lo < hi:
            mid = (lo + hi) // 2
            if key(arr[mid]) <= kx:
                lo = mid + 1
            else:
                hi = mid
        j = i
        while j > lo:
            arr[j] = arr[j - 1]
            j -= 1
        arr[lo] = x

def _merge(left, right, key):
    i = j = 0
    res = []
    while i < len(left) and j < len(right):
        if key(left[i]) <= key(right[j]):
            res.append(left[i]); i += 1
        else:
            res.append(right[j]); j += 1
    res.extend(left[i:])
    res.extend(right[j:])
    return res

def timsort(data: List[Any], key: Callable = lambda x: x, reverse: bool = False) -> List[Any]:
    arr = data[:]
    n = len(arr)
    if n < 2:
        return _maybe_reverse(arr, reverse)
    MIN_RUN = 32
    runs = []
    i = 0
    while i < n:
        run_start = i
        i += 1
        if i == n:
            runs.append((run_start, i - 1))
            break
        if key(arr[i]) >= key(arr[i - 1]):
            while i < n and key(arr[i]) >= key(arr[i - 1]):
                i += 1
        else:
            while i < n and key(arr[i]) < key(arr[i - 1]):
                i += 1
            arr[run_start:i] = reversed(arr[run_start:i])
        run_end = i - 1
        length = run_end - run_start + 1
        if length < MIN_RUN:
            ext_end = min(run_start + MIN_RUN - 1, n - 1)
            _binary_insertion(arr, run_start, ext_end, key)
            run_end = ext_end
            i = run_end + 1
        runs.append((run_start, run_end))
    pieces = [arr[s:e+1] for (s, e) in runs]
    while len(pieces) > 1:
        new_pieces = []
        for j in range(0, len(pieces), 2):
            if j + 1 < len(pieces):
                new_pieces.append(_merge(pieces[j], pieces[j+1], key))
            else:
                new_pieces.append(pieces[j])
        pieces = new_pieces
    res = pieces[0] if pieces else arr
    return _maybe_reverse(res, reverse)

# ======================================================
# 2. Comb Sort
# ======================================================
def comb_sort(data, key=lambda x: x, reverse=False):
    arr = data[:]
    gap = len(arr)
    shrink = 1.3
    swapped = True
    while gap > 1 or swapped:
        gap = int(gap / shrink)
        if gap < 1:
            gap = 1
        swapped = False
        for i in range(0, len(arr) - gap):
            if key(arr[i]) > key(arr[i + gap]):
                arr[i], arr[i + gap] = arr[i + gap], arr[i]
                swapped = True
    return _maybe_reverse(arr, reverse)

# ======================================================
# 3. Selection Sort
# ======================================================
def selection_sort(data, key=lambda x: x, reverse=False):
    arr = data[:]
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if key(arr[j]) < key(arr[min_idx]):
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return _maybe_reverse(arr, reverse)

# ======================================================
# 4. Tree Sort (BST)
# ======================================================
class _BSTNode:
    __slots__ = ("val", "left", "right")
    def __init__(self, val):
        self.val = val
        self.left = None
        self.right = None

def _bst_insert(node, val, key):
    if node is None:
        return _BSTNode(val)
    if key(val) < key(node.val):
        node.left = _bst_insert(node.left, val, key)
    else:
        node.right = _bst_insert(node.right, val, key)
    return node

def _bst_inorder(node, out):
    if not node:
        return
    _bst_inorder(node.left, out)
    out.append(node.val)
    _bst_inorder(node.right, out)

def tree_sort(data, key=lambda x: x, reverse=False):
    root = None
    for v in data:
        root = _bst_insert(root, v, key)
    out = []
    _bst_inorder(root, out)
    return _maybe_reverse(out, reverse)

# ======================================================
# 5. Pigeonhole Sort (enteros no negativos, rango pequeño)
# ======================================================
def pigeonhole_sort(data, key=lambda x: x, reverse=False):
    if not data:
        return []
    vals = [key(x) for x in data]
    if any((type(v) is not int) or (v < 0) for v in vals):
        raise ValueError("Pigeonhole sort requiere enteros >= 0.")
    mi, ma = min(vals), max(vals)
    size = ma - mi + 1
    holes = [[] for _ in range(size)]
    for x, v in zip(data, vals):
        holes[v - mi].append(x)
    out = []
    for bucket in holes:
        out.extend(bucket)
    return _maybe_reverse(out, reverse)

# ======================================================
# 6. Bucket Sort (floats en [0,1) normalizados)
# ======================================================
def bucket_sort(data, key=lambda x: x, reverse=False, buckets=10):
    if not data:
        return []
    vals = [key(x) for x in data]
    if any(not isinstance(v, (int, float)) for v in vals):
        raise ValueError("Bucket sort requiere numéricos.")
    vmin, vmax = min(vals), max(vals)
    rng = vmax - vmin if vmax != vmin else 1.0
    norm = [(v - vmin) / rng for v in vals]
    B = [[] for _ in range(buckets)]
    for x, nv in zip(data, norm):
        idx = int(nv * buckets)
        if idx == buckets: idx = buckets - 1
        B[idx].append(x)
    def ins_sort(arr, key):
        for i in range(1, len(arr)):
            y = arr[i]; ky = key(y)
            j = i - 1
            while j >= 0 and key(arr[j]) > ky:
                arr[j + 1] = arr[j]; j -= 1
            arr[j + 1] = y
        return arr
    out = []
    for b in B:
        out.extend(ins_sort(b, key))
    return _maybe_reverse(out, reverse)

# ======================================================
# 7. QuickSort
# ======================================================
def quick_sort(data, key=lambda x: x, reverse=False):
    arr = data[:]
    def _qs(lo, hi):
        if lo >= hi: return
        pivot = key(arr[(lo + hi) // 2])
        i, j = lo, hi
        while i <= j:
            while key(arr[i]) < pivot: i += 1
            while key(arr[j]) > pivot: j -= 1
            if i <= j:
                arr[i], arr[j] = arr[j], arr[i]
                i += 1; j -= 1
        if lo < j: _qs(lo, j)
        if i < hi: _qs(i, hi)
    _qs(0, len(arr) - 1)
    return _maybe_reverse(arr, reverse)

# ======================================================
# 8. HeapSort
# ======================================================
def heap_sort(data, key=lambda x: x, reverse=False):
    arr = data[:]
    n = len(arr)
    def heapify(n, i):
        largest = i
        l = 2*i + 1
        r = 2*i + 2
        if l < n and key(arr[l]) > key(arr[largest]): largest = l
        if r < n and key(arr[r]) > key(arr[largest]): largest = r
        if largest != i:
            arr[i], arr[largest] = arr[largest], arr[i]
            heapify(n, largest)
    for i in range(n//2 - 1, -1, -1):
        heapify(n, i)
    for i in range(n - 1, 0, -1):
        arr[0], arr[i] = arr[i], arr[0]
        heapify(i, 0)
    return _maybe_reverse(arr, reverse)

# ======================================================
# 9. Bitonic Sort (ideal n potencia de 2)
# ======================================================
def bitonic_sort(data, key=lambda x: x, reverse=False):
    arr = data[:]
    n = len(arr)
    if n == 0: return arr
    if n & (n - 1) != 0:
        return quick_sort(arr, key=key, reverse=reverse)
    def comp_swap(i, j, up):
        if (key(arr[i]) > key(arr[j])) == up:
            arr[i], arr[j] = arr[j], arr[i]
    def bitonic_merge(lo, cnt, up):
        if cnt > 1:
            k = cnt // 2
            for i in range(lo, lo + k):
                comp_swap(i, i + k, up)
            bitonic_merge(lo, k, up)
            bitonic_merge(lo + k, k, up)
    def bitonic_rec(lo, cnt, up):
        if cnt > 1:
            k = cnt // 2
            bitonic_rec(lo, k, True)
            bitonic_rec(lo + k, k, False)
            bitonic_merge(lo, cnt, up)
    bitonic_rec(0, n, True)
    return _maybe_reverse(arr, reverse)

# ======================================================
# 10. Gnome Sort
# ======================================================
def gnome_sort(data, key=lambda x: x, reverse=False):
    arr = data[:]
    i = 0
    n = len(arr)
    while i < n:
        if i == 0 or key(arr[i]) >= key(arr[i - 1]):
            i += 1
        else:
            arr[i], arr[i - 1] = arr[i - 1], arr[i]
            i -= 1
    return _maybe_reverse(arr, reverse)

# ======================================================
# 11. Binary Insertion Sort
# ======================================================
def binary_insertion_sort(data, key=lambda x: x, reverse=False):
    arr = data[:]
    for i in range(1, len(arr)):
        x = arr[i]; kx = key(x)
        lo, hi = 0, i
        while lo < hi:
            mid = (lo + hi) // 2
            if key(arr[mid]) <= kx: lo = mid + 1
            else: hi = mid
        j = i
        while j > lo:
            arr[j] = arr[j - 1]; j -= 1
        arr[lo] = x
    return _maybe_reverse(arr, reverse)

# ======================================================
# 12. Radix Sort (enteros >= 0)
# ======================================================
def radix_sort(data, key=lambda x: x, reverse=False, base=10):
    arr = data[:]
    vals = [key(x) for x in arr]
    if any((type(v) is not int) or (v < 0) for v in vals):
        raise ValueError("Radix sort requiere enteros >= 0.")
    if not arr:
        return arr
    maxv = max(vals)
    exp = 1
    while maxv // exp > 0:
        buckets = [[] for _ in range(base)]
        for x in arr:
            v = key(x)
            d = (v // exp) % base
            buckets[d].append(x)
        i = 0
        for b in buckets:
            for x in b:
                arr[i] = x; i += 1
        exp *= base
    return _maybe_reverse(arr, reverse)

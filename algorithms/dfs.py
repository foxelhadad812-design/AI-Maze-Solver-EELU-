"""
Depth-First Search (DFS) algorithm implementation.

Characteristics:
- Uses a Python list as a LIFO Stack.
- Explores deeply along each branch before backtracking.
- Does NOT guarantee the shortest or optimal path.
- Demonstrates high path length variance and deeper exploration patterns.
"""

import time
from typing import List, Tuple, Dict, Set, Optional, Generator, Any


def dfs_solve(maze) -> Dict[str, Any]:
    """
    Execute Depth-First Search synchronously.
    
    Returns a dictionary containing:
        - 'path': List of (row, col) tuples from start to goal (empty list if no path)
        - 'visited_order': List of nodes in the order they were expanded
        - 'nodes_expanded': Integer count of expanded nodes
        - 'time_ms': Elapsed execution time in milliseconds
        - 'found': Boolean indicating if goal was reached
    """
    # نبدأ التوقيت ونحصل على نقطتي البداية والهدف.
    t0 = time.perf_counter()
    
    start = maze.start
    goal = maze.goal
    
    # لو البداية هي الهدف، نرجّع النتيجة مباشرة من غير بحث.
    if start == goal:
        t1 = time.perf_counter()
        return {
            'path': [start],
            'visited_order': [start],
            'nodes_expanded': 1,
            'time_ms': (t1 - t0) * 1000.0,
            'found': True
        }
    
    # المكدس LIFO يخرج آخر خلية أُضيفت؛ لذلك DFS يتعمق في فرع قبل الرجوع.
    stack: List[Tuple[int, int]] = [start]
    # discovered تمنع زيارة الخلية نفسها مرارًا، وparent يحفظ طريق الوصول لها.
    discovered: Set[Tuple[int, int]] = {start}
    parent: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start: None}
    visited_order: List[Tuple[int, int]] = []
    nodes_expanded = 0
    found = False
    
    while stack:
        # نأخذ آخر خلية أُضيفت إلى المكدس لفحصها الآن.
        current = stack.pop()
        nodes_expanded += 1
        visited_order.append(current)
        
        if current == goal:
            found = True
            break
        
        # نضيف الجيران غير المكتشفين؛ آخر جار يُضاف سيكون أول جار يُفحص.
        for neighbor in maze.get_neighbors(current[0], current[1]):
            if neighbor not in discovered:
                discovered.add(neighbor)
                parent[neighbor] = current
                stack.append(neighbor)
    
    # عند العثور على الهدف، نرجع عبر parent حتى البداية ثم نعكس المسار.
    path: List[Tuple[int, int]] = []
    if found:
        curr: Optional[Tuple[int, int]] = goal
        while curr is not None:
            path.append(curr)
            curr = parent.get(curr)
        path.reverse()
    
    # ننهي التوقيت ونعيد المسار وترتيب الفحص وعدد الخلايا والنتيجة.
    t1 = time.perf_counter()
    
    return {
        'path': path,
        'visited_order': visited_order,
        'nodes_expanded': nodes_expanded,
        'time_ms': (t1 - t0) * 1000.0,
        'found': found
    }


def dfs_generator(maze) -> Generator[Dict[str, Any], None, None]:
    """
    Step-by-step generator for Pygame UI visualization.
    Yields independent snapshots of search state at each step.
    
    State yielded:
        - 'current': (row, col) or None
        - 'expanded': Set of expanded (closed) nodes
        - 'frontier': Set of nodes currently in the stack
        - 'discovered': Set of all discovered nodes (expanded + frontier)
        - 'visited': Alias for expanded (closed set)
        - 'path': Final reconstructed path when found, else None
        - 'nodes_expanded': Integer count of nodes expanded so far
        - 'is_complete': Boolean indicating if search has finished
        - 'found': Boolean indicating if goal was found
    """
    # هذا المولد ينفذ DFS خطوة بخطوة حتى تعرض الواجهة حركة البحث.
    start = maze.start
    goal = maze.goal
    
    # إذا كانت البداية هي الهدف، نرسل لقطة نهائية فورًا.
    if start == goal:
        yield {
            'current': start,
            'expanded': {start},
            'frontier': set(),
            'discovered': {start},
            'visited': {start},
            'path': [start],
            'nodes_expanded': 1,
            'is_complete': True,
            'found': True
        }
        return

    # stack هو ترتيب البحث، والمجموعات تحفظ ما سيُعرض كحدود وزيارات.
    stack: List[Tuple[int, int]] = [start]
    discovered: Set[Tuple[int, int]] = {start}
    expanded_set: Set[Tuple[int, int]] = set()
    parent: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start: None}
    nodes_expanded = 0
    found = False
    
    while stack:
        # آخر خلية أُضيفت تُفحص أولًا، وهذا هو سلوك DFS العميق.
        current = stack.pop()
        expanded_set.add(current)
        nodes_expanded += 1
        
        if current == goal:
            found = True
            # وصلنا للهدف؛ نعيد بناء الطريق ونرسل لقطة نهائية للواجهة.
            path: List[Tuple[int, int]] = []
            curr: Optional[Tuple[int, int]] = goal
            while curr is not None:
                path.append(curr)
                curr = parent.get(curr)
            path.reverse()
            
            exp_snap = set(expanded_set)
            yield {
                'current': current,
                'expanded': exp_snap,
                'frontier': set(stack),
                'discovered': set(discovered),
                'visited': exp_snap,
                'path': path,
                'nodes_expanded': nodes_expanded,
                'is_complete': True,
                'found': True
            }
            return
        
        # نضيف الجيران الجدد للمكدس، ليكمل البحث في أحد الفروع.
        for neighbor in maze.get_neighbors(current[0], current[1]):
            if neighbor not in discovered:
                discovered.add(neighbor)
                parent[neighbor] = current
                stack.append(neighbor)
        
        # نرسل نسخة ثابتة من الخلايا المفحوصة مع حالة البحث الحالية.
        exp_snap = set(expanded_set)
        yield {
            'current': current,
            'expanded': exp_snap,
            'frontier': set(stack),
            'discovered': set(discovered),
            'visited': exp_snap,
            'path': None,
            'nodes_expanded': nodes_expanded,
            'is_complete': False,
            'found': False
        }
    
    # إذا فرغ المكدس من دون العثور على الهدف، فلا يوجد مسار.
    exp_snap = set(expanded_set)
    yield {
        'current': None,
        'expanded': exp_snap,
        'frontier': set(),
        'discovered': set(discovered),
        'visited': exp_snap,
        'path': [],
        'nodes_expanded': nodes_expanded,
        'is_complete': True,
        'found': False
    }

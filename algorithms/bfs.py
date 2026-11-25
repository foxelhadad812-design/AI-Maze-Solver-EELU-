"""
Breadth-First Search (BFS) algorithm implementation.

Characteristics:
- Uses collections.deque as a FIFO Queue.
- Explores the search space level-by-level (shallowest nodes first).
- Guarantees the shortest / optimal path in unweighted uniform-cost grids.
- Complete: will always find a path if one exists.
"""

import time
from collections import deque
from typing import List, Tuple, Dict, Set, Optional, Generator, Any


def bfs_solve(maze) -> Dict[str, Any]:
    """
    Execute Breadth-First Search synchronously.
    
    Returns a dictionary containing:
        - 'path': List of (row, col) tuples from start to goal (empty list if no path)
        - 'visited_order': List of nodes in the order they were expanded
        - 'nodes_expanded': Integer count of expanded nodes
        - 'time_ms': Elapsed execution time in milliseconds
        - 'found': Boolean indicating if goal was reached
    """
    # نبدأ التوقيت عشان نحسب مدة تنفيذ الخوارزمية.
    t0 = time.perf_counter()
    
    # نقطتا البداية والهدف محفوظتان كزوج (صف، عمود).
    start = maze.start
    goal = maze.goal
    
    # لو البداية هي الهدف، نرجّع المسار مباشرة من غير بحث.
    if start == goal:
        t1 = time.perf_counter()
        return {
            'path': [start],
            'visited_order': [start],
            'nodes_expanded': 1,
            'time_ms': (t1 - t0) * 1000.0,
            'found': True
        }
    
    # الطابور FIFO يخرج أول خلية دخلت؛ لذلك BFS يبحث مستوى بعد مستوى.
    queue: deque = deque([start])
    # discovered تمنع إضافة الخلية نفسها أكثر من مرة.
    discovered: Set[Tuple[int, int]] = {start}
    # parent يحفظ الخلية التي وصلنا منها لكل خلية، لإعادة بناء المسار لاحقًا.
    parent: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start: None}
    # visited_order يسجل ترتيب فحص الخلايا، والعداد يحسب عددها.
    visited_order: List[Tuple[int, int]] = []
    nodes_expanded = 0
    found = False
    
    while queue:
        # نأخذ أقدم خلية أُضيفت إلى الطابور لفحصها الآن.
        current = queue.popleft()
        nodes_expanded += 1
        visited_order.append(current)
        
        if current == goal:
            found = True
            break
        
        # نضيف الجيران المسموحين الذين لم نكتشفهم من قبل.
        for neighbor in maze.get_neighbors(current[0], current[1]):
            if neighbor not in discovered:
                discovered.add(neighbor)
                parent[neighbor] = current
                queue.append(neighbor)
    
    # نرجع من الهدف إلى البداية باستخدام parent، ثم نعكس الترتيب.
    path: List[Tuple[int, int]] = []
    if found:
        curr: Optional[Tuple[int, int]] = goal
        while curr is not None:
            path.append(curr)
            curr = parent.get(curr)
        path.reverse()
    
    # نسجل وقت النهاية ونجهز النتيجة التي تعرضها الواجهة أو تستخدمها المقارنة.
    t1 = time.perf_counter()
    
    return {
        'path': path,
        'visited_order': visited_order,
        'nodes_expanded': nodes_expanded,
        'time_ms': (t1 - t0) * 1000.0,
        'found': found
    }


def bfs_generator(maze) -> Generator[Dict[str, Any], None, None]:
    """
    Step-by-step generator for Pygame UI visualization.
    Yields independent snapshots of search state at each step.
    
    State yielded:
        - 'current': (row, col) or None
        - 'expanded': Set of expanded (closed) nodes
        - 'frontier': Set of nodes currently in the queue
        - 'discovered': Set of all discovered nodes (expanded + frontier)
        - 'visited': Alias for expanded (closed set)
        - 'path': Final reconstructed path when found, else None
        - 'nodes_expanded': Integer count of nodes expanded so far
        - 'is_complete': Boolean indicating if search has finished
        - 'found': Boolean indicating if goal was found
    """
    # هذا المولد ينفذ البحث خطوة بخطوة لتستطيع الواجهة رسم تقدمه.
    start = maze.start
    goal = maze.goal
    
    # نفس الحالة الخاصة: البداية هي الهدف، إذن المسار خلية واحدة.
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

    # queue هو ترتيب العمل الحقيقي، والمجموعات التالية لعرض الحالة على الشاشة.
    queue: deque = deque([start])
    discovered: Set[Tuple[int, int]] = {start}
    frontier_set: Set[Tuple[int, int]] = {start}
    expanded_set: Set[Tuple[int, int]] = set()
    parent: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start: None}
    nodes_expanded = 0
    found = False
    
    while queue:
        # الخلية تنتقل من frontier (لم تُفحص بعد) إلى expanded (تم فحصها).
        current = queue.popleft()
        frontier_set.discard(current)
        expanded_set.add(current)
        nodes_expanded += 1
        
        if current == goal:
            found = True
            # عند الوصول للهدف نعيد بناء أقصر مسار ونرسل آخر لقطة مكتملة.
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
                'frontier': set(frontier_set),
                'discovered': set(discovered),
                'visited': exp_snap,
                'path': path,
                'nodes_expanded': nodes_expanded,
                'is_complete': True,
                'found': True
            }
            return
        
        # نكتشف الجيران مرة واحدة ونضيفهم للطابور ولواجهة عرض frontier.
        for neighbor in maze.get_neighbors(current[0], current[1]):
            if neighbor not in discovered:
                discovered.add(neighbor)
                parent[neighbor] = current
                queue.append(neighbor)
                frontier_set.add(neighbor)
        
        # نرسل نسخًا من المجموعات حتى لا تتغير اللقطة بعد عرضها.
        exp_snap = set(expanded_set)
        yield {
            'current': current,
            'expanded': exp_snap,
            'frontier': set(frontier_set),
            'discovered': set(discovered),
            'visited': exp_snap,
            'path': None,
            'nodes_expanded': nodes_expanded,
            'is_complete': False,
            'found': False
        }
    
    # إذا فرغ الطابور، فهذا يعني أنه لا يوجد طريق يصل البداية بالهدف.
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

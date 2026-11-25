"""
A* Search Algorithm implementation.

Characteristics:
- Uses heapq as a Priority Queue.
- Informed search using Manhattan Distance heuristic: h(n) = |r1 - r2| + |c1 - c2|.
- Evaluation function: f(n) = g(n) + h(n), where:
    g(n) is the exact cost from Start to node n (edge cost = 1).
    h(n) is the admissible heuristic estimate from node n to Goal.
- Guarantees an optimal (shortest) path on uniform-cost grid graphs because
  Manhattan distance is admissible (never overestimates) and consistent.
"""

import time
import heapq
from typing import List, Tuple, Dict, Set, Optional, Generator, Any


def manhattan_distance(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    """تحسب عدد الخطوات الأفقية والرأسية بين خليتين من دون المرور عبر الجدران."""
    # المسافة هي فرق الصفوف زائد فرق الأعمدة، لأن الحركة لا تكون قطريًا.
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar_solve(maze) -> Dict[str, Any]:
    """
    Execute A* Search synchronously.
    
    Returns a dictionary containing:
        - 'path': List of (row, col) tuples from start to goal (empty list if no path)
        - 'visited_order': List of nodes in the order they were expanded
        - 'nodes_expanded': Integer count of expanded nodes
        - 'time_ms': Elapsed execution time in milliseconds
        - 'found': Boolean indicating if goal was reached
    """
    # نبدأ التوقيت ونحدد نقطة البداية والهدف.
    t0 = time.perf_counter()
    
    start = maze.start
    goal = maze.goal
    
    # لو البداية هي الهدف، لا نحتاج إلى تشغيل البحث.
    # إذا كانت البداية هي الهدف، لا توجد خطوات بحث مطلوبة.
    if start == goal:
        t1 = time.perf_counter()
        return {
            'path': [start],
            'visited_order': [start],
            'nodes_expanded': 1,
            'time_ms': (t1 - t0) * 1000.0,
            'found': True
        }
    
    # طابور الأولوية يرتب الخلايا حسب f = g + h؛ الأصغر يُفحص أولًا.
    # counter يكسر التعادل بين خلايا لها نفس الأولوية.
    counter = 0
    # g للبداية يساوي صفرًا، لذلك f الأولوية يساوي h فقط.
    start_h = manhattan_distance(start, goal)
    open_heap: List[Tuple[int, int, Tuple[int, int]]] = [(start_h, counter, start)]
    
    # g_score تكلفة الوصول الفعلية من البداية، وparent يحفظ الطريق.
    g_score: Dict[Tuple[int, int], int] = {start: 0}
    parent: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start: None}
    closed_set: Set[Tuple[int, int]] = set()
    visited_order: List[Tuple[int, int]] = []
    nodes_expanded = 0
    found = False
    
    # open_heap يحتوي الخلايا المنتظرة، وclosed_set الخلايا التي فُحصت.
    while open_heap:
        f, _, current = heapq.heappop(open_heap)
        
        # قد تظهر الخلية أكثر من مرة بالطابور؛ نتجاهلها إذا سبق فحصها.
        if current in closed_set:
            continue
        
        closed_set.add(current)
        nodes_expanded += 1
        visited_order.append(current)
        
        # نفحص الهدف عند إخراجه بأقل أولوية، وليس عند مجرد اكتشافه.
        if current == goal:
            found = True
            break
        
        # تكلفة الوصول الحالية، ومنها نحسب تكلفة كل جار.
        current_g = g_score[current]
        
        for neighbor in maze.get_neighbors(current[0], current[1]):
            if neighbor in closed_set:
                continue
            
            # كل حركة تكلف خطوة واحدة، لذا نضيف 1 إلى التكلفة الحالية.
            tentative_g = current_g + 1
            
            if tentative_g < g_score.get(neighbor, float('inf')):
                # وجدنا طريقًا أرخص للجار؛ نحفظه ونحسب h ثم f = g + h.
                g_score[neighbor] = tentative_g
                parent[neighbor] = current
                h = manhattan_distance(neighbor, goal)
                f_val = tentative_g + h
                counter += 1
                heapq.heappush(open_heap, (f_val, counter, neighbor))
    
    # نعيد تكوين الطريق من الهدف إلى البداية ثم نعكسه.
    path: List[Tuple[int, int]] = []
    if found:
        curr: Optional[Tuple[int, int]] = goal
        while curr is not None:
            path.append(curr)
            curr = parent.get(curr)
        path.reverse()
    
    # ننهي التوقيت ونعيد نتيجة البحث ومعلومات الأداء.
    t1 = time.perf_counter()
    
    return {
        'path': path,
        'visited_order': visited_order,
        'nodes_expanded': nodes_expanded,
        'time_ms': (t1 - t0) * 1000.0,
        'found': found
    }


def astar_generator(maze) -> Generator[Dict[str, Any], None, None]:
    """
    Step-by-step generator for Pygame UI visualization.
    Yields independent snapshots of search state at each step.
    
    State yielded:
        - 'current': (row, col) or None
        - 'expanded': Set of expanded (closed) nodes
        - 'frontier': Set of nodes currently in open queue
        - 'discovered': Set of all discovered nodes (expanded + frontier)
        - 'visited': Alias for expanded (closed set)
        - 'path': Final reconstructed path when found, else None
        - 'nodes_expanded': Integer count of nodes expanded so far
        - 'is_complete': Boolean indicating if search has finished
        - 'found': Boolean indicating if goal was found
    """
    # نسخة المولد تنفذ A* خطوة خطوة لإظهار التقدم داخل الواجهة.
    start = maze.start
    goal = maze.goal
    
    # نتعامل مع متاهة البداية والهدف فيها الخلية نفسها مباشرة.
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

    # نبدأ البداية في طابور الأولوية؛ g هي تكلفة البداية وh تقدير الهدف.
    counter = 0
    # نضع البداية في الطابور بأولوية h لأن تكلفة الوصول g تساوي صفرًا.
    start_h = manhattan_distance(start, goal)
    open_heap: List[Tuple[int, int, Tuple[int, int]]] = [(start_h, counter, start)]
    open_set: Set[Tuple[int, int]] = {start}
    discovered_set: Set[Tuple[int, int]] = {start}
    
    # هذه المجموعات لتتبع أفضل تكلفة والطريق والخلايا المنتظرة أو المفحوصة.
    g_score: Dict[Tuple[int, int], int] = {start: 0}
    parent: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start: None}
    closed_set: Set[Tuple[int, int]] = set()
    nodes_expanded = 0
    found = False
    
    while open_heap:
        f, _, current = heapq.heappop(open_heap)
        
        # نتجاهل أي نسخة قديمة من خلية سبق فحصها.
        if current in closed_set:
            continue
        
        closed_set.add(current)
        open_set.discard(current)
        nodes_expanded += 1
        
        if current == goal:
            found = True
            # وصلنا للهدف؛ نعيد بناء الطريق ونرسل الحالة النهائية للواجهة.
            path: List[Tuple[int, int]] = []
            curr: Optional[Tuple[int, int]] = goal
            while curr is not None:
                path.append(curr)
                curr = parent.get(curr)
            path.reverse()
            
            exp_snap = set(closed_set)
            yield {
                'current': current,
                'expanded': exp_snap,
                'frontier': set(open_set),
                'discovered': set(discovered_set),
                'visited': exp_snap,
                'path': path,
                'nodes_expanded': nodes_expanded,
                'is_complete': True,
                'found': True
            }
            return
        
        # نستخدم تكلفة الوصول الحالية لفحص تكلفة الجيران.
        current_g = g_score[current]
        
        # لكل جار، نقبل الطريق فقط إذا أعطى تكلفة وصول أفضل.
        for neighbor in maze.get_neighbors(current[0], current[1]):
            if neighbor in closed_set:
                continue
            
            tentative_g = current_g + 1  # تكلفة خطوة واحدة إلى الجار.
            
            if tentative_g < g_score.get(neighbor, float('inf')):
                g_score[neighbor] = tentative_g
                parent[neighbor] = current
                # نحدّث الطريق الأفضل، ثم نحسب الأولوية f = تكلفة الطريق + التقدير.
                h = manhattan_distance(neighbor, goal)
                f_val = tentative_g + h
                counter += 1
                heapq.heappush(open_heap, (f_val, counter, neighbor))
                open_set.add(neighbor)
                discovered_set.add(neighbor)
        
        # نرسل نسخ الحالة الحالية لتستطيع الواجهة رسم هذه الخطوة.
        exp_snap = set(closed_set)
        yield {
            'current': current,
            'expanded': exp_snap,
            'frontier': set(open_set),
            'discovered': set(discovered_set),
            'visited': exp_snap,
            'path': None,
            'nodes_expanded': nodes_expanded,
            'is_complete': False,
            'found': False
        }
    
    # إذا فرغ طابور الأولوية من دون الهدف، فلا يوجد طريق متاح.
    exp_snap = set(closed_set)
    yield {
        'current': None,
        'expanded': exp_snap,
        'frontier': set(),
        'discovered': set(discovered_set),
        'visited': exp_snap,
        'path': [],
        'nodes_expanded': nodes_expanded,
        'is_complete': True,
        'found': False
    }

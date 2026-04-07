"""Auto-placement algorithm for n8n workflow nodes.

Uses a tree-based layout: BFS from start node, placing children
at increasing Y levels. Branches split horizontally.
"""

from __future__ import annotations

X_SPACING = 300
Y_SPACING = 200
START_X = 250
START_Y = 300


def compute_layout(
    nodes: list[dict],
    connections: dict[str, list[str]],
    start_id: str,
) -> None:
    """Mutate node['position'] in-place with auto-computed coordinates.

    Args:
        nodes: List of n8n node dicts (must have 'id' and 'position').
        connections: Adjacency map {source_id: [target_ids]}.
        start_id: The ID of the entry node.
    """
    if not nodes:
        return

    node_map = {n["id"]: n for n in nodes}
    placed: set[str] = set()

    levels: list[list[str]] = []
    queue: list[tuple[str, int]] = [(start_id, 0)]
    visited: set[str] = set()

    while queue:
        node_id, level = queue.pop(0)
        if node_id in visited or node_id not in node_map:
            continue
        visited.add(node_id)

        while len(levels) <= level:
            levels.append([])
        levels[level].append(node_id)

        for child_id in connections.get(node_id, []):
            if child_id not in visited:
                queue.append((child_id, level + 1))

    for level_idx, level_nodes in enumerate(levels):
        level_width = len(level_nodes) * X_SPACING
        start_x = START_X - level_width // 2 + X_SPACING // 2

        for node_idx, node_id in enumerate(level_nodes):
            if node_id in node_map:
                node_map[node_id]["position"] = [
                    start_x + node_idx * X_SPACING,
                    START_Y + level_idx * Y_SPACING,
                ]
                placed.add(node_id)

    next_y = START_Y + len(levels) * Y_SPACING
    for node in nodes:
        if node["id"] not in placed:
            node["position"] = [START_X, next_y]
            next_y += Y_SPACING

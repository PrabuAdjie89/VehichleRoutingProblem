from .utils import calc_cost, skipped_optional

def solve_nearest_insert(data, matrix):
    n = len(matrix); depot = data["depot"]
    mandatory = {i for i in range(n) if i != depot and data["node_types"][i] == "Mandatory"}
    optional = {i for i in range(n) if i != depot and data["node_types"][i] == "Optional"}
    candidates = mandatory | optional
    if not candidates: return None

    # Start with a mandatory node when possible; otherwise the closest optional node.
    start_set = mandatory if mandatory else optional
    first = min(start_set, key=lambda x: matrix[depot][x])
    route = [depot, first, depot]
    total_load = data["demands"][first]
    mandatory.discard(first); optional.discard(first)

    while mandatory:
        feasible = [x for x in mandatory if total_load + data["demands"][x] <= data["vehicle_capacity"]]
        if not feasible: return None
        node = min(feasible, key=lambda x: min(matrix[x][r] for r in route))
        best_pos, best_inc = None, None
        for i in range(len(route)-1):
            inc = matrix[route[i]][node] + matrix[node][route[i+1]] - matrix[route[i]][route[i+1]]
            if best_inc is None or inc < best_inc: best_inc, best_pos = inc, i+1
        route.insert(best_pos, node); mandatory.remove(node); total_load += data["demands"][node]

    while optional:
        feasible = [x for x in optional if total_load + data["demands"][x] <= data["vehicle_capacity"]]
        if not feasible: break
        node = min(feasible, key=lambda x: min(matrix[x][r] for r in route))
        best_pos, best_inc = None, None
        for i in range(len(route)-1):
            inc = matrix[route[i]][node] + matrix[node][route[i+1]] - matrix[route[i]][route[i+1]]
            if best_inc is None or inc < best_inc: best_inc, best_pos = inc, i+1
        route.insert(best_pos, node); optional.remove(node); total_load += data["demands"][node]

    dist, tm, base_cost = calc_cost(data, data["distance_matrix"], data["time_matrix"], route, True)
    skipped = skipped_optional(data, set(route))
    total_cost = base_cost + len(skipped) * data["drop_optional_penalty"]
    objective = sum(matrix[route[i]][route[i+1]] for i in range(len(route)-1))
    return {
        "route": [data["city_names"][x] for x in route], "total_objective": objective,
        "total_cost": total_cost, "total_load": total_load,
        "visited_mandatory": sum(1 for i in range(n) if (i == depot or data["node_types"][i] == "Mandatory") and i in route),
        "skipped_optional": len(skipped), "skipped_optional_names": skipped,
    }

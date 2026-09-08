from .utils import calc_cost, skipped_optional

def solve_nearest_neighbor(data, matrix):
    n = len(matrix); depot = data["depot"]
    required = {i for i in range(n) if i != depot and data["node_types"][i] == "Mandatory"}
    optional = {i for i in range(n) if i != depot and data["node_types"][i] == "Optional"}
    unvisited = required | optional
    route = [depot]; current = depot
    total_load = data["demands"][depot]

    # Greedily serve mandatory nodes first, then optional nodes when feasible.
    while required:
        feasible = [x for x in required if total_load + data["demands"][x] <= data["vehicle_capacity"]]
        if not feasible: return None
        x = min(feasible, key=lambda node: matrix[current][node])
        route.append(x); current = x; total_load += data["demands"][x]; required.remove(x); unvisited.discard(x)

    while optional:
        feasible = [x for x in optional if total_load + data["demands"][x] <= data["vehicle_capacity"]]
        if not feasible: break
        x = min(feasible, key=lambda node: matrix[current][node])
        route.append(x); current = x; total_load += data["demands"][x]; optional.remove(x); unvisited.discard(x)

    route.append(depot)
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

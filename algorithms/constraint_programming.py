from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from .utils import calc_cost, skipped_optional

def solve_cp(data, matrix):
    n = len(matrix)
    manager = pywrapcp.RoutingIndexManager(n, data["num_vehicles"], data["depot"])
    routing = pywrapcp.RoutingModel(manager)

    def cost_callback(from_index, to_index):
        return int(round(matrix[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)] * 1000))
    transit_callback = routing.RegisterTransitCallback(cost_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback)

    def demand_callback(from_index):
        return int(data["demands"][manager.IndexToNode(from_index)])
    demand_idx = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_idx, 0, [data["vehicle_capacity"]] * data["num_vehicles"], True, "Capacity"
    )

    # Optional nodes may be dropped. Mandatory nodes have no disjunction and therefore must be visited.
    for node in range(n):
        if node != data["depot"] and data["node_types"][node] == "Optional":
            routing.AddDisjunction([manager.NodeToIndex(node)], int(round(data["drop_optional_penalty"] * 1000)))

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    params.time_limit.FromSeconds(2)
    solution = routing.SolveWithParameters(params)
    if not solution:
        return None

    all_routes, visited = [], set()
    total_objective = total_distance = total_time = 0.0
    total_load = 0

    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        route_nodes = []
        route_cost_obj = 0
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            route_nodes.append(node)
            visited.add(node)
            total_load += data["demands"][node]
            prev = index
            index = solution.Value(routing.NextVar(index))
            route_cost_obj += routing.GetArcCostForVehicle(prev, index, vehicle_id)
        route_nodes.append(manager.IndexToNode(index))

        if len(route_nodes) > 2 or (len(route_nodes) == 2 and route_nodes[0] != route_nodes[1]):
            dist, tm, var_cost = calc_cost(data, data["distance_matrix"], data["time_matrix"], route_nodes, True)
            obj = sum(matrix[route_nodes[i]][route_nodes[i+1]] for i in range(len(route_nodes)-1))
            total_distance += dist; total_time += tm; total_objective += obj
            all_routes.append({
                "vehicle": vehicle_id + 1,
                "route": [data["city_names"][x] for x in route_nodes],
                "load": sum(data["demands"][x] for x in route_nodes),
                "objective": obj, "variable_cost": var_cost - data["fixed_vehicle_cost"],
                "fixed_cost": data["fixed_vehicle_cost"],
            })

    # Recompute business cost independently of the CP integer-scaled objective.
    skipped = skipped_optional(data, visited)
    total_cost = total_distance * data["distance_cost"] + total_time * data["time_cost"]
    total_cost += sum(r["fixed_cost"] for r in all_routes)
    total_cost += len(skipped) * data["drop_optional_penalty"]

    return {
        "route": all_routes[0]["route"] if data["num_vehicles"] == 1 and all_routes else [],
        "vehicle_routes": all_routes,
        "total_objective": total_objective,
        "total_cost": total_cost,
        "total_load": total_load,
        "visited_mandatory": sum(1 for i in range(n) if (i == data["depot"] or data["node_types"][i] == "Mandatory") and i in visited),
        "skipped_optional": len(skipped),
        "skipped_optional_names": skipped,
    }

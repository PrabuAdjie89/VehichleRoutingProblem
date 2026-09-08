def node_status(data, node):
    return node == data["depot"] or data["node_types"][node] == "Mandatory"

def calc_cost(data, distance_matrix, time_matrix, route_nodes, vehicle_used=True):
    distance = sum(distance_matrix[route_nodes[i]][route_nodes[i+1]] for i in range(len(route_nodes)-1))
    time = sum(time_matrix[route_nodes[i]][route_nodes[i+1]] for i in range(len(route_nodes)-1))
    variable = distance * data["distance_cost"] + time * data["time_cost"]
    fixed = data["fixed_vehicle_cost"] if vehicle_used and len(route_nodes) > 1 else 0.0
    return distance, time, variable + fixed

def skipped_optional(data, visited):
    return [
        data["city_names"][i] for i in range(len(data["city_names"]))
        if i != data["depot"] and data["node_types"][i] == "Optional" and i not in visited
    ]

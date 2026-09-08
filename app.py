import streamlit as st
import pandas as pd

from algorithms.constraint_programming import solve_cp
from algorithms.nearest_neighbor import solve_nearest_neighbor
from algorithms.nearest_insert import solve_nearest_insert

st.set_page_config(page_title="VRP Optimization", page_icon="🚚", layout="wide")
st.title("🚚 Vehicle Routing Problem")
st.caption("VRP dengan Mandatory/Optional Node dan perhitungan cost.")

def make_location_table(n):
    return pd.DataFrame({
        "Location": [f"Location {i}" for i in range(n)],
        "Demand": [0] + [1] * (n - 1),
        "Node Type": ["Mandatory"] * n,
    })

def make_matrix(n):
    labels = [f"Location {i}" for i in range(n)]
    return pd.DataFrame(
        [[0 if i == j else 0 for j in range(n)] for i in range(n)],
        columns=labels, index=labels,
    )

def matrix_from_editor(df):
    return df.astype(float).values.tolist()

st.sidebar.header("Vehicle Configuration")
num_locations = st.sidebar.number_input("Jumlah lokasi", min_value=2, max_value=100, value=5, step=1)
num_vehicles = st.sidebar.number_input("Jumlah kendaraan", min_value=1, max_value=100, value=1, step=1)
vehicle_capacity = st.sidebar.number_input("Kapasitas kendaraan", min_value=1, value=52, step=1)
objective = st.sidebar.radio("Objective", ["Distance", "Time"])

st.sidebar.header("Cost Configuration")
fixed_vehicle_cost = st.sidebar.number_input("Fixed cost / kendaraan", min_value=0.0, value=0.0, step=1.0)
distance_cost = st.sidebar.number_input("Cost / unit distance", min_value=0.0, value=1.0, step=0.1)
time_cost = st.sidebar.number_input("Cost / unit time", min_value=0.0, value=0.0, step=0.1)
drop_optional_penalty = st.sidebar.number_input(
    "Penalty jika Optional Node tidak dikunjungi",
    min_value=0.0, value=0.0, step=1.0,
    help="Penalty ditambahkan ke total cost untuk setiap optional node yang dilewati."
)

if "num_locations" not in st.session_state:
    st.session_state.num_locations = num_locations

if st.session_state.num_locations != num_locations:
    st.session_state.num_locations = num_locations
    st.session_state.locations = make_location_table(num_locations)
    st.session_state.distance_matrix = make_matrix(num_locations)
    st.session_state.time_matrix = make_matrix(num_locations)
    st.rerun()

if "locations" not in st.session_state:
    st.session_state.locations = make_location_table(num_locations)
if "distance_matrix" not in st.session_state:
    st.session_state.distance_matrix = make_matrix(num_locations)
if "time_matrix" not in st.session_state:
    st.session_state.time_matrix = make_matrix(num_locations)

st.header("1. Data Lokasi")
st.write("Tentukan setiap node sebagai **Mandatory** (wajib dikunjungi) atau **Optional** (boleh dilewati).")

locations_df = st.data_editor(
    st.session_state.locations, use_container_width=True, hide_index=True,
    num_rows="fixed", key="location_editor",
    column_config={
        "Node Type": st.column_config.SelectboxColumn(
            "Node Type", options=["Mandatory", "Optional"], required=True
        )
    },
)
st.session_state.locations = locations_df

location_names = locations_df["Location"].astype(str).str.strip().tolist()
demands = locations_df["Demand"].fillna(0).astype(int).tolist()
node_types = locations_df["Node Type"].fillna("Mandatory").astype(str).tolist()

if len(set(location_names)) != len(location_names):
    st.error("Nama lokasi harus unik.")
if any(d < 0 for d in demands):
    st.error("Demand tidak boleh negatif.")
if any(t not in ("Mandatory", "Optional") for t in node_types):
    st.error("Node Type harus Mandatory atau Optional.")

depot_name = st.selectbox("Depot", location_names)
depot = location_names.index(depot_name)

# Depot selalu wajib karena merupakan titik awal/akhir kendaraan.
if node_types[depot] != "Mandatory":
    st.info("Depot otomatis diperlakukan sebagai Mandatory.")

st.header("2. Distance Matrix")
st.caption("Baris = lokasi asal, kolom = lokasi tujuan.")
distance_df = st.data_editor(
    st.session_state.distance_matrix, use_container_width=True,
    hide_index=False, num_rows="fixed", key="distance_editor",
)
distance_df.index = location_names
distance_df.columns = location_names
st.session_state.distance_matrix = distance_df

st.header("3. Time Matrix")
st.caption("Masukkan waktu tempuh antar lokasi dalam menit.")
time_df = st.data_editor(
    st.session_state.time_matrix, use_container_width=True,
    hide_index=False, num_rows="fixed", key="time_editor",
)
time_df.index = location_names
time_df.columns = location_names
st.session_state.time_matrix = time_df

st.header("4. Dataset Summary")
total_demand = sum(demands[i] for i in range(num_locations) if i == depot or node_types[i] == "Mandatory")
optional_count = sum(1 for i in range(num_locations) if i != depot and node_types[i] == "Optional")
mandatory_count = num_locations - optional_count
total_capacity = num_vehicles * vehicle_capacity

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Jumlah Lokasi", num_locations)
c2.metric("Mandatory", mandatory_count)
c3.metric("Optional", optional_count)
c4.metric("Mandatory Demand", total_demand)
c5.metric("Total Kapasitas", total_capacity)

st.header("5. Optimization Method")
algorithms = st.multiselect(
    "Pilih algoritma",
    ["Constraint Programming", "Nearest Neighbor", "Nearest Insert"],
    default=["Constraint Programming", "Nearest Neighbor", "Nearest Insert"],
)

if st.button("🚀 Calculate Route", type="primary", use_container_width=True):
    try:
        distance_matrix = matrix_from_editor(distance_df)
        time_matrix = matrix_from_editor(time_df)
    except Exception:
        st.error("Matrix harus berisi angka.")
        st.stop()

    if len(distance_matrix) != num_locations or len(time_matrix) != num_locations:
        st.error("Ukuran matrix tidak sesuai.")
        st.stop()

    mandatory_demand = sum(
        demands[i] for i in range(num_locations)
        if i == depot or node_types[i] == "Mandatory"
    )
    if mandatory_demand > total_capacity:
        st.warning("Demand Mandatory melebihi total kapasitas. Tidak semua Mandatory Node dapat dilayani.")

    data = {
        "distance_matrix": distance_matrix,
        "time_matrix": time_matrix,
        "demands": demands,
        "node_types": node_types,
        "vehicle_capacity": vehicle_capacity,
        "num_vehicles": num_vehicles,
        "depot": depot,
        "city_names": location_names,
        "fixed_vehicle_cost": fixed_vehicle_cost,
        "distance_cost": distance_cost,
        "time_cost": time_cost,
        "drop_optional_penalty": drop_optional_penalty,
    }
    matrix = distance_matrix if objective == "Distance" else time_matrix
    results = []

    with st.spinner("Menghitung rute..."):
        solvers = [
            ("Constraint Programming", solve_cp),
            ("Nearest Neighbor", solve_nearest_neighbor),
            ("Nearest Insert", solve_nearest_insert),
        ]
        for name, solver in solvers:
            if name in algorithms:
                result = solver(data, matrix)
                if result:
                    result["Algorithm"] = name
                    results.append(result)

    if not results:
        st.error("Tidak ada solusi yang ditemukan.")
        st.stop()

    st.header("6. Results")
    rows = []
    for result in results:
        if result.get("vehicle_routes"):
            route_text = " | ".join(
                f"V{r['vehicle']}: {' → '.join(r['route'])}" for r in result["vehicle_routes"]
                if len(r["route"]) > 1
            )
        else:
            route_text = " → ".join(result["route"])

        rows.append({
            "Algorithm": result["Algorithm"],
            "Route": route_text,
            f"Total {objective}": result["total_objective"],
            "Total Cost": result["total_cost"],
            "Total Load": result["total_load"],
            "Visited Mandatory": result["visited_mandatory"],
            "Skipped Optional": result["skipped_optional"],
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.subheader("Route Details")
    for result in results:
        with st.expander(result["Algorithm"]):
            if result.get("vehicle_routes"):
                for r in result["vehicle_routes"]:
                    if len(r["route"]) > 1:
                        st.write(f"Vehicle {r['vehicle']}: {' → '.join(r['route'])}")
                        st.write(f"  Objective: {r['objective']:.2f} | Cost: {r['variable_cost'] + r['fixed_cost']:.2f} | Load: {r['load']}")
            else:
                st.write(" → ".join(result["route"]))
            st.write(f"Total {objective}: {result['total_objective']:.2f}")
            st.write(f"Total Cost: {result['total_cost']:.2f}")
            st.write(f"Visited Mandatory: {result['visited_mandatory']}")
            st.write(f"Skipped Optional: {result['skipped_optional']}")
            if result["skipped_optional_names"]:
                st.write("Optional skipped: " + ", ".join(result["skipped_optional_names"]))

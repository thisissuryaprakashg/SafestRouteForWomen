import osmnx as ox
import networkx as nx
import geopandas as gpd
from shapely.geometry import Point
from datetime import datetime
import os
from tqdm import tqdm  # For displaying progress bars in loops
import folium  # For interactive map rendering

# --- Step 1: Load or Download Road Network ---
graph_file = "bangalore.graphml"
day_graph_file = "day_graph.graphml"
night_graph_file = "night_graph.graphml"

# If the road network is already saved, load it. Otherwise, download and save it.
if os.path.exists(graph_file):
    G = ox.load_graphml(graph_file)
    print("Loaded road network from file!")
else:
    print("Downloading road network...")
    G = ox.graph_from_place("Bangalore, India", network_type="walk")
    ox.save_graphml(G, graph_file)
    print("Downloaded and saved road network!")

# --- Step 2: Load Safety-Related Geospatial Data ---
print("Loading safety parameters...")
crime_data = gpd.read_file("./crimes.geojson")
cctv_data = gpd.read_file("./cctv.geojson")
street_lights = gpd.read_file("./streetlights.geojson")
night_clubs = gpd.read_file("./pubs.geojson")
police_stations = gpd.read_file("./police.geojson")

# Reproject all geospatial data to a common CRS for accurate spatial analysis
target_crs = "EPSG:26918"
crime_data = crime_data.to_crs(target_crs)
cctv_data = cctv_data.to_crs(target_crs)
street_lights = street_lights.to_crs(target_crs)
night_clubs = night_clubs.to_crs(target_crs)
police_stations = police_stations.to_crs(target_crs)

# Enable spatial indexing to speed up spatial queries
crime_data.sindex
cctv_data.sindex
street_lights.sindex
night_clubs.sindex
police_stations.sindex

# --- Step 3: Utility Functions ---

def is_night():
    """Return True if the current time is considered night (6 PM - 6 AM)."""
    now = datetime.now()
    return now.hour < 6 or now.hour > 18

def count_nearby_features_with_sindex(edge_midpoint, gdf, radius=75, target_crs="EPSG:26918"):
    """
    Count how many features from a given GeoDataFrame are near a point.
    Uses spatial index for efficient search.
    """
    midpoint_gdf = gpd.GeoDataFrame(geometry=[edge_midpoint], crs="EPSG:4326")
    midpoint_gdf = midpoint_gdf.to_crs(target_crs)
    buffer = midpoint_gdf.geometry.iloc[0].buffer(radius)
    return gdf.sindex.query(buffer, predicate="intersects").size

def compute_edge_length(u, v, data, crime_data, cctv_data, street_lights, night_clubs, police_stations, is_night):
    """
    Adjust the edge length based on safety features near the edge midpoint.
    Adds penalties or rewards to make routes safer.
    """
    edge_midpoint = Point((data["geometry"].centroid.x, data["geometry"].centroid.y))
    length = float(data["length"])
    length += 25000  # Base penalty to influence routing away from long paths

    # Adjust based on safety features
    length += 1000 * count_nearby_features_with_sindex(edge_midpoint, crime_data)
    length -= 1000 * count_nearby_features_with_sindex(edge_midpoint, cctv_data)
    length -= 2500 * count_nearby_features_with_sindex(edge_midpoint, police_stations)

    if is_night:
        length -= 200 * count_nearby_features_with_sindex(edge_midpoint, street_lights)
        length += 4000 * count_nearby_features_with_sindex(edge_midpoint, night_clubs)

    return length

def modify_edge_lengths(G, is_night, crime_data, cctv_data, street_lights, night_clubs, police_stations):
    """
    Modify the 'length' attribute of each edge in the graph based on safety.
    """
    edges = list(G.edges(data=True))
    for u, v, data in tqdm(edges, desc="Modifying edge lengths", unit="edges"):
        if "geometry" in data and "length" in data:
            modified_length = compute_edge_length(
                u, v, data, crime_data, cctv_data,
                street_lights, night_clubs, police_stations, is_night
            )
            data["length"] = modified_length
    return G

# --- Step 4: Precompute and Save Day/Night Graphs if Not Already Present ---
if os.path.exists(day_graph_file):
    print("DAY Graph already precomputed and saved. Loading the appropriate graph...")
else:
    print("Precomputing and saving graphs for day...")
    day_graph = modify_edge_lengths(
        G, is_night=False, crime_data=crime_data, cctv_data=cctv_data,
        street_lights=street_lights, night_clubs=night_clubs, police_stations=police_stations
    )
    ox.save_graphml(day_graph, day_graph_file)

if os.path.exists(night_graph_file):
    print("NIGHT Graph already precomputed and saved. Loading the appropriate graph...")
else:
    print("Precomputing and saving graphs for night...")
    night_graph = modify_edge_lengths(
        G, is_night=True, crime_data=crime_data, cctv_data=cctv_data,
        street_lights=street_lights, night_clubs=night_clubs, police_stations=police_stations
    )
    ox.save_graphml(night_graph, night_graph_file)

# --- Step 5: Load the Appropriate Graph (Commented out for now) ---
# if is_night():
#     G = ox.load_graphml(night_graph_file)
# else:
#     G = ox.load_graphml(day_graph_file)

# --- Step 6: Routing Functions ---

def find_safest_route(G, start_coords, end_coords):
    """Find the safest route between two points using the modified edge weights."""
    start_node = ox.distance.nearest_nodes(G, start_coords[1], start_coords[0])
    end_node = ox.distance.nearest_nodes(G, end_coords[1], end_coords[0])
    route = nx.shortest_path(G, start_node, end_node, weight="weight")
    return route

def get_route_coordinates(G, route):
    """
    Convert a route from graph nodes to a list of (lat, lon) coordinates.
    Useful for plotting the route on a map.
    """
    return [(G.nodes[node]['y'], G.nodes[node]['x']) for node in route]

# --- Step 7: Compute the Safest Route Between Two Locations ---

start_coords = (12.99310, 77.55318)  # Start location (lat, lon)
end_coords = (12.99507, 77.55345)    # End location (lat, lon)

print("Computing the safest route...")
route = find_safest_route(G, start_coords, end_coords)

# --- Step 8: Visualize the Route on Folium ---

print("Visualizing the safest route on Folium...")
route_coords = get_route_coordinates(G, route)
m = folium.Map(location=start_coords[::-1], zoom_start=15)

# Draw the route line
folium.PolyLine(route_coords, color="blue", weight=5, opacity=0.8).add_to(m)

# (Optional) Add start and end markers
start_node = ox.distance.nearest_nodes(G, start_coords[::-1][0], start_coords[::-1][1])
end_node = ox.distance.nearest_nodes(G, end_coords[::-1][0], end_coords[::-1][1])

# Save map as an HTML file
output_map_file = "safest_route_map.html"
m.save(output_map_file)
print(f"Map saved to {output_map_file}. Open this file to view the route.")

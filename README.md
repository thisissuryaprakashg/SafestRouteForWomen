# Safe Path Recommender – Bangalore

This project recommends the **safest walking route** between any two points in Bangalore by analyzing multiple safety-related factors such as crime incidents, CCTV coverage, street lighting, police station proximity, and nightlife activity. Instead of just finding the shortest path, it finds routes that prioritize user safety.

---

## 🔍 Project Overview

The key idea is to use a graph representation of Bangalore’s street network and modify the edge weights to reflect the safety of each road segment. This way, safer routes may be slightly longer but avoid dangerous or poorly monitored areas.

### How it works:

- **Base graph:** The walking network of Bangalore is extracted from OpenStreetMap and saved as a `.graphml` file.
- **Safety data:** Various `.geojson` files provide spatial data on crime locations, CCTV cameras, streetlights, police stations, and pubs/nightclubs.
- **Edge weight modification:**  
  Each road segment’s weight (originally distance or travel time) is adjusted based on nearby safety factors:
  - **Risk factors** (like high crime density or nightlife venues at night) increase the edge weight.
  - **Safety factors** (like CCTV coverage, streetlights, and police proximity) decrease the edge weight.
  
This is done by calculating proximity or density scores of these features around each edge, and combining them into a safety score. The original edge weight is multiplied by a function of these scores to produce a modified “risk-aware” weight.

- **Separate day and night graphs:** Since safety conditions vary by time of day, the project precomputes two versions of the graph — one for daytime and one for nighttime — to reflect different risk profiles.

- **Route calculation:** The safest route is computed by finding the shortest path on the adjusted graph using NetworkX’s shortest path algorithms.

---

## 📁 Folder Structure

Place all the following files in the same directory:

- `crimes.geojson` — Crime incident locations  
- `cctv.geojson` — CCTV camera locations  
- `streetlights.geojson` — Public streetlight locations  
- `pubs.geojson` — Nightlife venues (pubs, clubs)  
- `police.geojson` — Police station locations  
- `bangalore.graphml` — Base road network graph  
- `day_graph.graphml` — Safety-weighted graph for daytime routing  
- `night_graph.graphml` — Safety-weighted graph for nighttime routing  
- `safest_route_map.html` — Generated interactive map showing the safest route

---

import pandas as pd
import networkx as nx

DATA_PATH = r"C:\Users\exam.cb\karthik pro\national_highways.xlsx"
ORIGIN = "Delhi"
DEST = "Bengaluru"


def load_data(path=DATA_PATH):
    df = pd.read_excel(path)
    df = df.copy()
    df["Travel_Time_hrs"] = (df["Distance_km"] / df["Avg_Speed_kmh"]).round(2)
    return df


def build_graph(df):
    G = nx.Graph()
    for _, r in df.iterrows():
        G.add_edge(
            r["Source_City"],
            r["Target_City"],
            highway=r["Highway_Code"],
            distance=float(r["Distance_km"]),
            speed=float(r["Avg_Speed_kmh"]),
            toll=float(r["Toll_INR"]),
            time=float(r["Travel_Time_hrs"]),
        )
    return G


def route_stats(G, path):
    if path is None or len(path) < 2:
        return None
    d = t = tol = 0.0
    legs = []
    for u, v in zip(path[:-1], path[1:]):
        e = G[u][v]
        d += e["distance"]
        t += e["time"]
        tol += e["toll"]
        legs.append(
            {
                "from": u,
                "to": v,
                "highway": e["highway"],
                "distance": e["distance"],
                "speed": e["speed"],
                "time": e["time"],
                "toll": e["toll"],
            }
        )
    return {
        "path": path,
        "distance": round(d, 2),
        "time": round(t, 2),
        "toll": round(tol, 2),
        "legs": legs,
    }


def best_routes(G, origin=ORIGIN, dest=DEST):
    routes = {}
    for w in ["distance", "time", "toll"]:
        dist, path = nx.single_source_dijkstra(G, origin, dest, weight=w)
        routes[w] = route_stats(G, path)
    return routes


def closure_fastest(G, origin=ORIGIN, dest=DEST, closed=("Mumbai", "Pune")):
    G2 = G.copy()
    if G2.has_edge(*closed):
        G2.remove_edge(*closed)
    connected = nx.is_connected(G2)
    dist, path = nx.single_source_dijkstra(G2, origin, dest, weight="time")
    after = route_stats(G2, path)
    before = best_routes(G, origin, dest)["time"]
    return {
        "connected": connected,
        "removed_edge": closed,
        "after": after,
        "before": before,
        "G2": G2,
    }


def network_description(G):
    deg = dict(G.degree())
    high_deg = {c: d for c, d in deg.items() if d >= 3}
    density = nx.density(G)
    avg_deg = sum(deg.values()) / len(deg)
    bc = nx.betweenness_centrality(G, weight="distance")
    top5 = sorted(bc.items(), key=lambda x: -x[1])[:5]
    return {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "connected": nx.is_connected(G),
        "high_degree": high_deg,
        "density": density,
        "avg_degree": avg_deg,
        "betweenness_top5": top5,
        "degree": deg,
    }


def dijkstra_trace(G, origin=ORIGIN, dest=DEST, weight="time"):
    """Return step-by-step Dijkstra trace for the subgraph corridor."""
    import heapq

    dist = {n: float("inf") for n in G.nodes}
    prev = {n: None for n in G.nodes}
    dist[origin] = 0
    visited = set()
    heap = [(0, origin)]
    steps = []
    while heap:
        d, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)
        snap = {n: (round(dist[n], 2) if dist[n] != float("inf") else "inf") for n in G.nodes}
        steps.append({"visited": u, "dist": d, "distances": dict(snap), "visited_set": set(visited)})
        if u == dest:
            break
        for v in G.neighbors(u):
            if v in visited:
                continue
            w = G[u][v][weight]
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))
    # reconstruct path
    path = []
    at = dest
    while at is not None:
        path.append(at)
        at = prev[at]
    path.reverse()
    return steps, path, dist[dest]

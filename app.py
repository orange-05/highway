import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from graph_core import (
    load_data, build_graph, route_stats, best_routes,
    closure_fastest, network_description, dijkstra_trace,
    ORIGIN, DEST, DATA_PATH,
)

st.set_page_config(
    page_title="National Highways Logistics Grid",
    page_icon="🚚",
    layout="wide",
)

st.title("🚚 National Highways Logistics Grid")
st.markdown(
    "**Delhi → Bengaluru** | Two contracts: (1) Cold-chain vaccines (time-critical)  "
    "(2) Weekly cement run (cost-critical)  |  Backup plan: Mumbai–Pune expressway closure"
)

# ---------------- Load data ----------------
@st.cache_data
def get_df():
    return load_data(DATA_PATH)

@st.cache_resource
def get_G(df):
    return build_graph(df)

df = get_df()
G = get_G(df)
desc = network_description(G)

# ---------------- Sidebar ----------------
st.sidebar.header("Navigation")
task = st.sidebar.radio(
    "Choose a task",
    [
        "1. Data Analysis",
        "2. Build the Graph",
        "3. Describe the Network",
        "4. Dijkstra Hand-Trace",
        "5. Distance vs Time vs Toll",
        "6. Expressway Closure",
        "7. Visualize",
        "8. Recommendation",
    ],
)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Dataset:** `{DATA_PATH}`")
st.sidebar.markdown(f"**Cities:** {desc['nodes']}  |  **Links:** {desc['edges']}")
st.sidebar.markdown(f"**Connected:** {desc['connected']}")

# ================= TASK 1 =================
if task == "1. Data Analysis":
    st.header("Task 1 — Analyse the data & identify trends (pandas)")
    st.subheader("Raw dataset (first 15 rows)")
    st.dataframe(df.head(15), use_container_width=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total highway links", len(df))
    c2.metric("Unique cities", len(set(df["Source_City"]) | set(df["Target_City"])))
    c3.metric("Total distance (km)", int(df["Distance_km"].sum()))
    c4.metric("Total toll (INR)", int(df["Toll_INR"].sum()))

    st.subheader("Distance statistics")
    st.dataframe(df["Distance_km"].describe().to_frame().T, use_container_width=True)

    st.subheader("Toll statistics")
    st.dataframe(df["Toll_INR"].describe().to_frame().T, use_container_width=True)

    st.subheader("Speed statistics")
    st.dataframe(df["Avg_Speed_kmh"].describe().to_frame().T, use_container_width=True)

    st.subheader("Top 10 longest links")
    st.dataframe(df.nlargest(10, "Distance_km"), use_container_width=True)

    st.subheader("Top 10 most expensive toll links")
    st.dataframe(df.nlargest(10, "Toll_INR"), use_container_width=True)

    # Trend charts
    st.subheader("Distance vs Toll (scatter)")
    fig = px.scatter(df, x="Distance_km", y="Toll_INR", color="Highway_Code",
                     hover_data=["Source_City", "Target_City", "Avg_Speed_kmh"],
                     title="Distance vs Toll by link")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Toll by Highway Code (box)")
    fig2 = px.box(df, x="Highway_Code", y="Toll_INR", points="all",
                  title="Toll distribution per highway code")
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("""
    **Trends observed:**
    - Longer links generally carry higher tolls, but expressways (Yamuna, Delhi Mumbai Exp, NE 4) charge a premium per km for higher speed.
    - The NH 44 North–South corridor forms the backbone Delhi → Bengaluru with the lowest cumulative toll.
    - The direct Delhi–Vadodara NE 4 link (1010 km, ₹1550) is the single longest and priciest link but enables the fastest routing.
    """)

# ================= TASK 2 =================
elif task == "2. Build the Graph":
    st.header("Task 2 — Build the graph")
    st.markdown(
        "Nodes = cities, Edges = highway links. Each edge carries **highway code, distance (km), "
        "avg speed (km/h), toll (INR)**. A derived **travel-time (hrs = distance / speed, rounded to 2 decimals)** column is added."
    )
    st.subheader("Enriched dataset (with Travel_Time_hrs)")
    show_df = df.copy()
    st.dataframe(show_df, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Nodes (cities)", G.number_of_nodes())
    c2.metric("Edges (links)", G.number_of_edges())
    c3.metric("Is connected?", "Yes" if desc["connected"] else "No")

    st.write("**Expected:** 46 cities, 52 links, connected ✅")
    st.write("**Actual:**", G.number_of_nodes(), "cities,", G.number_of_edges(), "links,",
             "connected" if desc["connected"] else "NOT connected")

    st.subheader("Edge attribute vector w(e) = (distance, time, toll)")
    st.markdown("Example link: **Delhi → Agra** (Yamuna Expressway)")
    e = G["Delhi"]["Agra"]
    st.code(f"w(Delhi,Agra) = ({e['distance']}, {e['time']}, {e['toll']})  # (km, hrs, INR)")

    with st.expander("Sample edge attributes (first 5)"):
        for i, (u, v, ed) in enumerate(list(G.edges(data=True))[:5]):
            st.write(f"{u} ↔ {v}: {ed}")

# ================= TASK 3 =================
elif task == "3. Describe the Network":
    st.header("Task 3 — Describe the network")

    st.subheader("a) Cities with degree ≥ 3")
    st.write("High-degree cities (junctions/hubs):")
    hd = desc["high_degree"]
    st.dataframe(pd.DataFrame(list(hd.items()), columns=["City", "Degree"]).sort_values("Degree", ascending=False),
                 use_container_width=True)
    st.write(f"**Network density:** {desc['density']:.4f}")
    st.write(f"**Average degree:** {desc['avg_degree']:.2f}")

    st.subheader("b) Betweenness centrality (weight = distance)")
    st.write("Top 5 cities by betweenness centrality:")
    bc_df = pd.DataFrame(desc["betweenness_top5"], columns=["City", "Betweenness"])
    st.dataframe(bc_df, use_container_width=True)
    st.markdown(
        "A high betweenness value means the city lies on many shortest (least-distance) paths "
        "across the network. For the truck fleet, these cities are **critical transshipment / "
        "bottleneck junctions** — closing or congesting one (e.g., Hyderabad or Nagpur) forces "
        "many detours and raises fleet-wide time and fuel cost."
    )

    st.subheader("c) Edge attribute vector w(e) = (d(e), t(e), toll(e))")
    st.markdown("Chosen link: **Delhi ↔ Agra** (Yamuna Expressway)")
    st.code(f"w(Delhi, Agra) = ({G['Delhi']['Agra']['distance']}, {G['Delhi']['Agra']['time']}, {G['Delhi']['Agra']['toll']})")
    st.markdown("- d(e) = 210 km\n- t(e) = 2.10 h\n- toll(e) = ₹310")

# ================= TASK 4 =================
elif task == "4. Dijkstra Hand-Trace":
    st.header("Task 4 — Trace Dijkstra (hand-work guide)")
    st.markdown(
        "Use the **NH 44 North–South corridor sub-graph** below (Delhi → Agra → Gwalior → Jhansi → "
        "Lalitpur → Sagar → Nagpur → Hyderabad → Kurnool → Anantapur → Bengaluru). "
        "We run Dijkstra minimizing **travel time**."
    )

    corridor = ["Delhi", "Agra", "Gwalior", "Jhansi", "Lalitpur", "Sagar", "Nagpur",
                "Hyderabad", "Kurnool", "Anantapur", "Bengaluru"]
    sub = G.subgraph(corridor)

    steps, path, final_dist = dijkstra_trace(sub, ORIGIN, DEST, weight="time")

    st.subheader("a) Sub-graph + iteration table")
    st.markdown("**Edges in sub-graph (time in hours):**")
    edge_rows = []
    for u, v, ed in sub.edges(data=True):
        edge_rows.append({"From": u, "To": v, "Highway": ed["highway"],
                          "Distance (km)": ed["distance"], "Time (h)": ed["time"]})
    st.dataframe(pd.DataFrame(edge_rows), use_container_width=True)

    st.markdown("**Iteration table (node visited & tentative distances after each step):**")
    rows = []
    all_nodes = list(sub.nodes)
    for s in steps:
        row = {"Step": len(rows) + 1, "Node visited": s["visited"]}
        for n in all_nodes:
            row[n] = s["distances"][n]
        rows.append(row)
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    st.subheader("b) Relaxation rule")
    st.code("""
    For current node u and each unvisited neighbor v:
        if dist[u] + w(u,v) < dist[v]:
            dist[v] = dist[u] + w(u,v)
            prev[v] = u
    where w(u,v) = travel time (hours) of edge (u,v).
    """)

    st.subheader("c) Verify with nx.single_source_dijkstra")
    dist_nx, path_nx = nx.single_source_dijkstra(sub, ORIGIN, DEST, weight="time")
    st.write("**Hand-trace result:**", path, "time =", round(final_dist, 2), "h")
    st.write("**NetworkX result:**", path_nx, "time =", round(dist_nx, 2), "h")
    st.success("✅ Match!" if path == path_nx and abs(final_dist - dist_nx) < 1e-6 else "❌ Mismatch")

# ================= TASK 5 =================
elif task == "5. Distance vs Time vs Toll":
    st.header("Task 5 — Delhi → Bengaluru: distance vs time vs toll")
    routes = best_routes(G)

    labels = {"distance": "Shortest Distance", "time": "Fastest", "toll": "Cheapest (Toll)"}
    for key in ["distance", "time", "toll"]:
        r = routes[key]
        st.subheader(f"{labels[key]} route")
        st.write("**Path:**", " → ".join(r["path"]))
        c1, c2, c3 = st.columns(3)
        c1.metric("Distance (km)", r["distance"])
        c2.metric("Time (h)", r["time"])
        c3.metric("Toll (INR)", r["toll"])
        with st.expander("Leg-by-leg breakdown"):
            st.dataframe(pd.DataFrame(r["legs"]), use_container_width=True)

    st.subheader("Why shortest and fastest differ")
    rd = routes["distance"]; rt = routes["time"]
    st.markdown(f"""
    - **Shortest distance** ({rd['distance']} km) follows NH 44 via Agra–Nagpur–Hyderabad but uses many
      lower-speed sections (60–85 km/h), so it takes **{rd['time']} h** and costs **₹{rd['toll']}**.
    - **Fastest** ({rt['time']} h) takes the Delhi–Vadodara NE 4 link (110 km/h) and the Mumbai–Pune
      expressway (90 km/h), covering **{rt['distance']} km** (330 km longer) but saving about
      **{rd['time'] - rt['time']:.2f} h**. It costs **₹{rt['toll']}** (₹{rt['toll']-rd['toll']} more in tolls).
    """)

    st.subheader("Comparison table")
    cmp_df = pd.DataFrame([
        {"Route": labels["distance"], "Distance (km)": routes["distance"]["distance"],
         "Time (h)": routes["distance"]["time"], "Toll (INR)": routes["distance"]["toll"]},
        {"Route": labels["time"], "Distance (km)": routes["time"]["distance"],
         "Time (h)": routes["time"]["time"], "Toll (INR)": routes["time"]["toll"]},
        {"Route": labels["toll"], "Distance (km)": routes["toll"]["distance"],
         "Time (h)": routes["toll"]["time"], "Toll (INR)": routes["toll"]["toll"]},
    ])
    st.dataframe(cmp_df, use_container_width=True)

# ================= TASK 6 =================
elif task == "6. Expressway Closure":
    st.header("Task 6 — Mumbai–Pune expressway closure (landslide)")
    st.markdown("The **Mumbai ↔ Pune** edge is removed from a copy of G. Recompute fastest Delhi → Bengaluru.")

    cl = closure_fastest(G)
    st.write("**Network still connected after closure:**", "Yes ✅" if cl["connected"] else "No ❌")

    st.subheader("Fastest route BEFORE closure")
    b = cl["before"]
    st.write(" → ".join(b["path"]))
    st.write(f"Distance: {b['distance']} km | Time: {b['time']} h | Toll: ₹{b['toll']}")

    st.subheader("Fastest route AFTER closure")
    a = cl["after"]
    st.write(" → ".join(a["path"]))
    st.write(f"Distance: {a['distance']} km | Time: {a['time']} h | Toll: ₹{a['toll']}")

    st.subheader("Change compared with pre-closure fastest")
    dd = a["distance"] - b["distance"]
    dt = a["time"] - b["time"]
    dtoll = a["toll"] - b["toll"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Δ Distance (km)", f"{dd:+.2f}")
    c2.metric("Δ Time (h)", f"{dt:+.2f}")
    c3.metric("Δ Toll (INR)", f"{dtoll:+.2f}")
    st.markdown(f"""
    With Mumbai–Pune closed, the fastest option reverts to the NH 44 corridor. The fleet loses the
    high-speed expressway shortcut: **+{dt:.2f} h**, travels **{-dd:.2f} km less**, and saves **₹{-dtoll}** in tolls.
    This is the **backup plan** for the cold-chain vaccines if the monsoon landslide strikes.
    """)

# ================= TASK 7 =================
elif task == "7. Visualize":
    st.header("Task 7 — Visualize")

    routes = best_routes(G)
    shortest_path = routes["distance"]["path"]
    fastest_path = routes["time"]["path"]

    st.subheader("a) Network with shortest & fastest Delhi → Bengaluru routes highlighted")

    # Layout
    pos = nx.spring_layout(G, seed=42, k=0.5)

    # Build edge traces
    edge_x, edge_y, edge_info = [], [], []
    for u, v, ed in G.edges(data=True):
        x0, y0 = pos[u]; x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
        edge_info.append(f"{u} ↔ {v}<br>{ed['highway']} | {ed['distance']} km | {ed['time']} h | ₹{ed['toll']}")

    edge_trace = go.Scatter(x=edge_x, y=edge_y, mode="lines",
                            line=dict(color="#cccccc", width=1),
                            hoverinfo="none", showlegend=False)

    # Highlighted route edges
    def route_edges(path):
        xs, ys = [], []
        for u, v in zip(path[:-1], path[1:]):
            x0, y0 = pos[u]; x1, y1 = pos[v]
            xs += [x0, x1, None]; ys += [y0, y1, None]
        return xs, ys

    sx, sy = route_edges(shortest_path)
    fx, fy = route_edges(fastest_path)

    shortest_trace = go.Scatter(x=sx, y=sy, mode="lines", line=dict(color="#2ecc71", width=4),
                                name="Shortest distance", hoverinfo="none")
    fastest_trace = go.Scatter(x=fx, y=fy, mode="lines", line=dict(color="#e74c3c", width=4),
                               name="Fastest", hoverinfo="none")

    # Node trace
    node_x = [pos[n][0] for n in G.nodes]
    node_y = [pos[n][1] for n in G.nodes]
    node_trace = go.Scatter(x=node_x, y=node_y, mode="markers+text",
                            text=list(G.nodes), textposition="top center",
                            marker=dict(size=10, color="#34495e", line=dict(width=1, color="white")),
                            hoverinfo="text", showlegend=False)

    fig = go.Figure(data=[edge_trace, shortest_trace, fastest_trace, node_trace])
    fig.update_layout(title="Delhi → Bengaluru: Shortest (green) vs Fastest (red)",
                      showlegend=True, hovermode="closest",
                      margin=dict(l=20, r=20, t=40, b=20),
                      xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                      yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                      height=650)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("b) Grouped horizontal bar chart — Shortest vs Fastest")
    rd, rt = routes["distance"], routes["time"]
    metrics = ["Distance (km)", "Time (h)", "Toll (INR)"]
    shortest_vals = [rd["distance"], rd["time"], rd["toll"]]
    fastest_vals = [rt["distance"], rt["time"], rt["toll"]]

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(y=metrics, x=shortest_vals, name="Shortest distance", orientation="h",
                          marker_color="#2ecc71"))
    fig2.add_trace(go.Bar(y=metrics, x=fastest_vals, name="Fastest", orientation="h",
                          marker_color="#e74c3c"))
    fig2.update_layout(barmode="group", title="Shortest vs Fastest route metrics",
                       xaxis_title="Value", yaxis_title="Metric", height=400)
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("""
    Because distance (km), time (h) and toll (₹) have different scales, they are plotted on a shared
    horizontal axis with the actual values shown; the relative bar lengths let you compare the two
    routes across all three metrics at a glance.
    """)

# ================= TASK 8 =================
elif task == "8. Recommendation":
    st.header("Task 8 — Recommendation (150–200 words)")

    routes = best_routes(G)
    cl = closure_fastest(G)
    rd, rt, rc = routes["distance"], routes["time"], routes["toll"]
    a, b = cl["after"], cl["before"]

    rec = f"""
**Cold-chain vaccines → Assign the FASTEST route**
Delhi → Vadodara → Surat → Mumbai → Pune → Kolhapur → Belagavi → Hubballi → Davanagere → Bengaluru.
Time: **{rt['time']} h**, distance: **{rt['distance']} km**, toll: **₹{rt['toll']}**.
Vaccines are temperature-sensitive and time-critical; the NE 4 (110 km/h) and Mumbai–Pune expressway (90 km/h)
save about **{rd['time']-rt['time']:.2f} h** versus the shortest route, reducing cold-chain breach risk despite
**₹{rt['toll']-rd['toll']}** higher toll and **{rt['distance']-rd['distance']} km** extra. If the monsoon landslide closes
Mumbai–Pune, switch to the backup NH 44 corridor ({a['time']} h, only **+{a['time']-b['time']:.2f} h**).

**Bulk dry freight (cement) → Assign the CHEAPEST / SHORTEST route**
Delhi → Agra → Gwalior → Jhansi → Lalitpur → Sagar → Nagpur → Hyderabad → Kurnool → Anantapur → Bengaluru.
Distance: **{rc['distance']} km**, time: **{rc['time']} h**, toll: **₹{rc['toll']}**.
Cement is non-perishable and cost-driven; this route saves **₹{rt['toll']-rc['toll']}** in tolls and **{rt['distance']-rc['distance']} km**
of fuel versus the fastest route. The NH 44 corridor is also the closure backup, keeping the cement schedule
robust. Total weekly saving vs fastest: **₹{rt['toll']-rc['toll']}** per truck.
""".strip()

    st.markdown(rec)
    st.caption(f"Word count: {len(rec.split())}")

# Footer
st.markdown("---")
st.markdown("Built with **Streamlit + NetworkX + Pandas + Plotly** | National Highways Logistics Grid")

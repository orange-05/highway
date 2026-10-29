# National Highways Logistics Grid

A fully operational, interactive **Streamlit** webapp that models India's national highway network as a weighted graph
and plans optimal truck routes for a Delhi-based logistics company serving two Bengaluru contracts:

1. **Cold-chain vaccines** — time-critical (minimise hours)
2. **Weekly cement run** — cost-critical (minimise toll & diesel)

## Scenario
A monsoon landslide may close the **Mumbai–Pune expressway**, so a backup route is pre-computed.

## Data
- `national_highways.xlsx` — 52 highway links, 46 cities
- Columns: Source_City, Target_City, Highway_Code, Distance_km, Avg_Speed_kmh, Toll_INR
- Derived column: Travel_Time_hrs = Distance_km / Avg_Speed_kmh (rounded to 2 decimals)

## Tech stack
Python · Pandas · NetworkX · Streamlit · Plotly · Matplotlib

## Run locally
```bash
cd road_app
pip install -r requirements.txt
streamlit run app.py
```

## Tasks covered
1. Data analysis & trends (pandas)
2. Graph build — 46 nodes, 52 edges, connected ✅, travel-time column
3. Network description — degree ≥ 3, density, avg degree, betweenness centrality top-5, edge vector w(e)
4. Dijkstra hand-trace (iteration table, relaxation rule, NetworkX verification)
5. Delhi → Bengaluru: shortest-distance vs fastest vs cheapest-toll routes
6. Mumbai–Pune expressway closure — fastest route recompute + delta comparison
7. Visualisation — highlighted network + grouped bar chart
8. Recommendation — vaccine route vs cement route with computed numbers



project explanation propmt 


we will be building an advanced  mini project that is the combination of python and graph theory the major concept is the "National highways logistics grid"  
the idea and challenge : a logistics company in Delhi had got 2 contracts for Bangalore [1: vaccines must stay cold , 2: a weekly run of cement]
I should plan the routes for the truck fleet  , where I need to be smart enough to optimize the time for vaccines and diesel and toll bills for cement , the insisted route is the Delhi Mumbai expressway is faster even tho it is longer 

the dataset _national_highways (in excel format)________ is being uploaded 
 dataset = "C:\Users\exam.cb\karthik pro\national_highways.xlsx"

I should model the highway network as a graph , where every city becomes the nodes and every highway link becomes an edge with its highway code , its distance in km , its average in km , its average truck speed in k /h and its toll in INR , by evening you must assign one route to each consignment and have a backup plan in case a monsoon landslide closes the Mumbai - Pune  expressway

these are the ideas and real world scenario  for which I need to provide the best powerful most efficient and effective solution 

TASKS I NEED TO ACHIEVE 

1) Analyse the data and identity trends using pandas
2) Build the graph , where loading the dataset , add a travel- time column (hours = distance / speed , rounded to 2 decimals)
 and build G will all 4 edges attributes . Print its size and confirm it has 46 cities and 52 links and that it is connected 
3) Describe the network
 a) list every city with degree >= 3 and report the density and average degree 
 b) compute betweenness centrality with weight="distance" and list the top 5 cities , explain in 2-3 sentences what a high value means for the truck fleet
 c) write the edge attribute vector w(e) = (d(e) , t(e) . tow(e)) fro one link of any choice , with its actual values

4) Trace Dijkratra (Using hand )  this is the only task which i need to draw it manually on paper for which i want to provide/ guide  the best accurate graph 
    
use the  content of the sub- graph provided pasted as the image  

  

   a ) draw the sub - graph and fill in an iteration table : the node visited at each step and the tentative distance of evey node after tha step 
   b ) write  the relaxation rule being applied 
   c ) verify  the final distance and paths with nx.single_source_dijkstra on G.subgraph() 

5) Distance vs time vs toll for Delhi -> Bengaluru 
  a . find the route with the shortest distance , the fastest route , and the cheapest route by toll
  b . for each , report the route toll km , total hours , total toll (INR)  , also explain why the shortest and fastest routes differ

6 ) expressway closure . A landslide closes the Mumbai - Pune expressway 
    a) remove that edge from a copy of G and recompute the fastest Delhi -> Bengaluru route
    b) report on the new route and how its time , distance and toll change compared with Task 4's fastest route differ 
7 Visualize 
 a) Draw he network and highlight the shortest  and fastest Delhi -> Bengaluru routes 
 b) Draw a grouped horizontal bar chart comparing the shortest and fastest routes on distance , time toll , normalize or use separate axes so all three metrices are      readable  


8 ) recommendation . IN 150- 200 words ADVISE THE COMPANY WHICH ROUTE TO ASSIGN TO COLD - CHAIN VACCINES AND WHICH TO BULK DRY FREIGHT ( for example , cement ) Support i choose with my computed numbers



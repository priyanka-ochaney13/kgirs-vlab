"""
Virtual Lab CA - Experiment
Title      : Create and Manage a Graph Database
Course     : Virtual Labs (as per IIT Kharagpur Virtual Labs format)
Description: This Streamlit application reproduces the standard sections of an
             IIT Kharagpur Virtual Lab experiment page (Aim, Objective, Theory,
             Procedure, Pretest, Simulator, Posttest, References) for the
             experiment "Create and Manage a Graph Database".

             Instead of installing and running an actual Neo4j server, the
             graph database is simulated in-memory using plain Python data
             structures (dictionaries/lists), and visualised with NetworkX +
             Matplotlib. This keeps the app self-contained, lightweight, and
             runnable with a single `streamlit run vlab.py`
             command, with no external database server or Neo4j installation
             required, as permitted by the experiment guidelines.

Run with   : streamlit run vlab.py
Requires   : streamlit, networkx, matplotlib
"""

import re
from dataclasses import dataclass, field

import matplotlib.pyplot as plt
import networkx as nx
import streamlit as st

# --------------------------------------------------------------------------
# Page configuration
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Virtual Lab | Create and Manage a Graph Database",
    layout="wide",
    initial_sidebar_state="expanded",
)

NODE_COLOR_PALETTE = [
    "#4C72B0", "#DD8452", "#55A868", "#C44E52",
    "#8172B2", "#937860", "#DA8BC3", "#8C8C8C",
]


# --------------------------------------------------------------------------
# In-memory Graph Database (simulated, Neo4j-free)
# --------------------------------------------------------------------------
@dataclass
class GraphDB:
    """A tiny in-memory property-graph engine.

    Nodes are stored as: {node_id: {"labels": [..], "properties": {..}}}
    Edges are stored as a list of: {"src", "dst", "type", "properties"}
    This mirrors the core concepts of a graph database (nodes, labels,
    relationships, properties) without depending on Neo4j.
    """

    nodes: dict = field(default_factory=dict)
    edges: list = field(default_factory=list)
    _next_id: int = 0

    def add_node(self, label: str, properties: dict) -> int:
        node_id = self._next_id
        self.nodes[node_id] = {"labels": [label] if label else [], "properties": dict(properties)}
        self._next_id += 1
        return node_id

    def delete_node(self, node_id: int) -> None:
        self.nodes.pop(node_id, None)
        self.edges = [e for e in self.edges if e["src"] != node_id and e["dst"] != node_id]

    def add_edge(self, src: int, dst: int, rel_type: str, properties: dict) -> None:
        self.edges.append({"src": src, "dst": dst, "type": rel_type, "properties": dict(properties)})

    def delete_edge(self, index: int) -> None:
        if 0 <= index < len(self.edges):
            self.edges.pop(index)

    def update_node_property(self, node_id: int, key: str, value: str) -> None:
        if node_id in self.nodes:
            self.nodes[node_id]["properties"][key] = value

    def neighbors(self, node_id: int) -> list:
        result = []
        for e in self.edges:
            if e["src"] == node_id:
                result.append((e["dst"], e["type"], "out"))
            elif e["dst"] == node_id:
                result.append((e["src"], e["type"], "in"))
        return result

    def shortest_path(self, src: int, dst: int):
        g = nx.Graph()
        g.add_nodes_from(self.nodes.keys())
        g.add_edges_from([(e["src"], e["dst"]) for e in self.edges])
        try:
            return nx.shortest_path(g, source=src, target=dst)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def to_networkx(self) -> nx.DiGraph:
        g = nx.DiGraph()
        for nid, data in self.nodes.items():
            label = data["labels"][0] if data["labels"] else "Node"
            name = data["properties"].get("name", str(nid))
            g.add_node(nid, label=label, name=name)
        for e in self.edges:
            g.add_edge(e["src"], e["dst"], type=e["type"])
        return g

    def node_display(self, node_id: int) -> str:
        data = self.nodes.get(node_id, {})
        label = data.get("labels", ["?"])[0] if data.get("labels") else "?"
        name = data.get("properties", {}).get("name", "")
        return f"#{node_id} ({label}" + (f': "{name}"' if name else "") + ")"


# --------------------------------------------------------------------------
# Tiny Cypher-like command parser (for the "query console" tab)
#   CREATE (label {key:"value", key2:"value2"})
#   MATCH (a)-[:REL_TYPE]->(b) WHERE a.name="X" AND b.name="Y"
# --------------------------------------------------------------------------
CREATE_NODE_RE = re.compile(r'^\s*CREATE\s*\(\s*(\w+)?\s*(\{.*\})?\s*\)\s*$', re.IGNORECASE)
CREATE_REL_RE = re.compile(
    r'^\s*CREATE\s*\(\s*(\w+)\s*\)\s*-\[\s*:?\s*(\w+)\s*\]->\s*\(\s*(\w+)\s*\)\s*$',
    re.IGNORECASE,
)


def _parse_props(prop_str: str) -> dict:
    props = {}
    if not prop_str:
        return props
    body = prop_str.strip().lstrip("{").rstrip("}")
    if not body.strip():
        return props
    for part in body.split(","):
        if ":" not in part:
            continue
        k, v = part.split(":", 1)
        props[k.strip()] = v.strip().strip('"').strip("'")
    return props


def run_command(db: GraphDB, name_to_id: dict, command: str) -> str:
    """Interpret a single simplified Cypher-style command against the GraphDB."""
    m = CREATE_NODE_RE.match(command)
    if m:
        label, prop_str = m.group(1) or "Node", m.group(2)
        props = _parse_props(prop_str)
        node_id = db.add_node(label, props)
        if "name" in props:
            name_to_id[props["name"]] = node_id
        return f"Created node {db.node_display(node_id)}"

    m = CREATE_REL_RE.match(command)
    if m:
        a_ref, rel_type, b_ref = m.group(1), m.group(2), m.group(3)
        src = name_to_id.get(a_ref)
        dst = name_to_id.get(b_ref)
        if src is None or dst is None:
            return "Error: unknown node reference. Create nodes with a matching 'name' property first."
        db.add_edge(src, dst, rel_type, {})
        return f"Created relationship {db.node_display(src)} -[{rel_type}]-> {db.node_display(dst)}"

    return "Error: command not recognised. Supported: CREATE (Label {name:\"X\"})  |  CREATE (X)-[:REL]->(Y)"


# --------------------------------------------------------------------------
# Session state initialisation
# --------------------------------------------------------------------------
if "db" not in st.session_state:
    st.session_state.db = GraphDB()
if "name_to_id" not in st.session_state:
    st.session_state.name_to_id = {}
if "console_log" not in st.session_state:
    st.session_state.console_log = []
if "pretest_submitted" not in st.session_state:
    st.session_state.pretest_submitted = False
if "posttest_submitted" not in st.session_state:
    st.session_state.posttest_submitted = False


def load_sample_graph() -> None:
    """Loads a small demo graph (kept intentionally small - few nodes)."""
    db = GraphDB()
    name_to_id = {}
    people = ["Alice", "Bob", "Carol"]
    for p in people:
        nid = db.add_node("Person", {"name": p})
        name_to_id[p] = nid
    org_id = db.add_node("Company", {"name": "Acme Corp"})
    name_to_id["Acme Corp"] = org_id

    db.add_edge(name_to_id["Alice"], name_to_id["Bob"], "FRIENDS_WITH", {})
    db.add_edge(name_to_id["Bob"], name_to_id["Carol"], "FRIENDS_WITH", {})
    db.add_edge(name_to_id["Alice"], name_to_id["Acme Corp"], "WORKS_AT", {"role": "Engineer"})
    db.add_edge(name_to_id["Carol"], name_to_id["Acme Corp"], "WORKS_AT", {"role": "Designer"})

    st.session_state.db = db
    st.session_state.name_to_id = name_to_id
    st.session_state.console_log = ["-- Sample graph loaded (4 nodes, 4 relationships) --"]


def draw_graph(db: GraphDB):
    g = db.to_networkx()
    fig, ax = plt.subplots(figsize=(7, 5))
    if len(g.nodes) == 0:
        ax.text(0.5, 0.5, "Graph is empty.\nAdd nodes to get started.",
                 ha="center", va="center", fontsize=12)
        ax.axis("off")
        return fig

    pos = nx.spring_layout(g, seed=42, k=0.9)
    labels_seen = {}
    node_colors = []
    for n in g.nodes:
        lbl = g.nodes[n]["label"]
        if lbl not in labels_seen:
            labels_seen[lbl] = NODE_COLOR_PALETTE[len(labels_seen) % len(NODE_COLOR_PALETTE)]
        node_colors.append(labels_seen[lbl])

    nx.draw_networkx_nodes(g, pos, node_size=1400, node_color=node_colors, ax=ax, alpha=0.9)
    nx.draw_networkx_labels(
        g, pos,
        labels={n: g.nodes[n]["name"] for n in g.nodes},
        font_size=9, font_color="white", ax=ax,
    )
    nx.draw_networkx_edges(g, pos, ax=ax, arrows=True, arrowsize=18,
                            connectionstyle="arc3,rad=0.08", edge_color="#555555")
    edge_labels = {(u, v): d["type"] for u, v, d in g.edges(data=True)}
    nx.draw_networkx_edge_labels(g, pos, edge_labels=edge_labels, font_size=8, ax=ax)

    handles = [plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=c, markersize=10, label=lbl)
               for lbl, c in labels_seen.items()]
    ax.legend(handles=handles, loc="upper left", fontsize=8, title="Node labels")
    ax.axis("off")
    fig.tight_layout()
    return fig


# --------------------------------------------------------------------------
# Sidebar navigation
# --------------------------------------------------------------------------
st.sidebar.title("Virtual Lab CA")
st.sidebar.caption("Experiment: Create and Manage a Graph Database")
section = st.sidebar.radio(
    "Go to section",
    ["Aim & Objective", "Theory", "Procedure", "Pretest",
     "Simulator", "Posttest", "References"],
)
st.sidebar.markdown("---")


# --------------------------------------------------------------------------
# Section: Aim & Objective
# --------------------------------------------------------------------------
if section == "Aim & Objective":
    st.title("Create and Manage a Graph Database")
    st.subheader("Aim")
    st.write(
        "To understand the fundamentals of graph databases by creating nodes, "
        "defining relationships between them, and performing basic graph "
        "operations, resulting in a functioning graph database of connected entities."
    )

    st.subheader("Objective")
    st.markdown(
        "- Understand what a graph database is and how it differs from a relational database.\n"
        "- Learn the core building blocks of a property graph: **nodes**, **labels**, "
        "**relationships**, and **properties**.\n"
        "- Create, read, update, and delete (CRUD) nodes and relationships.\n"
        "- Query the graph for neighbors and shortest paths between entities.\n"
        "- Visualize the resulting graph structure."
    )

    st.subheader("Expected Outcome")
    st.info("A functioning graph database containing connected entities.")

    st.subheader("Note on Tooling")
    st.write(
        "This experiment is normally carried out by installing Neo4j and using the "
        "Cypher query language. In this Virtual Lab implementation, the same "
        "concepts (nodes, relationships, properties, and graph queries) are "
        "simulated directly in Python and rendered with NetworkX/Matplotlib, "
        "so the experiment can be run and graded without a Neo4j server installation."
    )

# --------------------------------------------------------------------------
# Section: Theory
# --------------------------------------------------------------------------
elif section == "Theory":
    st.title("Theory")

    st.markdown("### 1. What is a Graph Database?")
    st.write(
        "A graph database is a type of NoSQL database that uses graph structures "
        "(nodes, edges/relationships, and properties) to represent and store data. "
        "Unlike relational databases, which store data in rows and tables and use "
        "foreign keys and joins to represent relationships, a graph database stores "
        "relationships as first-class citizens, making it efficient for highly "
        "connected data such as social networks, recommendation engines, and "
        "knowledge graphs."
    )

    st.markdown("### 2. Core Concepts")
    st.markdown(
        "- **Node**: Represents an entity (e.g., a Person, a Company). "
        "A node can have one or more **labels** that categorize it.\n"
        "- **Relationship**: A directed, typed connection between two nodes "
        "(e.g., `Alice -[:FRIENDS_WITH]-> Bob`). Relationships can also hold properties.\n"
        "- **Property**: A key-value pair attached to a node or relationship "
        "(e.g., `name: \"Alice\"`, `role: \"Engineer\"`).\n"
        "- **Traversal**: The process of navigating from one node to another "
        "by following relationships — the fundamental operation in graph queries."
    )

    st.markdown("### 3. Neo4j and Cypher (Reference)")
    st.write(
        "Neo4j is one of the most widely used native graph database management "
        "systems. It uses the Cypher query language, whose syntax reads similarly "
        "to drawing the graph in ASCII form."
    )
    st.code(
        'CREATE (a:Person {name: "Alice"})\n'
        'CREATE (b:Person {name: "Bob"})\n'
        'CREATE (a)-[:FRIENDS_WITH]->(b)\n'
        'MATCH (p:Person)-[:FRIENDS_WITH]->(q:Person) RETURN p, q',
        language="cypher",
    )
    st.write(
        "This Virtual Lab simulator uses a simplified version of the same "
        "syntax (see the **Simulator → Command Console** tab) so that the "
        "conceptual mapping to Neo4j/Cypher remains clear."
    )

    st.markdown("### 4. Common Graph Operations")
    st.markdown(
        "- **Create** a node / relationship.\n"
        "- **Read** node and relationship properties.\n"
        "- **Update** a property on an existing node.\n"
        "- **Delete** a node or relationship.\n"
        "- **Query neighbors** of a node (adjacent nodes).\n"
        "- **Find shortest path** between two nodes."
    )

    st.markdown("### 5. Applications of Graph Databases")
    st.markdown(
        "- Social networks (friend/follower graphs)\n"
        "- Recommendation systems\n"
        "- Fraud detection\n"
        "- Knowledge graphs and semantic search\n"
        "- Network and IT infrastructure mapping"
    )

# --------------------------------------------------------------------------
# Section: Procedure
# --------------------------------------------------------------------------
elif section == "Procedure":
    st.title("Procedure")
    st.markdown(
        "1. Go to the **Simulator** section from the sidebar.\n"
        "2. (Optional) Click **Load Sample Graph** to see a small pre-built "
        "graph of connected entities.\n"
        "3. Use the **Add Node** panel to create nodes: choose a label "
        "(e.g., Person, Company) and enter properties such as `name`.\n"
        "4. Use the **Add Relationship** panel to connect two existing nodes "
        "with a directed, typed relationship (e.g., `FRIENDS_WITH`, `WORKS_AT`).\n"
        "5. Observe the graph visualization update automatically after every "
        "create/update/delete operation.\n"
        "6. Use the **Query** panel to look up the neighbors of a node, or "
        "find the shortest path between two nodes.\n"
        "7. Use the **Command Console** tab to try Cypher-style commands "
        "directly, mirroring how the same task would be done in Neo4j.\n"
        "8. Use the **Update / Delete** panel to modify a node's property or "
        "remove a node/relationship, and confirm the graph updates correctly.\n"
        "9. Attempt the **Pretest** before starting the simulation and the "
        "**Posttest** after completing it, to self-assess understanding."
    )

# --------------------------------------------------------------------------
# Section: Pretest
# --------------------------------------------------------------------------
elif section == "Pretest":
    st.title("Pretest")
    st.write("Answer the following questions before you begin the simulation.")

    q1 = st.radio(
        "1. In a graph database, a relationship is best described as:",
        ["A row in a table", "A directed, typed connection between two nodes",
         "A column constraint", "An index on a property"],
        index=None, key="pre_q1",
    )
    q2 = st.radio(
        "2. Which of these is NOT a core component of a property graph?",
        ["Node", "Relationship", "Property", "Foreign Key"],
        index=None, key="pre_q2",
    )
    q3 = st.radio(
        "3. Neo4j's query language is called:",
        ["SQL", "Cypher", "SPARQL", "GraphQL"],
        index=None, key="pre_q3",
    )

    if st.button("Submit Pretest"):
        st.session_state.pretest_submitted = True

    if st.session_state.pretest_submitted:
        score = 0
        score += q1 == "A directed, typed connection between two nodes"
        score += q2 == "Foreign Key"
        score += q3 == "Cypher"
        st.success(f"Score: {score} / 3")

# --------------------------------------------------------------------------
# Section: Simulator
# --------------------------------------------------------------------------
elif section == "Simulator":
    st.title("Simulator: Graph Database Operations")

    db: GraphDB = st.session_state.db
    name_to_id: dict = st.session_state.name_to_id

    top_col1, top_col2 = st.columns([1, 3])
    with top_col1:
        if st.button("Load Sample Graph"):
            load_sample_graph()
            st.rerun()
        if st.button("Clear Graph"):
            st.session_state.db = GraphDB()
            st.session_state.name_to_id = {}
            st.session_state.console_log = []
            st.rerun()

    with top_col2:
        st.caption(
            f"Current graph: **{len(db.nodes)} node(s)**, **{len(db.edges)} relationship(s)**."
        )

    tab_graph, tab_crud, tab_query, tab_console = st.tabs(
        ["Graph View", "Create / Update / Delete", "Query", "Command Console"]
    )

    # ---- Graph View ----
    with tab_graph:
        fig = draw_graph(db)
        st.pyplot(fig)

    # ---- Create / Update / Delete ----
    with tab_crud:
        st.markdown("#### Add Node")
        with st.form("add_node_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                new_label = st.text_input("Label (e.g., Person, Company)", value="Person")
            with c2:
                new_name = st.text_input("name property (used as node identifier)")
            extra_props = st.text_input(
                "Additional properties (comma-separated key=value pairs, optional)",
                placeholder="role=Engineer, age=25",
            )
            submitted_node = st.form_submit_button("Create Node")
            if submitted_node:
                props = {}
                if new_name:
                    props["name"] = new_name
                if extra_props.strip():
                    for pair in extra_props.split(","):
                        if "=" in pair:
                            k, v = pair.split("=", 1)
                            props[k.strip()] = v.strip()
                node_id = db.add_node(new_label.strip() or "Node", props)
                if new_name:
                    name_to_id[new_name] = node_id
                st.success(f"Created node {db.node_display(node_id)}")
                st.rerun()

        st.markdown("---")
        st.markdown("#### Add Relationship")
        if len(db.nodes) < 2:
            st.warning("Create at least two nodes first.")
        else:
            options = {db.node_display(nid): nid for nid in db.nodes}
            with st.form("add_edge_form", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                with c1:
                    src_label = st.selectbox("From node", list(options.keys()), key="edge_src")
                with c2:
                    rel_type = st.text_input("Relationship type", value="RELATED_TO")
                with c3:
                    dst_label = st.selectbox("To node", list(options.keys()), key="edge_dst")
                submitted_edge = st.form_submit_button("Create Relationship")
                if submitted_edge:
                    db.add_edge(options[src_label], options[dst_label], rel_type.strip() or "RELATED_TO", {})
                    st.success(f"Created relationship: {src_label} -[{rel_type}]-> {dst_label}")
                    st.rerun()

        st.markdown("---")
        st.markdown("#### Update Node Property")
        if db.nodes:
            options = {db.node_display(nid): nid for nid in db.nodes}
            c1, c2, c3 = st.columns(3)
            with c1:
                upd_label = st.selectbox("Node", list(options.keys()), key="upd_node")
            with c2:
                upd_key = st.text_input("Property key", key="upd_key")
            with c3:
                upd_value = st.text_input("New value", key="upd_value")
            if st.button("Update Property"):
                if upd_key:
                    db.update_node_property(options[upd_label], upd_key, upd_value)
                    st.success(f"Updated '{upd_key}' on {upd_label}")
                    st.rerun()

        st.markdown("---")
        st.markdown("#### Delete Node / Relationship")
        c1, c2 = st.columns(2)
        with c1:
            if db.nodes:
                options = {db.node_display(nid): nid for nid in db.nodes}
                del_node_label = st.selectbox("Node to delete", list(options.keys()), key="del_node")
                if st.button("Delete Node"):
                    db.delete_node(options[del_node_label])
                    st.success(f"Deleted {del_node_label}")
                    st.rerun()
        with c2:
            if db.edges:
                edge_labels = [
                    f"[{i}] {db.node_display(e['src'])} -[{e['type']}]-> {db.node_display(e['dst'])}"
                    for i, e in enumerate(db.edges)
                ]
                del_edge_label = st.selectbox("Relationship to delete", edge_labels, key="del_edge")
                if st.button("Delete Relationship"):
                    idx = int(del_edge_label.split("]")[0].strip("["))
                    db.delete_edge(idx)
                    st.success("Deleted relationship")
                    st.rerun()

    # ---- Query ----
    with tab_query:
        st.markdown("#### Neighbors of a Node")
        if db.nodes:
            options = {db.node_display(nid): nid for nid in db.nodes}
            q_node_label = st.selectbox("Select node", list(options.keys()), key="q_neighbor_node")
            if st.button("Find Neighbors"):
                nid = options[q_node_label]
                nbrs = db.neighbors(nid)
                if nbrs:
                    for other_id, rel, direction in nbrs:
                        arrow = "→" if direction == "out" else "←"
                        st.write(f"{q_node_label} {arrow} [{rel}] {arrow} {db.node_display(other_id)}")
                else:
                    st.info("No neighbors found.")
        else:
            st.info("Create some nodes first.")

        st.markdown("---")
        st.markdown("#### Shortest Path Between Two Nodes")
        if len(db.nodes) >= 2:
            options = {db.node_display(nid): nid for nid in db.nodes}
            c1, c2 = st.columns(2)
            with c1:
                sp_src_label = st.selectbox("From", list(options.keys()), key="sp_src")
            with c2:
                sp_dst_label = st.selectbox("To", list(options.keys()), key="sp_dst")
            if st.button("Find Shortest Path"):
                path = db.shortest_path(options[sp_src_label], options[sp_dst_label])
                if path:
                    st.success(" → ".join(db.node_display(n) for n in path))
                else:
                    st.warning("No path exists between the selected nodes.")

    # ---- Command Console ----
    with tab_console:
        st.markdown(
            "Enter simplified Cypher-style commands. Supported forms:\n\n"
            '`CREATE (Label {name:"X"})`  and  `CREATE (X)-[:REL_TYPE]->(Y)`'
        )
        command = st.text_input("Command", placeholder='CREATE (Person {name:"Dave"})')
        if st.button("Run Command"):
            if command.strip():
                output = run_command(db, name_to_id, command.strip())
                st.session_state.console_log.append(f"> {command}")
                st.session_state.console_log.append(output)
                st.rerun()

        st.markdown("##### Console Log")
        st.code("\n".join(st.session_state.console_log) if st.session_state.console_log else "(empty)")

# --------------------------------------------------------------------------
# Section: Posttest
# --------------------------------------------------------------------------
elif section == "Posttest":
    st.title("Posttest")
    st.write("Answer the following questions after completing the simulation.")

    p1 = st.radio(
        "1. If node A has an outgoing relationship to node B, this is written as:",
        ["B -> A", "A -> B", "A <-> B", "A = B"],
        index=None, key="post_q1",
    )
    p2 = st.radio(
        "2. Finding the shortest sequence of relationships connecting two nodes is called:",
        ["Indexing", "Sharding", "Path finding / traversal", "Normalization"],
        index=None, key="post_q2",
    )
    p3 = st.radio(
        "3. Which statement about graph databases is TRUE?",
        [
            "They cannot store properties on relationships",
            "They are best suited for highly connected data",
            "They always require a fixed schema like relational tables",
            "They cannot represent directed relationships",
        ],
        index=None, key="post_q3",
    )

    if st.button("Submit Posttest"):
        st.session_state.posttest_submitted = True

    if st.session_state.posttest_submitted:
        score = 0
        score += p1 == "A -> B"
        score += p2 == "Path finding / traversal"
        score += p3 == "They are best suited for highly connected data"
        st.success(f"Score: {score} / 3")

# --------------------------------------------------------------------------
# Section: References
# --------------------------------------------------------------------------
elif section == "References":
    st.title("References")
    st.markdown(
        "- Neo4j Documentation: Graph Database Concepts — https://neo4j.com/docs/getting-started/graph-database/\n"
        "- Neo4j Cypher Manual — https://neo4j.com/docs/cypher-manual/current/\n"
        "- NetworkX Documentation — https://networkx.org/documentation/stable/\n"
        "- IIT Kharagpur Virtual Labs — https://vlab.co.in/\n"
        "- Robinson, I., Webber, J., & Eifrem, E. *Graph Databases* (2nd ed.), O'Reilly Media."
    )
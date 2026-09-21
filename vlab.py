"""
Virtual Laboratory Experiment (Streamlit)
Experiment 8 : Create and Manage a Graph Database
Roll Nos     : 36, 38, 39, 40
Aim          : Create nodes and relationships, and perform basic graph operations.
Outcome      : A functioning graph database containing connected entities.

Sections (in the sequence required for all Virtual Lab experiments):
  1. Purpose            : Aim, expected outcome, learning objectives.
  2. Theory             : Background, experimental procedure, key terms.
  3. Simulation         : In-memory graph database (nodes, relationships, CRUD, queries, command
                          console), interactive Plotly graph visualisation and metrics.
  4. Quiz               : 10 random questions drawn from a 50-question bank (quiz_questions.json),
                          self-graded with instant feedback.
  5. Report Generation  : Student info, observations, downloadable PDF report
                          (includes the final graph diagram).
  6. Certificate        : Downloadable certificate of completion (PDF).
  7. References         : Sources used for this experiment.

The graph database is simulated in memory with plain Python data structures, so no database
server is needed.

Run with : streamlit run vlab.py
Files    : vlab.py and quiz_questions.json (keep both in the same folder)
Requires : pip install streamlit networkx matplotlib pandas plotly fpdf2
"""

import html
import io
import json
import os
import random
import re
import textwrap
import math
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from fpdf import FPDF


# ======================================================================================
# 1. EXPERIMENT CONFIGURATION & EDUCATIONAL CONTENT
# ======================================================================================

LAB_NAME = "KGIRS Virtual Lab"

# Section order required for every experiment in the Virtual Lab
SECTIONS = ["Purpose", "Theory", "Simulation", "Quiz", "Report Generation", "Certificate", "References"]

# True  = the certificate unlocks only after the quiz has been submitted
# False = students can download it any time
CERTIFICATE_REQUIRES_QUIZ = True

EXPERIMENT_CONFIG = {
    "number": 8,
    "title": "Create and Manage a Graph Database",
    "roll_numbers": "36, 38, 39, 40",
    "aim": "Create nodes and relationships, and perform basic graph operations.",
    "expected_outcome": "A functioning graph database containing connected entities.",
    "objectives": [
        "Understand what a graph database is and how it differs from a relational database.",
        "Learn the building blocks of a property graph: nodes, labels, relationships and properties.",
        "Create, read, update and delete (CRUD) nodes and relationships.",
        "Query the graph for neighbors and shortest paths between entities.",
        "Visualize the resulting graph and record observations in a lab report."
    ]
}

FULL_TITLE = f"Experiment {EXPERIMENT_CONFIG['number']}: {EXPERIMENT_CONFIG['title']}"

THEORY_CONTENT = {
    "background": """
### Overview & Principles
A **graph database** stores data as a network: **nodes** represent entities, **relationships**
connect them, and **properties** describe both. Because relationships are stored directly instead of
being rebuilt through joins, graph databases handle highly connected data (social networks,
recommendations, fraud detection, knowledge graphs) efficiently.

| Aspect | Relational database | Graph database |
|---|---|---|
| Data model | Rows in tables | Nodes and relationships |
| Connections | Foreign keys and JOINs | Stored directly as relationships |
| Schema | Fixed | Flexible |
| Connected queries | Slow as joins get deeper | Traversals stay fast |

### Querying a Graph
Graph queries describe patterns instead of tables. A pattern reads like an ASCII drawing of the
graph, with nodes in parentheses and relationships in square brackets:

```text
CREATE (a:Person {name: "Alice"})
CREATE (b:Person {name: "Bob"})
CREATE (a)-[:FRIENDS_WITH]->(b)
MATCH (p:Person)-[:FRIENDS_WITH]->(q:Person) RETURN p, q
```

### Note on this Virtual Lab
The simulator implements these concepts (nodes, labels, relationships, properties, traversal)
with an in-memory Python graph and a command console that accepts commands like the ones above,
so no database server is needed.

### Workflow & System Overview
1. **Create**: Add nodes (with a label and properties) and connect them with typed relationships.
2. **Manage**: Update properties, delete nodes or relationships, and watch the graph change.
3. **Query**: Find the neighbors of a node and the shortest path between two nodes.
    """,
    "procedure": [
        "Step 1: Review the purpose, theoretical background and key terminology.",
        "Step 2: Navigate to the Simulation section in the sidebar menu.",
        "Step 3: Optionally click 'Load Sample Graph' to start from a small pre-built graph.",
        "Step 4: In 'Create / Update / Delete', add nodes with a label and a name property.",
        "Step 5: Connect nodes by creating typed, directed relationships (e.g. FRIENDS_WITH).",
        "Step 6: Update a node property, then delete a node or relationship and observe the graph.",
        "Step 7: In 'Query', find the neighbors of a node and the shortest path between two nodes.",
        "Step 8: In 'Command Console', try graph query commands such as CREATE and MATCH.",
        "Step 9: Complete the assessment Quiz to test your conceptual understanding.",
        "Step 10: Open Report Generation, enter your details, and download your PDF report.",
        "Step 11: Open Certificate to download your certificate of completion."
    ],
    "key_terms": {
        "Node": "An entity in the graph (e.g. a Person or a Company).",
        "Label": "A tag that categorizes a node (e.g. Person, Company).",
        "Relationship": "A directed, typed connection between two nodes (e.g. FRIENDS_WITH).",
        "Property": "A key-value pair stored on a node or relationship (e.g. name: \"Alice\").",
        "Traversal": "Navigating from node to node by following relationships.",
        "Shortest Path": "The fewest-hop chain of relationships connecting two nodes."
    }
}

REFERENCES = [
    "Angles, R., & Gutierrez, C. (2008). Survey of graph database models. "
    "*ACM Computing Surveys*, 40(1).",
    "Robinson, I., Webber, J., & Eifrem, E. (2015). *Graph Databases* (2nd ed.). O'Reilly Media.",
    "NetworkX Documentation: https://networkx.org/documentation/stable/",
    "Plotly Python Documentation: https://plotly.com/python/",
    "Streamlit Documentation: https://docs.streamlit.io/",
]

SIMULATION_CONFIG = {
    "default_node_label": "Person",
    "default_rel_type": "RELATED_TO",
    "sample_nodes": [
        ("Person", {"name": "Priyanka"}),
        ("Person", {"name": "Supriya"}),
        ("Person", {"name": "Amogh"}),
        ("Person", {"name": "Akshit"}),
    ],
    "sample_edges": [
        ("Priyanka", "Supriya", "FRIENDS_WITH", {}),
        ("Supriya", "Amogh", "FRIENDS_WITH", {}),
        ("Priyanka", "Akshit", "FRIENDS_WITH", {}),
        ("Amogh", "Akshit", "FRIENDS_WITH", {}),
    ],
    "console_examples": [
        'CREATE (:Person {name:"Dave"})',
        'CREATE (Dave)-[:FRIENDS_WITH]->(Alice)',
        'MATCH (n:Person) RETURN n',
        'MATCH (a)-[r:FRIENDS_WITH]->(b) RETURN a, r, b',
        'MATCH (n {name:"Dave"}) DETACH DELETE n',
    ],
}

# ---- Quiz bank: 50 questions live in quiz_questions.json, 10 are picked at random per session ----
QUIZ_FILE = Path(__file__).with_name("quiz_questions.json")
QUIZ_SIZE = 10


@st.cache_data
def load_quiz_bank() -> list:
    with open(QUIZ_FILE, encoding="utf-8") as f:
        return json.load(f)


def pick_quiz_questions(n: int = QUIZ_SIZE) -> list:
    """Picks n random questions from the bank and renumbers them 1..n for this session."""
    bank = load_quiz_bank()
    picked = random.sample(bank, min(n, len(bank)))
    return [{**q, "id": i} for i, q in enumerate(picked, start=1)]


def quiz_questions() -> list:
    """The 10 questions drawn for the current session."""
    return st.session_state["quiz_questions"]


NODE_COLOR_PALETTE = [
    "#4C72B0", "#DD8452", "#55A868", "#C44E52",
    "#8172B2", "#937860", "#DA8BC3", "#8C8C8C",
]

# Graph drawing constants (shared by the interactive Plotly view and the PDF image)
EDGE_COLOR = "#6b7280"
EDGE_CURVE = 0.25  # bend used only when two nodes point at each other
PLOTLY_CONFIG = {"displaylogo": False, "scrollZoom": True,
                 "modeBarButtonsToRemove": ["select2d", "lasso2d"]}


# ======================================================================================
# 2. SIMULATION ENGINE: IN-MEMORY GRAPH DATABASE + PATTERN-STYLE PARSER
# ======================================================================================

@dataclass
class GraphDB:
    """A tiny in-memory property-graph engine (nodes, labels, relationships, properties).

    Nodes are stored as: {node_id: {"labels": [..], "properties": {..}}}
    Edges are stored as a list of: {"src", "dst", "type", "properties"}
    """

    nodes: dict = field(default_factory=dict)
    edges: list = field(default_factory=list)
    _next_id: int = 0

    # ---- Create / Update / Delete ----
    def add_node(self, label: str, properties: dict) -> int:
        node_id = self._next_id
        self.nodes[node_id] = {"labels": [label] if label else [], "properties": dict(properties)}
        self._next_id += 1
        return node_id

    def delete_node(self, node_id: int) -> None:
        """Deletes a node together with every relationship attached to it (DETACH DELETE)."""
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

    # ---- Read / Query ----
    def find_by_name(self, name: str) -> Optional[int]:
        for node_id, data in self.nodes.items():
            if data["properties"].get("name") == name:
                return node_id
        return None

    def neighbors(self, node_id: int) -> list:
        result = []
        for e in self.edges:
            if e["src"] == node_id:
                result.append((e["dst"], e["type"], "out"))
            elif e["dst"] == node_id:
                result.append((e["src"], e["type"], "in"))
        return result

    def shortest_path(self, src: int, dst: int):
        """Shortest path treating relationships as undirected (fewest hops)."""
        g = nx.Graph()
        g.add_nodes_from(self.nodes.keys())
        g.add_edges_from([(e["src"], e["dst"]) for e in self.edges])
        try:
            return nx.shortest_path(g, source=src, target=dst)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    # ---- Presentation helpers ----
    def label_of(self, node_id: int) -> str:
        data = self.nodes.get(node_id)
        if data and data["labels"]:
            return data["labels"][0]
        return "Node"

    def node_name(self, node_id: int) -> str:
        data = self.nodes.get(node_id, {})
        return str(data.get("properties", {}).get("name", f"#{node_id}"))

    def node_display(self, node_id: int) -> str:
        if node_id not in self.nodes:
            return f"#{node_id} (deleted)"
        name = self.nodes[node_id]["properties"].get("name", "")
        return f"#{node_id} ({self.label_of(node_id)}" + (f': "{name}"' if name else "") + ")"

    def to_networkx(self) -> nx.DiGraph:
        g = nx.DiGraph()
        for nid in self.nodes:
            g.add_node(nid, label=self.label_of(nid), name=self.node_name(nid))
        for e in self.edges:
            if g.has_edge(e["src"], e["dst"]):
                g[e["src"]][e["dst"]]["type"] += f", {e['type']}"
            else:
                g.add_edge(e["src"], e["dst"], type=e["type"])
        return g

    def nodes_table(self) -> pd.DataFrame:
        rows = [
            {
                "ID": nid,
                "Label": self.label_of(nid),
                "Properties": ", ".join(f"{k}={v}" for k, v in data["properties"].items()),
            }
            for nid, data in self.nodes.items()
        ]
        return pd.DataFrame(rows, columns=["ID", "Label", "Properties"])

    def edges_table(self) -> pd.DataFrame:
        rows = [
            {
                "From": self.node_name(e["src"]),
                "Relationship": e["type"],
                "To": self.node_name(e["dst"]),
                "Properties": ", ".join(f"{k}={v}" for k, v in e["properties"].items()),
            }
            for e in self.edges
        ]
        return pd.DataFrame(rows, columns=["From", "Relationship", "To", "Properties"])


# ---- Simplified pattern-style parser (used by the Command Console) ----
_NODE = r"\(\s*(?:(\w+)\s*)?(?::\s*(\w+)\s*)?(\{[^}]*\})?\s*\)"
CREATE_NODE_RE = re.compile(rf"^CREATE\s*{_NODE}$", re.IGNORECASE)
CREATE_REL_RE = re.compile(
    r"^CREATE\s*\(\s*([^)]+?)\s*\)\s*-\s*\[\s*(?:\w+)?\s*:\s*(\w+)\s*(\{[^}]*\})?\s*\]\s*->\s*\(\s*([^)]+?)\s*\)$",
    re.IGNORECASE,
)
MATCH_NODES_RE = re.compile(rf"^MATCH\s*{_NODE}\s*RETURN\s+.+$", re.IGNORECASE)
MATCH_RELS_RE = re.compile(
    r"^MATCH\s*\(\s*(\w+)?\s*(?::\s*(\w+))?\s*\)\s*-\s*\[\s*(\w+)?\s*(?::\s*(\w+))?\s*\]\s*->\s*"
    r"\(\s*(\w+)?\s*(?::\s*(\w+))?\s*\)\s*RETURN\s+.+$",
    re.IGNORECASE,
)
DETACH_DELETE_RE = re.compile(rf"^MATCH\s*{_NODE}\s*DETACH\s+DELETE\s+\w+$", re.IGNORECASE)


def _parse_props(prop_str: Optional[str]) -> dict:
    props = {}
    if not prop_str:
        return props
    body = prop_str.strip().lstrip("{").rstrip("}")
    for part in body.split(","):
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        props[key.strip()] = value.strip().strip('"').strip("'")
    return props


def _clean_ref(ref: str) -> str:
    return ref.strip().strip('"').strip("'")


def _node_matches(node: dict, label: Optional[str], props: dict) -> bool:
    if label and label not in node["labels"]:
        return False
    return all(str(node["properties"].get(k)) == v for k, v in props.items())


def run_command(db: GraphDB, command: str) -> str:
    """Interprets one simplified pattern-style command against the GraphDB."""
    command = command.strip().rstrip(";").strip()

    m = CREATE_REL_RE.match(command)
    if m:
        a_ref, rel_type, prop_str, b_ref = m.groups()
        src, dst = db.find_by_name(_clean_ref(a_ref)), db.find_by_name(_clean_ref(b_ref))
        if src is None or dst is None:
            return "Error: unknown node. Create both nodes first (they are looked up by their 'name' property)."
        db.add_edge(src, dst, rel_type, _parse_props(prop_str))
        return f"Created relationship {db.node_display(src)} -[{rel_type}]-> {db.node_display(dst)}"

    m = CREATE_NODE_RE.match(command)
    if m:
        var, label, prop_str = m.groups()
        props = _parse_props(prop_str)
        name = props.get("name")
        if name and db.find_by_name(name) is not None:
            return f'Error: a node named "{name}" already exists.'
        node_id = db.add_node(label or var or "Node", props)
        return f"Created node {db.node_display(node_id)}"

    m = MATCH_RELS_RE.match(command)
    if m:
        _, a_label, _, r_type, _, b_label = m.groups()
        rows = []
        for e in db.edges:
            if r_type and e["type"] != r_type:
                continue
            if a_label and a_label not in db.nodes[e["src"]]["labels"]:
                continue
            if b_label and b_label not in db.nodes[e["dst"]]["labels"]:
                continue
            rows.append(f"{db.node_display(e['src'])} -[{e['type']}]-> {db.node_display(e['dst'])}")
        if not rows:
            return "(no matching relationships)"
        return "\n".join(rows) + f"\nReturned {len(rows)} relationship(s)"

    m = MATCH_NODES_RE.match(command)
    if m:
        _, label, prop_str = m.groups()
        props = _parse_props(prop_str)
        found = [nid for nid, d in db.nodes.items() if _node_matches(d, label, props)]
        if not found:
            return "(no matching nodes)"
        rows = [f"{db.node_display(nid)}  {db.nodes[nid]['properties']}" for nid in found]
        return "\n".join(rows) + f"\nReturned {len(found)} node(s)"

    m = DETACH_DELETE_RE.match(command)
    if m:
        _, label, prop_str = m.groups()
        props = _parse_props(prop_str)
        targets = [nid for nid, d in db.nodes.items() if _node_matches(d, label, props)]
        for nid in targets:
            db.delete_node(nid)
        return f"Deleted {len(targets)} node(s) and their relationships"

    return "Error: command not recognised. See the supported command examples above."


# ---- Session-level helpers ----
def graph_changed(message: Optional[str] = None) -> None:
    """Call after any change to the graph: shows an optional success message on the next run
    and clears query results that may now be out of date."""
    if message:
        st.session_state["flash"] = message
    st.session_state.pop("nbr_result", None)
    st.session_state.pop("path_result", None)


def node_select(label: str, key: str, db: GraphDB):
    """Selectbox over node ids, so the selection survives a rename. Returns the chosen node id."""
    ids = list(db.nodes.keys())
    if st.session_state.get(key) not in ids:
        st.session_state.pop(key, None)
    return st.selectbox(label, ids, format_func=db.node_display, key=key)


def load_sample_graph() -> None:
    db = GraphDB()
    for label, props in SIMULATION_CONFIG["sample_nodes"]:
        db.add_node(label, props)
    for src_name, dst_name, rel, props in SIMULATION_CONFIG["sample_edges"]:
        db.add_edge(db.find_by_name(src_name), db.find_by_name(dst_name), rel, props)
    st.session_state["db"] = db
    st.session_state["console_output"] = ""
    graph_changed(f"Loaded sample graph ({len(db.nodes)} nodes, {len(db.edges)} relationships)")


def clear_graph() -> None:
    st.session_state["db"] = GraphDB()
    st.session_state["console_output"] = ""
    graph_changed("Removed all nodes and relationships")


# ======================================================================================
# 2b. GRAPH DRAWING: SHARED LAYOUT, INTERACTIVE PLOTLY VIEW, STATIC IMAGE FOR THE PDF
# ======================================================================================

def _ring_positions(nodes: list) -> dict:
    """Places nodes evenly on a circle (top-first, flat-sided for even counts)."""
    n = len(nodes)
    start = math.pi / 2 + (math.pi / n if n % 2 == 0 else 0)
    return {
        node: (math.cos(start + 2 * math.pi * i / n), math.sin(start + 2 * math.pi * i / n))
        for i, node in enumerate(nodes)
    }


def _graph_layout(g: nx.DiGraph) -> dict:
    """Picks the tidiest layout for the graph size/shape.

    - 1 node           : centred
    - star (hub+spokes): hub in the middle, the rest on a ring
    - up to 16 nodes   : ring, ordered by traversal so linked nodes sit next to each other
    - larger graphs    : spring layout with extra spacing
    """
    n = len(g)
    if n == 1:
        return {node: (0.0, 0.0) for node in g}

    und = nx.Graph(g)
    und.remove_edges_from(list(nx.selfloop_edges(und)))

    hub, hub_degree = max(und.degree, key=lambda item: item[1])
    if n >= 4 and hub_degree == n - 1 and und.number_of_edges() == n - 1:
        pos = {hub: (0.0, 0.0)}
        pos.update(_ring_positions([node for node in und.nodes if node != hub]))
        return pos

    if n <= 16:
        order, seen = [], set()
        for start in und.nodes:
            if start not in seen:
                for node in nx.dfs_preorder_nodes(und, start):
                    seen.add(node)
                    order.append(node)
        return _ring_positions(order)

    # Tie separate pieces together with invisible links so they don't drift far apart
    tied = und.copy()
    parts = [next(iter(c)) for c in nx.connected_components(und)]
    tied.add_edges_from(zip(parts, parts[1:]))
    raw = nx.spring_layout(tied, seed=42, k=1.5 / math.sqrt(n), iterations=300)
    return {node: (float(p[0]), float(p[1])) for node, p in raw.items()}


def _props_text(props: dict) -> str:
    return ", ".join(f"{k}={v}" for k, v in props.items())


def _node_hover(db: GraphDB, node_id: int) -> str:
    """HTML shown when hovering over a node."""
    lines = [
        f"<b>{html.escape(db.node_name(node_id))}</b>",
        f"Label: {html.escape(db.label_of(node_id))}",
        f"ID: {node_id}",
    ]
    for key, value in db.nodes[node_id]["properties"].items():
        if key != "name":
            lines.append(f"{html.escape(str(key))}: {html.escape(str(value))}")
    out_count = sum(1 for e in db.edges if e["src"] == node_id)
    in_count = sum(1 for e in db.edges if e["dst"] == node_id)
    lines.append(f"Relationships: {out_count} out, {in_count} in")
    return "<br>".join(lines)


def build_graph_figure(db: GraphDB) -> go.Figure:
    """Interactive Plotly view: hover for details, scroll to zoom, drag to pan."""
    fig = go.Figure()
    fig.update_layout(
        template="plotly_white", paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(l=10, r=10, t=10, b=50), dragmode="pan",
        hoverlabel=dict(bgcolor="white", bordercolor="#d1d5db", font=dict(color="#111827", size=12)),
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)

    if not db.nodes:
        fig.add_annotation(text="Graph is empty.<br>Add nodes to get started.",
                           xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
                           font=dict(size=16, color="#6b7280"))
        fig.update_layout(height=320)
        return fig

    g = db.to_networkx()
    pos = _graph_layout(g)
    n = len(db.nodes)
    marker_px = 34 if n <= 8 else 26 if n <= 16 else 18
    name_font = 12 if n <= 8 else 11 if n <= 16 else 9
    chip_font = 11 if n <= 16 else 9
    arrow_tail_px = marker_px / 2 + 26

    # Group relationships by (from, to) so several between the same pair share one arrow
    groups = {}
    for e in db.edges:
        groups.setdefault((e["src"], e["dst"]), []).append(e)

    line_x, line_y = [], []
    hover_x, hover_y, hover_text = [], [], []
    for (u, v), rels in groups.items():
        (x1, y1), (x2, y2) = pos[u], pos[v]
        tangent = None
        if u == v:  # self-relationship: a small loop above the node
            r = 0.2
            angles = [math.radians(-60 + 300 * i / 40) for i in range(41)]
            pts = [(x1 + r * math.cos(a), y1 + r + r * math.sin(a)) for a in angles]
            label_x, label_y = x1, y1 + 2 * r + 0.1
        elif (v, u) in groups:  # two-way pair: bend each arrow to its own side
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            cx, cy = mx + EDGE_CURVE * (y2 - y1), my - EDGE_CURVE * (x2 - x1)
            steps = [i / 24 for i in range(25)]
            pts = [((1 - t) ** 2 * x1 + 2 * (1 - t) * t * cx + t ** 2 * x2,
                    (1 - t) ** 2 * y1 + 2 * (1 - t) * t * cy + t ** 2 * y2) for t in steps]
            label_x = 0.25 * x1 + 0.5 * cx + 0.25 * x2
            label_y = 0.25 * y1 + 0.5 * cy + 0.25 * y2
            tangent = (x2 - cx, y2 - cy)
        else:
            pts = [(x1, y1), (x2, y2)]
            label_x, label_y = (x1 + x2) / 2, (y1 + y2) / 2
            tangent = (x2 - x1, y2 - y1)

        line_x += [p[0] for p in pts] + [None]
        line_y += [p[1] for p in pts] + [None]

        # Arrowhead just outside the target node (offsets are in pixels, so it survives zooming)
        if tangent and math.hypot(*tangent) > 0:
            tx, ty = tangent[0] / math.hypot(*tangent), tangent[1] / math.hypot(*tangent)
            fig.add_annotation(
                x=x2, y=y2, xref="x", yref="y", ax=-tx * arrow_tail_px, ay=ty * arrow_tail_px,
                axref="pixel", ayref="pixel", showarrow=True, text="", arrowhead=2,
                arrowsize=1.3, arrowwidth=2, arrowcolor=EDGE_COLOR, standoff=marker_px / 2 + 2,
            )

        # Relationship label as a small chip on the edge
        chip_text = ", ".join(dict.fromkeys(r["type"] for r in rels))
        fig.add_annotation(
            x=label_x, y=label_y, xref="x", yref="y", text=html.escape(chip_text), showarrow=False,
            font=dict(size=chip_font, color="#374151"), bgcolor="white", bordercolor="#d1d5db",
            borderwidth=1, borderpad=3,
        )

        detail = "<br>".join(
            f"<b>{html.escape(r['type'])}</b>"
            + (f"  {html.escape(_props_text(r['properties']))}" if r["properties"] else "")
            for r in rels
        )
        hover_x.append(label_x)
        hover_y.append(label_y)
        hover_text.append(f"{html.escape(db.node_name(u))} \u2192 {html.escape(db.node_name(v))}<br>{detail}")

    fig.add_trace(go.Scatter(
        x=line_x, y=line_y, mode="lines", line=dict(width=2, color=EDGE_COLOR),
        hoverinfo="skip", showlegend=False,
    ))
    fig.add_trace(go.Scatter(  # invisible hover targets on each relationship
        x=hover_x, y=hover_y, mode="markers", marker=dict(size=18, color="rgba(0,0,0,0)"),
        hovertext=hover_text, hoverinfo="text", showlegend=False,
    ))

    # One trace per node label, so the legend doubles as a colour key
    labels_in_order = list(dict.fromkeys(db.label_of(nid) for nid in db.nodes))
    for i, label in enumerate(labels_in_order):
        ids = [nid for nid in db.nodes if db.label_of(nid) == label]
        fig.add_trace(go.Scatter(
            x=[pos[nid][0] for nid in ids], y=[pos[nid][1] for nid in ids],
            mode="markers+text", name=label,
            text=[f"<b>{html.escape(textwrap.fill(db.node_name(nid), 14)).replace(chr(10), '<br>')}</b>"
                  for nid in ids],
            textposition="bottom center", textfont=dict(size=name_font, color="#111827"),
            marker=dict(size=marker_px, color=NODE_COLOR_PALETTE[i % len(NODE_COLOR_PALETTE)],
                        line=dict(color="white", width=2)),
            hovertext=[_node_hover(db, nid) for nid in ids], hoverinfo="text",
        ))

    # Equal spacing on both axes so circles stay round; extra room below for names
    xs, ys = [p[0] for p in pos.values()], [p[1] for p in pos.values()]
    fig.update_xaxes(range=[min(xs) - 0.6, max(xs) + 0.6])
    fig.update_yaxes(range=[min(ys) - 0.7, max(ys) + 0.6], scaleanchor="x", scaleratio=1)
    fig.update_layout(
        height=560 if n <= 16 else 700,
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.02, yanchor="top",
                    itemclick=False, itemdoubleclick=False),
    )
    return fig


def draw_graph(db: GraphDB):
    """Static matplotlib version of the graph. Used for the PDF report image."""
    g = db.to_networkx()
    fig, ax = plt.subplots(figsize=(7, 5))
    if len(g.nodes) == 0:
        ax.text(0.5, 0.5, "Graph is empty.\nAdd nodes to get started.",
                ha="center", va="center", fontsize=12)
        ax.axis("off")
        return fig

    n = len(g)
    node_size = 900 if n <= 8 else 600 if n <= 16 else 400
    font_size = 9 if n <= 8 else 7.5 if n <= 16 else 6.5
    radius_pt = math.sqrt(node_size) / 2
    pos = _graph_layout(g)

    # Node colours (one per label)
    label_colors, node_colors = {}, []
    for node in g.nodes:
        lbl = g.nodes[node]["label"]
        if lbl not in label_colors:
            label_colors[lbl] = NODE_COLOR_PALETTE[len(label_colors) % len(NODE_COLOR_PALETTE)]
        node_colors.append(label_colors[lbl])

    # Edges: straight by default, gently curved only when two nodes point at each other
    curved = [(u, v) for u, v in g.edges if u != v and g.has_edge(v, u)]
    loops = [(u, v) for u, v in g.edges if u == v]
    straight = [(u, v) for u, v in g.edges if u != v and not g.has_edge(v, u)]
    edge_style = dict(ax=ax, arrows=True, arrowstyle="-|>", arrowsize=16, width=1.4,
                      edge_color=EDGE_COLOR, node_size=node_size)
    if straight:
        nx.draw_networkx_edges(g, pos, edgelist=straight, **edge_style)
    if curved:
        nx.draw_networkx_edges(g, pos, edgelist=curved,
                               connectionstyle=f"arc3,rad={EDGE_CURVE}", **edge_style)
    if loops:
        nx.draw_networkx_edges(g, pos, edgelist=loops, **edge_style)

    # Nodes on top of the edges
    nodes = nx.draw_networkx_nodes(g, pos, node_size=node_size, node_color=node_colors,
                                   edgecolors="white", linewidths=2, ax=ax)
    nodes.set_zorder(3)

    # Node names sit just below each node, with a white outline so they stay readable
    for node in g.nodes:
        x, y = pos[node]
        ax.annotate(
            textwrap.fill(g.nodes[node]["name"], 14), (x, y),
            xytext=(0, -(radius_pt + 4)), textcoords="offset points",
            ha="center", va="top", fontsize=font_size, fontweight="bold", color="#111827",
            path_effects=[pe.withStroke(linewidth=3, foreground="white")], zorder=5,
        )

    # Relationship labels as small chips on the middle of each edge
    curved_set = set(curved)
    chip = dict(boxstyle="round,pad=0.2", fc="white", ec="#d1d5db", lw=0.6)
    for u, v, data in g.edges(data=True):
        (x1, y1), (x2, y2) = pos[u], pos[v]
        if u == v:
            ax.annotate(data["type"], (x1, y1), xytext=(0, radius_pt + 24), textcoords="offset points",
                        ha="center", va="center", fontsize=7.5, color="#374151", bbox=chip, zorder=4)
            continue
        lx, ly = (x1 + x2) / 2, (y1 + y2) / 2
        if (u, v) in curved_set:  # follow the bend of the arc
            lx += 0.5 * EDGE_CURVE * (y2 - y1)
            ly -= 0.5 * EDGE_CURVE * (x2 - x1)
        ax.text(lx, ly, data["type"], ha="center", va="center", fontsize=7.5,
                color="#374151", bbox=chip, zorder=4)

    # Even spacing on both axes, with room below the nodes for their names
    legend_rows = math.ceil(len(label_colors) / 4)
    bottom = 0.06 + 0.06 * legend_rows
    box_w, box_h = 7 * 0.96, 5 * (0.98 - bottom)
    xs, ys = [p[0] for p in pos.values()], [p[1] for p in pos.values()]
    x0, x1 = min(xs) - 0.5, max(xs) + 0.5
    y0, y1 = min(ys) - 0.7, max(ys) + 0.4
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    half_w, half_h = (x1 - x0) / 2, (y1 - y0) / 2
    if half_w / half_h < box_w / box_h:   # widen or heighten the view to fill the plot area
        half_w = half_h * box_w / box_h
    else:
        half_h = half_w * box_h / box_w
    ax.set_xlim(cx - half_w, cx + half_w)
    ax.set_ylim(cy - half_h, cy + half_h)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")

    # Legend under the graph
    handles = [plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=c, markersize=10, label=lbl)
               for lbl, c in label_colors.items()]
    fig.legend(handles=handles, loc="lower center", ncol=min(len(handles), 4), fontsize=8,
               frameon=False, title="Node labels", title_fontsize=8)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=bottom)
    return fig


def graph_png_bytes(db: GraphDB) -> Optional[bytes]:
    if not db.nodes:
        return None
    fig = draw_graph(db)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    return buf.getvalue()


def bar_chart(title: str, counts: dict, x_title: str) -> go.Figure:
    fig = go.Figure(go.Bar(x=list(counts.keys()), y=list(counts.values())))
    fig.update_layout(
        title=title, xaxis_title=x_title, yaxis_title="Count",
        height=300, margin=dict(l=20, r=20, t=40, b=20),
    )
    fig.update_yaxes(dtick=1, rangemode="tozero")
    return fig


# ======================================================================================
# 3. PDF EXPORTERS: LAB REPORT AND CERTIFICATE
# ======================================================================================

_PDF_REPLACEMENTS = {
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u2013": "-", "\u2014": "-", "\u2192": "->", "\u2190": "<-", "\u2022": "-",
}


def _pdf_safe(text) -> str:
    """The built-in PDF fonts only support Latin-1, so replace anything else."""
    text = str(text)
    for old, new in _PDF_REPLACEMENTS.items():
        text = text.replace(old, new)
    return text.encode("latin-1", "replace").decode("latin-1")


def _trunc(text, width_mm: float) -> str:
    text = _pdf_safe(text)
    max_chars = max(4, int(width_mm / 1.6))
    return text if len(text) <= max_chars else text[: max_chars - 3] + "..."


class LabReportPDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}} | Virtual Laboratory Report", align="C")


def _pdf_field(pdf, x, y, label, value, label_w, value_w, color=(15, 23, 42), bold=False):
    pdf.set_xy(x, y)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(label_w, 6, _pdf_safe(label))
    pdf.set_font("Helvetica", "B" if bold else "", 9)
    pdf.set_text_color(*color)
    pdf.cell(value_w, 6, _trunc(value, value_w))


def _pdf_heading(pdf, text):
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 7, _pdf_safe(text), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(51, 65, 85)


def generate_pdf_report(student_name: str, roll_nos: str, date_str: str,
                        quiz_score: int, quiz_total: int,
                        quiz_submitted: bool, student_notes: str, db: GraphDB) -> bytes:
    """Compiles the experiment record into a formatted PDF report."""
    pdf = LabReportPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # Title
    pdf.set_text_color(15, 23, 42)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, _pdf_safe(FULL_TITLE), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Student & session info box
    y0 = pdf.get_y()
    pdf.set_fill_color(241, 245, 249)
    pdf.set_draw_color(203, 213, 225)
    pdf.rect(10, y0, 190, 27, "FD")
    _pdf_field(pdf, 14, y0 + 2, "Student Name(s):", student_name or "N/A", 34, 150)
    _pdf_field(pdf, 14, y0 + 10, "Roll No(s):", roll_nos or "N/A", 34, 56)
    _pdf_field(pdf, 104, y0 + 10, "Experiment Date:", date_str or datetime.now().strftime("%Y-%m-%d"), 34, 48)
    if quiz_submitted and quiz_total:
        pct = int(quiz_score / quiz_total * 100)
        quiz_text = f"{quiz_score} / {quiz_total} ({pct}%)"
        quiz_color = (16, 150, 105) if quiz_score >= max(1, quiz_total // 2) else (220, 38, 38)
    else:
        quiz_text, quiz_color = "Not attempted", (100, 116, 139)
    _pdf_field(pdf, 14, y0 + 18, "Quiz Evaluation:", quiz_text, 34, 150, color=quiz_color, bold=True)
    pdf.set_y(y0 + 27 + 6)

    # 1. Aim & expected outcome
    _pdf_heading(pdf, "1. Aim & Expected Outcome")
    pdf.multi_cell(0, 5, _pdf_safe(f"Aim: {EXPERIMENT_CONFIG['aim']}"), new_x="LMARGIN", new_y="NEXT")
    pdf.multi_cell(0, 5, _pdf_safe(f"Expected outcome: {EXPERIMENT_CONFIG['expected_outcome']}"),
                   new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # 2. Objectives
    _pdf_heading(pdf, "2. Learning Objectives")
    for obj in EXPERIMENT_CONFIG["objectives"]:
        pdf.multi_cell(0, 5, _pdf_safe(f"- {obj}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # 3. Final graph state
    _pdf_heading(pdf, "3. Final Graph State")
    pdf.cell(0, 5, f"Nodes: {len(db.nodes)}    Relationships: {len(db.edges)}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    png = graph_png_bytes(db)
    if png:
        img_w = 120
        img_h = img_w * 5 / 7  # matches the 7 x 5 in figure
        if pdf.get_y() + img_h > pdf.h - 20:
            pdf.add_page()
        pdf.image(io.BytesIO(png), x=(pdf.w - img_w) / 2, y=pdf.get_y(), w=img_w)
        pdf.set_y(pdf.get_y() + img_h + 4)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(51, 65, 85)
    else:
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(0, 6, "Graph is empty, so no diagram was generated.", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
    for e in db.edges[:30]:
        line = f"- {db.node_name(e['src'])} -[{e['type']}]-> {db.node_name(e['dst'])}"
        pdf.multi_cell(0, 5, _pdf_safe(line), new_x="LMARGIN", new_y="NEXT")
    if len(db.edges) > 30:
        pdf.cell(0, 5, f"... and {len(db.edges) - 30} more relationship(s)", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # 4. Observations
    _pdf_heading(pdf, "4. Observations & Analysis")
    notes_text = student_notes.strip() if student_notes.strip() else (
        "The experiment demonstrated the creation and management of a graph database "
        "of connected entities, matching the expected outcome."
    )
    pdf.multi_cell(0, 5, _pdf_safe(notes_text), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    # Sign-off line
    if pdf.get_y() > pdf.h - 45:
        pdf.add_page()
    y = pdf.get_y() + 15
    pdf.set_draw_color(180, 180, 180)
    pdf.line(130, y, 190, y)
    pdf.set_xy(130, y + 2)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(60, 4, "Instructor / Student Signature", align="C")

    return bytes(pdf.output())


def generate_certificate_pdf(student_name: str, roll_nos: str, date_str: str,
                             quiz_score: int, quiz_total: int, quiz_submitted: bool) -> bytes:
    """Builds a one-page landscape A4 certificate of completion for this experiment."""
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)
    pdf.set_margins(28, 20, 28)
    pdf.add_page()
    w, h = pdf.w, pdf.h

    # Double border
    pdf.set_draw_color(30, 58, 138)
    pdf.set_line_width(1.6)
    pdf.rect(8, 8, w - 16, h - 16)
    pdf.set_draw_color(147, 163, 199)
    pdf.set_line_width(0.4)
    pdf.rect(12, 12, w - 24, h - 24)

    # Heading
    pdf.set_y(26)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(0, 8, _pdf_safe(LAB_NAME.upper()), new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Times", "B", 36)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 20, "Certificate of Completion", new_x="LMARGIN", new_y="NEXT", align="C")
    y = pdf.get_y() + 1
    pdf.set_draw_color(30, 58, 138)
    pdf.set_line_width(0.6)
    pdf.line(w / 2 - 30, y, w / 2 + 30, y)
    pdf.set_y(y + 8)

    # Body
    pdf.set_font("Helvetica", "", 13)
    pdf.set_text_color(51, 65, 85)
    pdf.cell(0, 10, "This is to certify that", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Times", "BI", 28)
    pdf.set_text_color(15, 23, 42)
    pdf.multi_cell(0, 14, _pdf_safe(student_name.strip()), new_x="LMARGIN", new_y="NEXT", align="C")
    if roll_nos.strip():
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(0, 8, _pdf_safe(f"Roll No(s): {roll_nos.strip()}"), new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 13)
    pdf.set_text_color(51, 65, 85)
    pdf.cell(0, 9, "has successfully completed the virtual lab experiment", new_x="LMARGIN", new_y="NEXT",
             align="C")
    pdf.set_font("Helvetica", "B", 17)
    pdf.set_text_color(30, 58, 138)
    pdf.multi_cell(0, 10, _pdf_safe(FULL_TITLE), new_x="LMARGIN", new_y="NEXT", align="C")
    if quiz_submitted and quiz_total:
        pct = int(quiz_score / quiz_total * 100)
        pdf.ln(2)
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(0, 8, f"Quiz score: {quiz_score} / {quiz_total} ({pct}%)", new_x="LMARGIN", new_y="NEXT",
                 align="C")

    # Date (left) and signature (right)
    base_y = h - 38
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 23, 42)
    pdf.set_xy(35, base_y - 8)
    pdf.cell(60, 6, _pdf_safe(date_str), align="C")
    pdf.set_draw_color(120, 130, 150)
    pdf.set_line_width(0.3)
    pdf.line(35, base_y, 95, base_y)
    pdf.line(w - 95, base_y, w - 35, base_y)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 116, 139)
    pdf.set_xy(35, base_y + 2)
    pdf.cell(60, 6, "Date", align="C")
    pdf.set_xy(w - 95, base_y + 2)
    pdf.cell(60, 6, "Instructor Signature", align="C")

    return bytes(pdf.output())


# ======================================================================================
# 4. SECTION RENDERERS: PURPOSE, THEORY, SIMULATION, QUIZ, REPORT, CERTIFICATE, REFERENCES
# ======================================================================================

def render_purpose_section():
    """Renders Section 1: Aim, expected outcome and learning objectives."""
    st.header("Purpose")
    st.markdown(f"**Aim:** {EXPERIMENT_CONFIG['aim']}")
    st.markdown(f"**Expected Outcome:** {EXPERIMENT_CONFIG['expected_outcome']}")

    st.subheader("Learning Objectives")
    for i, obj in enumerate(EXPERIMENT_CONFIG["objectives"]):
        st.write(f"- **Goal {i + 1}**: {obj}")


def render_theory_section():
    """Renders Section 2: background theory, experimental procedure and key terms."""
    st.header("Theoretical Framework & Background")
    st.markdown(THEORY_CONTENT["background"])

    st.divider()
    st.subheader("Experimental Procedure")
    for step in THEORY_CONTENT["procedure"]:
        st.write(f"- {step}")

    st.divider()
    with st.expander("Key Terminology & Variable Reference"):
        var_df = pd.DataFrame(
            list(THEORY_CONTENT["key_terms"].items()),
            columns=["Term / Variable", "Definition & Role"]
        )
        st.table(var_df)


def render_simulation_section():
    """Renders Section 3: interactive graph database sandbox."""
    st.header("Interactive Simulation Sandbox")
    st.info("Create nodes and relationships, and run queries to explore the graph.")

    cfg = SIMULATION_CONFIG
    db: GraphDB = st.session_state["db"]

    flash = st.session_state.pop("flash", None)
    if flash:
        st.success(flash)

    b1, b2, _ = st.columns([1, 1, 4])
    with b1:
        if st.button("Load Sample Graph"):
            load_sample_graph()
            st.rerun()
    with b2:
        if st.button("Clear Graph"):
            clear_graph()
            st.rerun()

    labels_present = {db.label_of(nid) for nid in db.nodes}
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Nodes", len(db.nodes))
    with m2:
        st.metric("Relationships", len(db.edges))
    with m3:
        st.metric("Distinct Labels", len(labels_present))

    view = st.radio(
        "Simulation view",
        ["Graph View", "Create / Update / Delete", "Query", "Command Console"],
        horizontal=True, key="sim_view", label_visibility="collapsed",
    )

    # ---- Graph View ----
    if view == "Graph View":
        st.subheader("Graph Visualization")
        if db.nodes:
            st.caption("Hover over a node or relationship for details. Scroll to zoom, drag to pan.")
        st.plotly_chart(build_graph_figure(db), theme=None, config=PLOTLY_CONFIG)

        if db.nodes:
            t1, t2 = st.columns(2)
            with t1:
                st.caption("Nodes")
                st.dataframe(db.nodes_table(), hide_index=True)
            with t2:
                st.caption("Relationships")
                if db.edges:
                    st.dataframe(db.edges_table(), hide_index=True)
                else:
                    st.info("No relationships yet.")

            node_counts, rel_counts = {}, {}
            for nid in db.nodes:
                node_counts[db.label_of(nid)] = node_counts.get(db.label_of(nid), 0) + 1
            for e in db.edges:
                rel_counts[e["type"]] = rel_counts.get(e["type"], 0) + 1
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(bar_chart("Nodes by Label", node_counts, "Label"))
            with c2:
                if rel_counts:
                    st.plotly_chart(bar_chart("Relationships by Type", rel_counts, "Type"))

    # ---- Create / Update / Delete ----
    if view == "Create / Update / Delete":
        st.markdown("#### Add Node")
        with st.form("add_node_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                new_label = st.text_input("Label (e.g., Person, Company)", value=cfg["default_node_label"])
            with c2:
                new_name = st.text_input("name property (used as node identifier)")
            extra_props = st.text_input(
                "Additional properties (comma-separated key=value pairs, optional)",
                placeholder="role=Engineer, age=25",
            )
            if st.form_submit_button("Create Node"):
                new_name = new_name.strip()
                if new_name and db.find_by_name(new_name) is not None:
                    st.error(f'A node named "{new_name}" already exists. Use a different name.')
                else:
                    props = {"name": new_name} if new_name else {}
                    for pair in extra_props.split(","):
                        if "=" in pair:
                            k, v = pair.split("=", 1)
                            props[k.strip()] = v.strip()
                    node_id = db.add_node(new_label.strip() or "Node", props)
                    graph_changed(f"Created node {db.node_display(node_id)}")
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
                    rel_type = st.text_input("Relationship type", value=cfg["default_rel_type"])
                with c3:
                    dst_label = st.selectbox("To node", list(options.keys()), key="edge_dst")
                rel_props_text = st.text_input(
                    "Relationship properties (comma-separated key=value pairs, optional)",
                    placeholder="since=2020",
                )
                if st.form_submit_button("Create Relationship"):
                    rel = re.sub(r"\W+", "_", rel_type.strip()).upper() or cfg["default_rel_type"]
                    rel_props = {}
                    for pair in rel_props_text.split(","):
                        if "=" in pair:
                            k, v = pair.split("=", 1)
                            rel_props[k.strip()] = v.strip()
                    db.add_edge(options[src_label], options[dst_label], rel, rel_props)
                    graph_changed(f"Created relationship: {src_label} -[{rel}]-> {dst_label}")
                    st.rerun()

        st.markdown("---")
        st.markdown("#### Update Node Property")
        if db.nodes:
            c1, c2, c3 = st.columns(3)
            with c1:
                upd_node = node_select("Node", "upd_node", db)
            with c2:
                upd_key = st.text_input("Property key", key="upd_key")
            with c3:
                upd_value = st.text_input("New value", key="upd_value")
            if st.button("Update Property"):
                key, value = upd_key.strip(), upd_value.strip()
                existing = db.find_by_name(value) if key == "name" else None
                if not key:
                    st.warning("Enter a property key.")
                elif existing is not None and existing != upd_node:
                    st.error(f'A node named "{value}" already exists. Use a different name.')
                else:
                    before = db.node_display(upd_node)
                    db.update_node_property(upd_node, key, value)
                    graph_changed(f"Set {key}={value} on {before}")
                    st.rerun()
        else:
            st.info("Create a node first.")

        st.markdown("---")
        st.markdown("#### Delete Node / Relationship")
        c1, c2 = st.columns(2)
        with c1:
            if db.nodes:
                del_node = node_select("Node to delete", "del_node", db)
                st.caption("Deleting a node also removes its relationships (DETACH DELETE).")
                if st.button("Delete Node"):
                    label = db.node_display(del_node)
                    db.delete_node(del_node)
                    graph_changed(f"Deleted {label} and its relationships")
                    st.rerun()
        with c2:
            if db.edges:
                edge_options = {
                    f"[{i}] {db.node_display(e['src'])} -[{e['type']}]-> {db.node_display(e['dst'])}": i
                    for i, e in enumerate(db.edges)
                }
                del_edge_label = st.selectbox("Relationship to delete", list(edge_options.keys()), key="del_edge")
                if st.button("Delete Relationship"):
                    db.delete_edge(edge_options[del_edge_label])
                    graph_changed(f"Deleted relationship {del_edge_label}")
                    st.rerun()

    # ---- Query ----
    if view == "Query":
        st.markdown("#### Neighbors of a Node")
        if db.nodes:
            q_node = node_select("Select node", "q_neighbor_node", db)
            if st.button("Find Neighbors"):
                nbrs = db.neighbors(q_node)
                me = db.node_display(q_node)
                if nbrs:
                    lines = []
                    for other_id, rel, direction in nbrs:
                        if direction == "out":
                            lines.append(f"{me} -[{rel}]-> {db.node_display(other_id)}")
                        else:
                            lines.append(f"{me} <-[{rel}]- {db.node_display(other_id)}")
                    st.session_state["nbr_result"] = "\n".join(lines)
                else:
                    st.session_state["nbr_result"] = ""
            shown = st.session_state.get("nbr_result")
            if shown is not None:
                if shown:
                    st.code(shown)
                else:
                    st.info("No neighbors found.")
        else:
            st.info("Create some nodes first.")

        st.markdown("---")
        st.markdown("#### Shortest Path Between Two Nodes")
        if len(db.nodes) >= 2:
            c1, c2 = st.columns(2)
            with c1:
                sp_src = node_select("From", "sp_src", db)
            with c2:
                sp_dst = node_select("To", "sp_dst", db)
            if st.button("Find Shortest Path"):
                path = db.shortest_path(sp_src, sp_dst)
                if path:
                    st.session_state["path_result"] = ("ok", " -> ".join(db.node_display(n) for n in path))
                else:
                    st.session_state["path_result"] = ("none", "No path exists between the selected nodes.")
            shown = st.session_state.get("path_result")
            if shown:
                if shown[0] == "ok":
                    st.success(shown[1])
                else:
                    st.warning(shown[1])
        else:
            st.info("Create at least two nodes first.")

    # ---- Command Console ----
    if view == "Command Console":
        st.markdown("Enter simplified graph query commands. Supported examples:")
        st.code("\n".join(cfg["console_examples"]), language="text")
        st.caption("Nodes are referenced by their `name` property.")
        command = st.text_input("Command", placeholder='CREATE (:Person {name:"Dave"})', key="console_cmd")
        if st.button("Run Command"):
            if command.strip():
                output = run_command(db, command)
                st.session_state["console_output"] = f"> {command}\n{output}"
                graph_changed()
                st.rerun()
            else:
                st.warning("Enter a command first.")

        st.markdown("##### Output")
        st.code(st.session_state["console_output"] or "(empty)")


def render_quiz_section():
    """Renders Section 4: assessment quiz with self-grading and feedback."""
    st.header("Concept Assessment Quiz")
    st.write("Answer the conceptual questions below to evaluate your understanding of the experiment.")

    with st.form("lab_quiz_form"):
        user_responses = {}
        for q in quiz_questions():
            st.subheader(f"Question {q['id']}")
            st.write(q["question"])
            selected = st.radio(
                label=f"Options for Question {q['id']}:",
                options=q["options"],
                index=st.session_state["quiz_answers"].get(q["id"]),
                key=f"quiz_radio_{q['id']}",
                label_visibility="collapsed"
            )
            user_responses[q["id"]] = q["options"].index(selected) if selected is not None else None

        submitted = st.form_submit_button("Submit Quiz for Grading", type="primary")

    if submitted:
        score = 0
        st.session_state["quiz_answers"] = user_responses
        st.session_state["quiz_submitted"] = True

        st.divider()
        st.subheader("Evaluation Results and Feedback")
        for q in quiz_questions():
            user_ans = user_responses.get(q["id"])
            correct_ans = q["answer_index"]
            if user_ans == correct_ans:
                score += 1
                st.success(f"**Question {q['id']}: Correct!**\n\n_{q['explanation']}_")
            elif user_ans is None:
                st.warning(f"**Question {q['id']}: Not answered.**\n\n"
                           f"**Correct Answer:** {q['options'][correct_ans]}\n\n"
                           f"**Reasoning:** _{q['explanation']}_")
            else:
                st.error(f"**Question {q['id']}: Incorrect.** (Your answer: {q['options'][user_ans]})\n\n"
                         f"**Correct Answer:** {q['options'][correct_ans]}\n\n"
                         f"**Reasoning:** _{q['explanation']}_")

        st.session_state["quiz_score"] = score
        perc = (score / len(quiz_questions())) * 100
        st.info(f"Final Score: **{score} / {len(quiz_questions())}** ({perc:.0f}%)")

    elif st.session_state.get("quiz_submitted", False):
        st.success(f"Quiz already submitted. Current score: "
                   f"**{st.session_state.get('quiz_score', 0)} / {len(quiz_questions())}**")


def render_report_section():
    """Renders Section 5: lab report generator with PDF export."""
    st.header("Report Generation")
    st.write("Compile your details, final graph, and quiz evaluation into a PDF report.")

    info = st.session_state["student_info"]
    col1, col2, col3 = st.columns(3)
    with col1:
        student_name = st.text_input("Student Name(s)", value=info.get("name", ""),
                                     placeholder="Enter member names")
    with col2:
        roll_nos = st.text_input("Roll No(s).", value=info.get("id", EXPERIMENT_CONFIG["roll_numbers"]))
    with col3:
        lab_date = st.date_input("Experiment Date", value=datetime.now())

    info["name"] = student_name
    info["id"] = roll_nos
    info["date"] = str(lab_date)

    st.subheader("Discussion & Observations")
    student_notes = st.text_area(
        "Enter your interpretation of results, observations, and conclusions:",
        value=st.session_state.get("student_notes", ""),
        placeholder=("Example: We created nodes and relationships, updated and deleted them, and "
                     "verified neighbors and shortest paths on the resulting graph."),
        height=120
    )
    st.session_state["student_notes"] = student_notes

    db: GraphDB = st.session_state["db"]
    quiz_submitted = st.session_state.get("quiz_submitted", False)
    quiz_score = st.session_state.get("quiz_score", 0)

    st.divider()
    st.subheader("Report Summary Preview")
    st.write(f"**Experiment:** {FULL_TITLE}")
    st.write(f"**Student(s):** {student_name or 'N/A'} | **Roll No(s):** {roll_nos} | **Date:** {lab_date}")
    st.write(f"**Quiz Score:** {quiz_score} / {len(quiz_questions())}" if quiz_submitted
             else "**Quiz Score:** not attempted yet")
    st.write(f"**Final Graph:** {len(db.nodes)} node(s), {len(db.edges)} relationship(s)")

    st.plotly_chart(build_graph_figure(db), theme=None, config=PLOTLY_CONFIG)

    pdf_bytes = generate_pdf_report(
        student_name=student_name,
        roll_nos=roll_nos,
        date_str=str(lab_date),
        quiz_score=quiz_score,
        quiz_total=len(quiz_questions()),
        quiz_submitted=quiz_submitted,
        student_notes=student_notes,
        db=db,
    )

    st.divider()
    st.download_button(
        "Download Report (PDF)",
        data=pdf_bytes,
        file_name="lab_report.pdf",
        mime="application/pdf",
        type="primary",
    )


def render_certificate_section():
    """Renders Section 6: certificate of completion with PDF download."""
    st.header("Certificate")
    st.write("Confirm your details to generate your certificate of completion for this experiment.")

    info = st.session_state["student_info"]
    try:
        default_date = datetime.strptime(info.get("date", ""), "%Y-%m-%d")
    except ValueError:
        default_date = datetime.now()

    col1, col2, col3 = st.columns(3)
    with col1:
        student_name = st.text_input("Student Name(s)", value=info.get("name", ""),
                                     placeholder="Enter member names", key="cert_name")
    with col2:
        roll_nos = st.text_input("Roll No(s).", value=info.get("id", EXPERIMENT_CONFIG["roll_numbers"]),
                                 key="cert_roll")
    with col3:
        cert_date = st.date_input("Date", value=default_date, key="cert_date")

    # Keep the details shared with the Report Generation section
    info["name"] = student_name
    info["id"] = roll_nos
    info["date"] = str(cert_date)

    quiz_submitted = st.session_state.get("quiz_submitted", False)
    quiz_score = st.session_state.get("quiz_score", 0)

    if CERTIFICATE_REQUIRES_QUIZ and not quiz_submitted:
        st.info("Submit the Quiz to unlock your certificate.")
        return
    if not student_name.strip():
        st.warning("Enter your name(s) above to generate the certificate.")
        return

    st.success(f"Certificate ready for **{student_name.strip()}**.")
    certificate_bytes = generate_certificate_pdf(
        student_name=student_name,
        roll_nos=roll_nos,
        date_str=str(cert_date),
        quiz_score=quiz_score,
        quiz_total=len(quiz_questions()),
        quiz_submitted=quiz_submitted,
    )
    st.download_button(
        "Download Certificate (PDF)",
        data=certificate_bytes,
        file_name="lab_certificate.pdf",
        mime="application/pdf",
        type="primary",
    )


def render_references_section():
    """Renders Section 7: references."""
    st.header("References")
    st.markdown("\n".join(f"{i}. {ref}" for i, ref in enumerate(REFERENCES, start=1)))


# ======================================================================================
# 5. MAIN ENTRYPOINT & NAVIGATION
# ======================================================================================

def init_session_state():
    """Initializes Streamlit session state variables."""
    defaults = {
        "db": GraphDB,
        "console_output": lambda: "",
        "quiz_questions": pick_quiz_questions,
        "quiz_answers": dict,
        "quiz_submitted": lambda: False,
        "quiz_score": lambda: 0,
        "student_info": lambda: {"name": "", "id": EXPERIMENT_CONFIG["roll_numbers"],
                                 "date": str(datetime.now().date())},
        "student_notes": lambda: "",
    }
    for key, factory in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = factory()


SECTION_RENDERERS = {
    "Purpose": render_purpose_section,
    "Theory": render_theory_section,
    "Simulation": render_simulation_section,
    "Quiz": render_quiz_section,
    "Report Generation": render_report_section,
    "Certificate": render_certificate_section,
    "References": render_references_section,
}


def main():
    st.set_page_config(
        page_title=f"Virtual Lab | {EXPERIMENT_CONFIG['title']}",
        page_icon=None,
        layout="wide"
    )

    init_session_state()

    st.title(FULL_TITLE)
    st.caption(f"{LAB_NAME} | Roll No(s): {EXPERIMENT_CONFIG['roll_numbers']}")

    section = st.sidebar.radio("Lab Navigator", options=SECTIONS)

    st.sidebar.divider()
    st.sidebar.subheader("Progress Tracker")
    db: GraphDB = st.session_state["db"]
    quiz_status = "Done" if st.session_state.get("quiz_submitted", False) else "Pending"
    st.sidebar.write(f"- **Graph Size:** {len(db.nodes)} nodes, {len(db.edges)} relationships")
    st.sidebar.write(f"- **Quiz Status:** {quiz_status}")
    if st.session_state.get("quiz_submitted", False):
        st.sidebar.write(f"- **Quiz Score:** `{st.session_state.get('quiz_score', 0)} / {len(quiz_questions())}`")

    SECTION_RENDERERS[section]()


if __name__ == "__main__":
    main()
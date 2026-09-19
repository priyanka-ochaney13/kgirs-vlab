"""
Virtual Laboratory Experiment (Streamlit)
Experiment 8 : Create and Manage a Graph Database
Roll Nos     : 36, 38, 39, 40
Aim          : Install Neo4j, create nodes and relationships, and perform basic graph operations.
Outcome      : A functioning graph database containing connected entities.

Sections (as per the lab template):
  1. Theory            : Aim, objectives, background, Neo4j installation reference, procedure, key terms.
  2. Simulation        : In-memory graph database (nodes, relationships, CRUD, queries, Cypher-style
                         console), graph visualisation, metrics, and a trial logger.
  3. Quiz              : 10-question self-grading assessment with instant feedback.
  4. Report Generation : Student info, recorded trials, observations, downloadable PDF report.

The graph database is simulated in memory with plain Python data structures, so the app runs
without a Neo4j server. Neo4j installation steps are given in the Theory section for reference.

Run with : streamlit run vlab.py
Requires : pip install streamlit networkx matplotlib pandas plotly fpdf2
"""

import io
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from fpdf import FPDF


# ======================================================================================
# 1. EXPERIMENT CONFIGURATION & EDUCATIONAL CONTENT
# ======================================================================================

EXPERIMENT_CONFIG = {
    "number": 8,
    "title": "Create and Manage a Graph Database",
    "roll_numbers": "36, 38, 39, 40",
    "aim": "Install Neo4j, create nodes and relationships, and perform basic graph operations.",
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

### Neo4j and Cypher
Neo4j is a widely used native graph database. Its query language, **Cypher**, reads like an ASCII
drawing of the graph:

```cypher
CREATE (a:Person {name: "Alice"})
CREATE (b:Person {name: "Bob"})
CREATE (a)-[:FRIENDS_WITH]->(b)
MATCH (p:Person)-[:FRIENDS_WITH]->(q:Person) RETURN p, q
```

### Installing Neo4j (reference)
1. Download Neo4j Desktop or the Community Edition from neo4j.com/download, **or** run it with Docker:

```bash
docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/test12345 neo4j
```

2. Open Neo4j Browser at `http://localhost:7474` and sign in with user `neo4j` and your password.
3. Run the Cypher statements above in the query bar and view the resulting graph.

### Note on this Virtual Lab
The simulator reproduces the same concepts (nodes, labels, relationships, properties, traversal)
with an in-memory Python graph and a Cypher-style console, so it runs without a Neo4j server.

### Workflow & System Overview
1. **Create**: Add nodes (with a label and properties) and connect them with typed relationships.
2. **Manage**: Update properties, delete nodes or relationships, and watch the graph change.
3. **Query**: Find the neighbors of a node and the shortest path between two nodes.
    """,
    "procedure": [
        "Step 1: Review the theoretical background, objectives, and key terminology.",
        "Step 2: (Reference) Install Neo4j and open Neo4j Browser as described above.",
        "Step 3: Navigate to the Simulation section in the sidebar menu.",
        "Step 4: Optionally click 'Load Sample Graph' to start from a small pre-built graph.",
        "Step 5: In 'Create / Update / Delete', add nodes with a label and a name property.",
        "Step 6: Connect nodes by creating typed, directed relationships (e.g. FRIENDS_WITH).",
        "Step 7: Update a node property, then delete a node or relationship and observe the graph.",
        "Step 8: In 'Query', find the neighbors of a node and the shortest path between two nodes.",
        "Step 9: In 'Command Console', try Cypher-style commands such as CREATE and MATCH.",
        "Step 10: Click 'Record Current Trial' after each operation (log at least 4 trials).",
        "Step 11: Complete the assessment Quiz to test your conceptual understanding.",
        "Step 12: Open Report Generation, enter your details, and download your PDF report."
    ],
    "key_terms": {
        "Node": "An entity in the graph (e.g. a Person or a Company).",
        "Label": "A tag that categorizes a node (e.g. Person, Company).",
        "Relationship": "A directed, typed connection between two nodes (e.g. FRIENDS_WITH).",
        "Property": "A key-value pair stored on a node or relationship (e.g. name: \"Alice\").",
        "Traversal": "Navigating from node to node by following relationships.",
        "Shortest Path": "The fewest-hop chain of relationships connecting two nodes.",
        "Cypher": "Neo4j's declarative graph query language."
    }
}

SIMULATION_CONFIG = {
    "default_node_label": "Person",
    "default_rel_type": "RELATED_TO",
    "sample_nodes": [
        ("Person", {"name": "Alice"}),
        ("Person", {"name": "Bob"}),
        ("Person", {"name": "Carol"}),
        ("Company", {"name": "Acme Corp"}),
    ],
    "sample_edges": [
        ("Alice", "Bob", "FRIENDS_WITH", {}),
        ("Bob", "Carol", "FRIENDS_WITH", {}),
        ("Alice", "Acme Corp", "WORKS_AT", {"role": "Engineer"}),
        ("Carol", "Acme Corp", "WORKS_AT", {"role": "Designer"}),
    ],
    "console_examples": [
        'CREATE (:Person {name:"Dave"})',
        'CREATE (Dave)-[:FRIENDS_WITH]->(Alice)',
        'MATCH (n:Person) RETURN n',
        'MATCH (a)-[r:FRIENDS_WITH]->(b) RETURN a, r, b',
        'MATCH (n {name:"Dave"}) DETACH DELETE n',
    ],
}

QUIZ_QUESTIONS = [
    {
        "id": 1,
        "question": "In a property graph, what is a relationship?",
        "options": [
            "A) A row stored in a table",
            "B) A directed, typed connection between two nodes",
            "C) A constraint placed on a column",
            "D) An index built on a property"
        ],
        "answer_index": 1,
        "explanation": "A relationship links two nodes, has a direction and a type (e.g. WORKS_AT), and can hold properties."
    },
    {
        "id": 2,
        "question": "Which of the following is NOT a core component of a property graph?",
        "options": [
            "A) Node",
            "B) Relationship",
            "C) Property",
            "D) Foreign-key join table"
        ],
        "answer_index": 3,
        "explanation": "Property graphs use nodes, relationships and properties. Join tables and foreign keys belong to the relational model."
    },
    {
        "id": 3,
        "question": "What is the name of Neo4j's query language?",
        "options": [
            "A) GraphQL",
            "B) SPARQL",
            "C) Cypher",
            "D) Gremlin"
        ],
        "answer_index": 2,
        "explanation": "Cypher is Neo4j's declarative query language; its syntax resembles an ASCII drawing of the graph."
    },
    {
        "id": 4,
        "question": "Which Cypher clause is used to add a new node to the database?",
        "options": [
            "A) MATCH",
            "B) RETURN",
            "C) WHERE",
            "D) CREATE"
        ],
        "answer_index": 3,
        "explanation": "CREATE adds new nodes and relationships. MATCH finds existing patterns, and RETURN outputs results."
    },
    {
        "id": 5,
        "question": "Why are graph databases efficient for highly connected data?",
        "options": [
            "A) They compress every record into a single column",
            "B) They avoid storing relationships altogether",
            "C) Relationships are stored directly, so queries follow links instead of running costly joins",
            "D) They only support very small datasets"
        ],
        "answer_index": 2,
        "explanation": "Relationships are first-class and stored with the nodes, so traversals follow direct links rather than computing joins."
    },
    {
        "id": 6,
        "question": "What does the pattern (a)-[:WORKS_AT]->(b) express?",
        "options": [
            "A) Node b has an outgoing WORKS_AT relationship to node a",
            "B) Node a has an outgoing WORKS_AT relationship to node b",
            "C) Nodes a and b are the same node",
            "D) a and b are both labels"
        ],
        "answer_index": 1,
        "explanation": "The arrow shows direction: the relationship starts at a and points to b."
    },
    {
        "id": 7,
        "question": "Finding the shortest chain of relationships between two nodes is an example of:",
        "options": [
            "A) Graph traversal / path finding",
            "B) Sharding",
            "C) Normalization",
            "D) Indexing"
        ],
        "answer_index": 0,
        "explanation": "Shortest-path search walks (traverses) relationships between nodes to find the route with the fewest hops."
    },
    {
        "id": 8,
        "question": "Which statement about property graphs is TRUE?",
        "options": [
            "A) Only nodes can hold properties",
            "B) Both nodes and relationships can hold key-value properties",
            "C) Relationships cannot have a direction",
            "D) Every node must have exactly the same properties"
        ],
        "answer_index": 1,
        "explanation": "Properties can be attached to nodes and to relationships, and nodes can differ in their properties (flexible schema)."
    },
    {
        "id": 9,
        "question": "Which of these is a typical use case for a graph database?",
        "options": [
            "A) Storing large binary video files",
            "B) Serving a single flat CSV log",
            "C) Caching simple key-value session data",
            "D) Building a recommendation engine from user-item connections"
        ],
        "answer_index": 3,
        "explanation": "Recommendations, social networks and fraud detection depend on connections between entities, which graphs model naturally."
    },
    {
        "id": 10,
        "question": "In Neo4j, which statement deletes a node together with all of its relationships?",
        "options": [
            "A) DROP n",
            "B) REMOVE n",
            "C) DETACH DELETE n",
            "D) CLEAR n"
        ],
        "answer_index": 2,
        "explanation": "A plain DELETE fails if the node still has relationships; DETACH DELETE removes the node and its relationships."
    }
]

NODE_COLOR_PALETTE = [
    "#4C72B0", "#DD8452", "#55A868", "#C44E52",
    "#8172B2", "#937860", "#DA8BC3", "#8C8C8C",
]


# ======================================================================================
# 2. SIMULATION ENGINE: IN-MEMORY GRAPH DATABASE + CYPHER-STYLE PARSER
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


# ---- Simplified Cypher-style parser (used by the Command Console) ----
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
    """Interprets one simplified Cypher-style command against the GraphDB."""
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
def set_last_op(operation: str, result: str, flash: bool = False) -> None:
    """Remembers the most recent operation so it can be logged as a trial."""
    db: GraphDB = st.session_state["db"]
    st.session_state["last_op"] = {
        "operation": operation,
        "result": result,
        "nodes": len(db.nodes),
        "relationships": len(db.edges),
    }
    if flash:
        st.session_state["flash"] = result


def load_sample_graph() -> None:
    db = GraphDB()
    for label, props in SIMULATION_CONFIG["sample_nodes"]:
        db.add_node(label, props)
    for src_name, dst_name, rel, props in SIMULATION_CONFIG["sample_edges"]:
        db.add_edge(db.find_by_name(src_name), db.find_by_name(dst_name), rel, props)
    st.session_state["db"] = db
    st.session_state["console_log"] = ["-- Sample graph loaded --"]
    set_last_op(
        "LOAD sample graph",
        f"Loaded sample graph ({len(db.nodes)} nodes, {len(db.edges)} relationships)",
        flash=True,
    )


def clear_graph() -> None:
    st.session_state["db"] = GraphDB()
    st.session_state["console_log"] = []
    set_last_op("CLEAR graph", "Removed all nodes and relationships", flash=True)


def draw_graph(db: GraphDB):
    g = db.to_networkx()
    fig, ax = plt.subplots(figsize=(7, 5))
    if len(g.nodes) == 0:
        ax.text(0.5, 0.5, "Graph is empty.\nAdd nodes to get started.",
                ha="center", va="center", fontsize=12)
        ax.axis("off")
        return fig

    pos = nx.spring_layout(g, seed=42, k=0.9)
    label_colors = {}
    node_colors = []
    for n in g.nodes:
        lbl = g.nodes[n]["label"]
        if lbl not in label_colors:
            label_colors[lbl] = NODE_COLOR_PALETTE[len(label_colors) % len(NODE_COLOR_PALETTE)]
        node_colors.append(label_colors[lbl])

    nx.draw_networkx_nodes(g, pos, node_size=1400, node_color=node_colors, ax=ax, alpha=0.9)
    nx.draw_networkx_labels(g, pos, labels={n: g.nodes[n]["name"] for n in g.nodes},
                            font_size=9, font_color="white", ax=ax)
    nx.draw_networkx_edges(g, pos, ax=ax, arrows=True, arrowsize=18,
                           connectionstyle="arc3,rad=0.08", edge_color="#555555")
    edge_labels = {(u, v): d["type"] for u, v, d in g.edges(data=True)}
    nx.draw_networkx_edge_labels(g, pos, edge_labels=edge_labels, font_size=8, ax=ax)

    handles = [plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=c, markersize=10, label=lbl)
               for lbl, c in label_colors.items()]
    ax.legend(handles=handles, loc="upper left", fontsize=8, title="Node labels")
    ax.axis("off")
    fig.tight_layout()
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
# 3. LAB REPORT PDF EXPORTER
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
                        trials_df: pd.DataFrame, quiz_score: int, quiz_total: int,
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

    # 3. Recorded trials
    _pdf_heading(pdf, "3. Recorded Experimental Trials & Data")
    if trials_df.empty:
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 6, "No simulation trials recorded during this session.", new_x="LMARGIN", new_y="NEXT")
    else:
        columns = [("Trial #", "Trial", 14), ("Operation", "Operation", 46), ("Nodes", "Nodes", 14),
                   ("Relationships", "Rels", 16), ("Result", "Result", 80), ("Timestamp", "Time", 20)]
        pdf.set_fill_color(37, 99, 235)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 8)
        for _, short, width in columns:
            pdf.cell(width, 6, short, border=1, align="C", fill=True)
        pdf.ln()

        pdf.set_fill_color(248, 250, 252)
        pdf.set_text_color(30, 41, 59)
        pdf.set_font("Helvetica", "", 8)
        fill = False
        for _, row in trials_df.iterrows():
            for key, _, width in columns:
                pdf.cell(width, 5, _trunc(row.get(key, ""), width), border=1, align="C", fill=fill)
            pdf.ln()
            fill = not fill
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(51, 65, 85)
    pdf.ln(4)

    # 4. Final graph state
    _pdf_heading(pdf, "4. Final Graph State")
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
    for e in db.edges[:30]:
        line = f"- {db.node_name(e['src'])} -[{e['type']}]-> {db.node_name(e['dst'])}"
        pdf.multi_cell(0, 5, _pdf_safe(line), new_x="LMARGIN", new_y="NEXT")
    if len(db.edges) > 30:
        pdf.cell(0, 5, f"... and {len(db.edges) - 30} more relationship(s)", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # 5. Observations
    _pdf_heading(pdf, "5. Observations & Analysis")
    notes_text = student_notes.strip() if student_notes.strip() else (
        "The experimental trials demonstrated the creation and management of a graph database "
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


# ======================================================================================
# 4. SECTION RENDERERS: THEORY, SIMULATION, QUIZ, REPORT
# ======================================================================================

def render_theory_section():
    """Renders Section 1: Aim, Theory, Objectives, Procedure and Key Terms."""
    st.header("Theoretical Framework & Background")
    st.markdown(f"**Aim:** {EXPERIMENT_CONFIG['aim']}")
    st.markdown(f"**Expected Outcome:** {EXPERIMENT_CONFIG['expected_outcome']}")
    st.markdown(THEORY_CONTENT["background"])

    st.subheader("Learning Objectives")
    for i, obj in enumerate(EXPERIMENT_CONFIG["objectives"]):
        st.write(f"- **Goal {i + 1}**: {obj}")

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

    with st.expander("References"):
        st.markdown(
            "- Neo4j Documentation: Graph Database Concepts: https://neo4j.com/docs/getting-started/\n"
            "- Neo4j Cypher Manual: https://neo4j.com/docs/cypher-manual/current/\n"
            "- NetworkX Documentation: https://networkx.org/documentation/stable/\n"
            "- Robinson, I., Webber, J., & Eifrem, E. *Graph Databases* (2nd ed.), O'Reilly Media."
        )


def render_simulation_section():
    """Renders Section 2: interactive graph database sandbox and trial logger."""
    st.header("Interactive Simulation Sandbox")
    st.info("Create nodes and relationships, run queries, then log each operation as a trial.")

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

    last_op_slot = st.empty()

    tab_graph, tab_crud, tab_query, tab_console = st.tabs(
        ["Graph View", "Create / Update / Delete", "Query", "Command Console"]
    )

    # ---- Graph View ----
    with tab_graph:
        st.subheader("Graph Visualization")
        fig = draw_graph(db)
        st.pyplot(fig)
        plt.close(fig)

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
    with tab_crud:
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
                    set_last_op("CREATE node", f"Created node {db.node_display(node_id)}", flash=True)
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
                    set_last_op("CREATE relationship", f"Created relationship: {src_label} -[{rel}]-> {dst_label}",
                                flash=True)
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
                if upd_key.strip():
                    db.update_node_property(options[upd_label], upd_key.strip(), upd_value)
                    set_last_op("UPDATE property", f"Set {upd_key.strip()}={upd_value} on {upd_label}", flash=True)
                    st.rerun()
                else:
                    st.warning("Enter a property key.")
        else:
            st.info("Create a node first.")

        st.markdown("---")
        st.markdown("#### Delete Node / Relationship")
        c1, c2 = st.columns(2)
        with c1:
            if db.nodes:
                options = {db.node_display(nid): nid for nid in db.nodes}
                del_node_label = st.selectbox("Node to delete", list(options.keys()), key="del_node")
                st.caption("Deleting a node also removes its relationships (DETACH DELETE).")
                if st.button("Delete Node"):
                    db.delete_node(options[del_node_label])
                    set_last_op("DELETE node", f"Deleted {del_node_label} and its relationships", flash=True)
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
                    set_last_op("DELETE relationship", f"Deleted relationship {del_edge_label}", flash=True)
                    st.rerun()

    # ---- Query ----
    with tab_query:
        st.markdown("#### Neighbors of a Node")
        if db.nodes:
            options = {db.node_display(nid): nid for nid in db.nodes}
            q_node_label = st.selectbox("Select node", list(options.keys()), key="q_neighbor_node")
            if st.button("Find Neighbors"):
                nbrs = db.neighbors(options[q_node_label])
                if nbrs:
                    lines = []
                    for other_id, rel, direction in nbrs:
                        if direction == "out":
                            lines.append(f"{q_node_label} -[{rel}]-> {db.node_display(other_id)}")
                        else:
                            lines.append(f"{q_node_label} <-[{rel}]- {db.node_display(other_id)}")
                    st.code("\n".join(lines))
                    names = ", ".join(db.node_name(o) for o, _, _ in nbrs)
                    result = f"{len(nbrs)} relationship(s): {names}"
                else:
                    st.info("No neighbors found.")
                    result = "No neighbors found"
                set_last_op(f"QUERY neighbors of {db.node_name(options[q_node_label])}", result)
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
                src, dst = options[sp_src_label], options[sp_dst_label]
                path = db.shortest_path(src, dst)
                if path:
                    st.success(" -> ".join(db.node_display(n) for n in path))
                    result = f"Path ({len(path) - 1} hop(s)): " + " -> ".join(db.node_name(n) for n in path)
                else:
                    st.warning("No path exists between the selected nodes.")
                    result = "No path exists"
                set_last_op(f"QUERY shortest path {db.node_name(src)} to {db.node_name(dst)}", result)
        else:
            st.info("Create at least two nodes first.")

    # ---- Command Console ----
    with tab_console:
        st.markdown("Enter simplified Cypher-style commands. Supported examples:")
        st.code("\n".join(cfg["console_examples"]), language="cypher")
        st.caption("Nodes are referenced by their `name` property.")
        command = st.text_input("Command", placeholder='CREATE (:Person {name:"Dave"})', key="console_cmd")
        if st.button("Run Command"):
            if command.strip():
                output = run_command(db, command)
                st.session_state["console_log"].append(f"> {command}")
                st.session_state["console_log"].append(output)
                set_last_op(f"CONSOLE {command.strip()[:40]}", output.splitlines()[0])
                st.rerun()
            else:
                st.warning("Enter a command first.")

        st.markdown("##### Console Log")
        log = st.session_state["console_log"]
        st.code("\n".join(log) if log else "(empty)")

    # ---- Data Logger ----
    st.divider()
    st.subheader("Experimental Data Log Book")
    col_log1, col_log2 = st.columns([1.5, 3.5])

    with col_log1:
        st.caption("Capture the last operation and the current graph size into your trial table:")
        if st.button("Record Current Trial", type="primary"):
            op = st.session_state["last_op"]
            if op is None:
                st.warning("Perform an operation first, then record it.")
            else:
                trial_record = {
                    "Trial #": len(st.session_state["trials"]) + 1,
                    "Operation": op["operation"],
                    "Nodes": op["nodes"],
                    "Relationships": op["relationships"],
                    "Result": op["result"],
                    "Timestamp": datetime.now().strftime("%H:%M:%S"),
                }
                st.session_state["trials"].append(trial_record)
                st.toast(f"Trial #{trial_record['Trial #']} successfully saved!")

        if st.button("Clear Logged Trials"):
            st.session_state["trials"] = []
            st.toast("Trial log cleared.")

    with col_log2:
        if st.session_state["trials"]:
            df_trials = pd.DataFrame(st.session_state["trials"])
            st.dataframe(df_trials, hide_index=True)
            st.download_button(
                "Download Trials as CSV",
                data=df_trials.to_csv(index=False).encode("utf-8"),
                file_name="experiment_trials.csv",
                mime="text/csv",
            )
        else:
            st.info("No trials recorded yet. Perform an operation, then click 'Record Current Trial'.")

    # Filled last so it always shows the latest operation
    op = st.session_state["last_op"]
    if op:
        last_op_slot.info(f"**Last operation:** {op['operation']}  \n{op['result']}")
    else:
        last_op_slot.caption("No operation performed yet.")


def render_quiz_section():
    """Renders Section 3: assessment quiz with self-grading and feedback."""
    st.header("Concept Assessment Quiz")
    st.write("Answer the conceptual questions below to evaluate your understanding of the experiment.")

    with st.form("lab_quiz_form"):
        user_responses = {}
        for q in QUIZ_QUESTIONS:
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
        for q in QUIZ_QUESTIONS:
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
        perc = (score / len(QUIZ_QUESTIONS)) * 100
        st.info(f"Final Score: **{score} / {len(QUIZ_QUESTIONS)}** ({perc:.0f}%)")

    elif st.session_state.get("quiz_submitted", False):
        st.success(f"Quiz already submitted. Current score: "
                   f"**{st.session_state.get('quiz_score', 0)} / {len(QUIZ_QUESTIONS)}**")


def render_report_section():
    """Renders Section 4: lab report generator with PDF export."""
    st.header("Report Generation")
    st.write("Compile your details, recorded trials, and quiz evaluation into a PDF report.")

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
    trials_df = pd.DataFrame(st.session_state["trials"]) if st.session_state["trials"] else pd.DataFrame()
    quiz_submitted = st.session_state.get("quiz_submitted", False)
    quiz_score = st.session_state.get("quiz_score", 0)

    st.divider()
    st.subheader("Report Summary Preview")
    st.write(f"**Experiment:** {FULL_TITLE}")
    st.write(f"**Student(s):** {student_name or 'N/A'} | **Roll No(s):** {roll_nos} | **Date:** {lab_date}")
    st.write(f"**Quiz Score:** {quiz_score} / {len(QUIZ_QUESTIONS)}" if quiz_submitted
             else "**Quiz Score:** not attempted yet")
    st.write(f"**Final Graph:** {len(db.nodes)} node(s), {len(db.edges)} relationship(s)")

    if not trials_df.empty:
        st.dataframe(trials_df, hide_index=True)
    else:
        st.info("Note: You have not recorded any trials in the Simulation tab yet. "
                "Your report will indicate 0 trials.")

    pdf_bytes = generate_pdf_report(
        student_name=student_name,
        roll_nos=roll_nos,
        date_str=str(lab_date),
        trials_df=trials_df,
        quiz_score=quiz_score,
        quiz_total=len(QUIZ_QUESTIONS),
        quiz_submitted=quiz_submitted,
        student_notes=student_notes,
        db=db,
    )

    st.divider()
    st.subheader("Download Official Lab Report (.pdf)")
    st.download_button(
        label="Download lab_report.pdf",
        data=pdf_bytes,
        file_name="lab_report.pdf",
        mime="application/pdf",
        key="stream_pdf_btn",
        type="primary",
    )

# ======================================================================================
# 5. MAIN ENTRYPOINT & NAVIGATION
# ======================================================================================

def init_session_state():
    """Initializes Streamlit session state variables."""
    defaults = {
        "db": GraphDB,
        "console_log": list,
        "trials": list,
        "last_op": lambda: None,
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


def main():
    st.set_page_config(
        page_title=f"Virtual Lab | {EXPERIMENT_CONFIG['title']}",
        page_icon=None,
        layout="wide"
    )

    init_session_state()

    st.title(FULL_TITLE)
    st.caption(f"Roll No(s): {EXPERIMENT_CONFIG['roll_numbers']}")

    section = st.sidebar.radio(
        "Lab Navigator",
        options=["Theory", "Simulation", "Quiz", "Report Generation"]
    )

    st.sidebar.divider()
    st.sidebar.subheader("Progress Tracker")
    db: GraphDB = st.session_state["db"]
    quiz_status = "Done" if st.session_state.get("quiz_submitted", False) else "Pending"
    st.sidebar.write(f"- **Trials Logged:** {len(st.session_state['trials'])}")
    st.sidebar.write(f"- **Graph Size:** {len(db.nodes)} nodes, {len(db.edges)} relationships")
    st.sidebar.write(f"- **Quiz Status:** {quiz_status}")
    if st.session_state.get("quiz_submitted", False):
        st.sidebar.write(f"- **Quiz Score:** `{st.session_state.get('quiz_score', 0)} / {len(QUIZ_QUESTIONS)}`")

    if section == "Theory":
        render_theory_section()
    elif section == "Simulation":
        render_simulation_section()
    elif section == "Quiz":
        render_quiz_section()
    elif section == "Report Generation":
        render_report_section()


if __name__ == "__main__":
    main()
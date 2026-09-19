# Virtual Lab: Create and Manage a Graph Database

**Experiment 8: Create and Manage a Graph Database**

**Roll Nos:** 36, 38, 39, 40

---

## Experiment Details

| | |
|---|---|
| **Experiment No.** | 8 |
| **Title** | Create and Manage a Graph Database |
| **Aim** | Create nodes and relationships, and perform basic graph operations. |
| **Expected Outcome** | A functioning graph database containing connected entities. |
| **Implementation note** | Graph database simulated with Python + NetworkX; no database server needed. |

---

## Features

### Theory
- Aim, expected outcome, and graph vs relational comparison
- Querying patterns (ASCII-style node/relationship notation)
- Workflow & system overview
- Learning objectives (5 goals)
- 10-step experimental procedure
- Key terminology table
- References

### Simulation
- **Metrics**: live counts of nodes, relationships, and distinct labels
- **Graph View**: interactive Plotly graph (hover for details, scroll to zoom, drag to pan), nodes and relationships tables, and bar charts of nodes by label and relationships by type
- **Create / Update / Delete**:
  - Add nodes with a label and properties (including extra `key=value` pairs)
  - Add typed, directed relationships with optional properties
  - Update any property on an existing node
  - Delete nodes (with their relationships — DETACH DELETE) or individual relationships
- **Query**: neighbors of a node and shortest path between two nodes
- **Command Console**: simplified Cypher-style commands (`CREATE`, `MATCH ... RETURN`, `MATCH ... DETACH DELETE`)
- **Load Sample Graph / Clear Graph**
- Smart graph layout: centered single node, hub-and-spoke for stars, ring layout for small graphs, spring layout for larger graphs

### Quiz
- 10 random questions drawn from a 50-question bank (`quiz_questions.json`)
- Self-graded with instant feedback, correct answers, and explanations for each question
- Session-persistent score

### Report Generation
- Enter student names, roll numbers, and experiment date
- Add discussion/observations
- Live preview of graph, quiz score, and summary
- Download a formatted PDF containing:
  - Aim & expected outcome
  - Learning objectives
  - Final graph diagram (static image) + node/relationship counts
  - Relationship list
  - Quiz evaluation
  - Observations & signature line

### Sidebar Progress Tracker
- Graph size (nodes, relationships)
- Quiz status and score

---

## Requirements

- Python 3.9+
- streamlit (1.36 or newer)
- networkx
- matplotlib
- pandas
- plotly
- fpdf2 (install `fpdf2`, not `fpdf`)

---

## Setup

```bash
pip install streamlit networkx matplotlib pandas plotly fpdf2
```

### Files Required

Keep both files in the same folder:

| File | Purpose |
|---|---|
| `vlab.py` | Main Streamlit application |
| `quiz_questions.json` | 50-question quiz bank (10 randomly selected per session) |

For Streamlit Cloud deployment, add a `requirements.txt` next to `vlab.py`:

```
streamlit>=1.36
networkx
matplotlib
pandas
plotly
fpdf2
```

---

## Running the App

```bash
streamlit run vlab.py
```

This opens the app in your browser (typically `http://localhost:8501`). Use the **Lab Navigator** in the sidebar to move between sections.

---

## How to Use the Simulator

1. Open **Simulation** from the sidebar.
2. Click **Load Sample Graph** for a small demo (or start empty).
3. In **Create / Update / Delete**:
   - Add a node with a label (e.g. `Person`, `Company`) and properties
   - Connect two nodes with a directed, typed relationship
   - Update a property on an existing node
   - Delete a node or a relationship
4. Check **Graph View**, which updates after every operation.
5. Use **Query** for a node's neighbors or the shortest path between two nodes.
6. Try the **Command Console**:
   ```
   CREATE (:Person {name:"Dave"})
   CREATE (Dave)-[:FRIENDS_WITH]->(Alice)
   MATCH (n:Person) RETURN n
   MATCH (a)-[r:FRIENDS_WITH]->(b) RETURN a, r, b
   MATCH (n {name:"Dave"}) DETACH DELETE n
   ```
7. Complete the **Quiz**, then open **Report Generation**, enter your details and download the PDF.

---

## Command Console Reference

| Command | Description |
|---|---|
| `CREATE (:Person {name:"Dave"})` | Create a node with a label and properties |
| `CREATE (Dave)-[:FRIENDS_WITH]->(Alice)` | Create a directed relationship between two nodes (looked up by `name`) |
| `MATCH (n:Person) RETURN n` | Find all nodes with a given label |
| `MATCH (n {name:"Dave"}) RETURN n` | Find nodes by property |
| `MATCH (a)-[r:FRIENDS_WITH]->(b) RETURN a, r, b` | Find relationships by type |
| `MATCH (n {name:"Dave"}) DETACH DELETE n` | Delete a node and all its relationships |

---

## Architecture Overview

| Section | Key Components |
|---|---|
| **Theory** | `render_theory_section()`, `THEORY_CONTENT`, `EXPERIMENT_CONFIG` |
| **Simulation** | `GraphDB` (in-memory engine), `run_command()` (parser), `build_graph_figure()` (Plotly), `draw_graph()` (Matplotlib for PDF) |
| **Quiz** | `load_quiz_bank()`, `pick_quiz_questions()`, `render_quiz_section()` |
| **Report** | `generate_pdf_report()`, `LabReportPDF`, `graph_png_bytes()` |

### GraphDB Data Model

```python
nodes = {node_id: {"labels": ["Person"], "properties": {"name": "Alice"}}}
edges = [{"src": 0, "dst": 1, "type": "FRIENDS_WITH", "properties": {}}]
```

---

## License

This project is developed for academic purposes as part of the Virtual Laboratory curriculum.
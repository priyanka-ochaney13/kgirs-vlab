# Virtual Lab: Create and Manage a Graph Database

**Experiment 8: Create and Manage a Graph Database**

**Roll Nos:** 36, 38, 39, 40

Part of the **KGIRS Virtual Lab**. Sections follow the sequence required for all experiments:
Purpose → Theory → Simulation → Quiz → Report Generation → Certificate → References.

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

### 1. Purpose
- Aim and expected outcome
- Learning objectives (5 goals)

### 2. Theory
- Graph vs relational database comparison
- Querying patterns (ASCII-style node/relationship notation)
- Workflow & system overview
- 11-step experimental procedure
- Key terminology table

### 3. Simulation
- **Metrics**: live counts of nodes, relationships, and distinct labels
- **Graph View**: interactive Plotly graph (hover for details, scroll to zoom, drag to pan), nodes and relationships tables, and bar charts of nodes by label and relationships by type
- **Create / Update / Delete**:
  - Add nodes with a label and properties (including extra `key=value` pairs)
  - Add typed, directed relationships with optional properties
  - Update any property on an existing node
  - Delete nodes (with their relationships, i.e. DETACH DELETE) or individual relationships
- **Query**: neighbors of a node and shortest path between two nodes
- **Command Console**: simplified Cypher-style commands (`CREATE`, `MATCH ... RETURN`, `MATCH ... DETACH DELETE`) with the output of the latest command
- **Load Sample Graph / Clear Graph**
- Smart graph layout: centered single node, hub-and-spoke for stars, ring layout for small graphs, spring layout for larger graphs

### 4. Quiz
- 10 random questions drawn from a 50-question bank (`quiz_questions.json`)
- Self-graded with instant feedback, correct answers, and explanations for each question
- Session-persistent score

### 5. Report Generation
- Enter student names, roll numbers, and experiment date
- Add discussion/observations
- Live preview of the graph, quiz score, and summary
- Download a formatted PDF containing:
  - Aim & expected outcome
  - Learning objectives
  - Final graph diagram (static image) + node/relationship counts
  - Relationship list
  - Quiz evaluation
  - Observations & signature line

### 6. Certificate
- Confirm student names, roll numbers, and date (shared with Report Generation, so they only need to be entered once)
- Unlocks after the quiz is submitted (configurable, see [Configuration](#configuration))
- Download a landscape A4 PDF certificate of completion containing:
  - Student name(s) and roll number(s)
  - Experiment title
  - Quiz score
  - Date and instructor signature line

### 7. References
- Numbered list of the sources used for this experiment

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

## Configuration

Settings at the top of `vlab.py`:

| Setting | Purpose |
|---|---|
| `LAB_NAME` | Lab name shown under the title and on the certificate (`"KGIRS Virtual Lab"`) |
| `SECTIONS` | Order of the sidebar sections (Purpose to References) |
| `CERTIFICATE_REQUIRES_QUIZ` | `True` unlocks the certificate only after the quiz is submitted; `False` lets students download it any time |
| `REFERENCES` | List of sources shown in the References section |
| `EXPERIMENT_CONFIG` | Experiment number, title, roll numbers, aim, expected outcome and objectives |

---

## How to Use the Simulator

1. Read the **Purpose** and **Theory** sections.
2. Open **Simulation** from the sidebar.
3. Click **Load Sample Graph** for a small demo (or start empty).
4. In **Create / Update / Delete**:
   - Add a node with a label (e.g. `Person`, `Company`) and properties
   - Connect two nodes with a directed, typed relationship
   - Update a property on an existing node
   - Delete a node or a relationship
5. Check **Graph View**, which updates after every operation. Hover over nodes and relationships for details.
6. Use **Query** for a node's neighbors or the shortest path between two nodes.
7. Try the **Command Console**:
```
   CREATE (:Person {name:"Dave"})
   CREATE (Dave)-[:FRIENDS_WITH]->(Alice)
   MATCH (n:Person) RETURN n
   MATCH (a)-[r:FRIENDS_WITH]->(b) RETURN a, r, b
   MATCH (n {name:"Dave"}) DETACH DELETE n
```
8. Complete the **Quiz**.
9. Open **Report Generation**, enter your details and download the PDF report.
10. Open **Certificate** and download your certificate of completion.

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
| **Purpose** | `render_purpose_section()`, `EXPERIMENT_CONFIG` |
| **Theory** | `render_theory_section()`, `THEORY_CONTENT` |
| **Simulation** | `GraphDB` (in-memory engine), `run_command()` (parser), `build_graph_figure()` (interactive Plotly view), `draw_graph()` (Matplotlib image for the PDF) |
| **Quiz** | `load_quiz_bank()`, `pick_quiz_questions()`, `render_quiz_section()` |
| **Report** | `generate_pdf_report()`, `LabReportPDF`, `graph_png_bytes()` |
| **Certificate** | `render_certificate_section()`, `generate_certificate_pdf()`, `CERTIFICATE_REQUIRES_QUIZ` |
| **References** | `render_references_section()`, `REFERENCES` |
| **Navigation** | `SECTIONS`, `SECTION_RENDERERS`, `main()` |

The graph layout (`_graph_layout()`) is shared by the Plotly view and the PDF image, so both show the same arrangement.

### GraphDB Data Model

```python
nodes = {node_id: {"labels": ["Person"], "properties": {"name": "Alice"}}}
edges = [{"src": 0, "dst": 1, "type": "FRIENDS_WITH", "properties": {}}]
```

---

## License

This project is developed for academic purposes as part of the Virtual Laboratory curriculum.
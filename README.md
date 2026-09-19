# Virtual Lab: Create and Manage a Graph Database

A Streamlit implementation of **Experiment 8: Create and Manage a Graph Database**, structured as per the lab template: **Theory, Simulation, Quiz, Report Generation**.

**Roll Nos:** 36, 38, 39, 40

Instead of running an actual **Neo4j** server, the app simulates a property graph database in memory with plain Python data structures and visualizes it with NetworkX + Matplotlib. All core concepts (nodes, labels, relationships, properties) are preserved. Neo4j installation steps and Cypher examples are included in the Theory section for reference.


## Experiment Details

| | |
|---|---|
| **Experiment No.** | 8 |
| **Title** | Create and Manage a Graph Database |
| **Aim** | Install Neo4j, create nodes and relationships, and perform basic graph operations. |
| **Expected Outcome** | A functioning graph database containing connected entities. |
| **Implementation note** | Graph database simulated with Python + NetworkX; Neo4j installation steps given in Theory. |

## Features

- **Theory**: aim, expected outcome, graph vs relational comparison, Neo4j/Cypher reference, Neo4j installation steps, learning objectives, 12-step procedure, key terminology table, references
- **Simulation**
  - **Metrics**: live counts of nodes, relationships and distinct labels
  - **Graph View**: auto-updating graph (color-coded by label), nodes and relationships tables, and charts of nodes by label and relationships by type
  - **Create / Update / Delete**: add nodes (label + properties), add typed relationships (with optional properties), edit properties, delete nodes (with their relationships) or relationships
  - **Query**: neighbors of a node, shortest path between two nodes
  - **Command Console**: Cypher-style commands (`CREATE`, `MATCH ... RETURN`, `MATCH ... DETACH DELETE`)
  - **Load Sample Graph / Clear Graph**
  - **Data Log Book**: "Record Current Trial" logs the last operation and graph size; trials can be cleared or downloaded as CSV
- **Quiz**: 10 auto-graded multiple-choice questions with a correct/incorrect result and an explanation for each
- **Report Generation**: enter names, roll numbers, date and observations, then download a PDF containing the aim, objectives, recorded trials, a final graph snapshot, relationship list, quiz score and observations
- **Sidebar progress tracker**: trials logged, graph size, quiz status and score

## Requirements

- Python 3.9+
- streamlit (1.36 or newer)
- networkx
- matplotlib
- pandas
- plotly
- fpdf2 (install `fpdf2`, not `fpdf`)

## Setup

```bash
pip install streamlit networkx matplotlib pandas plotly fpdf2
```

For Streamlit Cloud deployment, add a `requirements.txt` next to `vlab.py`:

```
streamlit>=1.36
networkx
matplotlib
pandas
plotly
fpdf2
```

## Running the App

```bash
streamlit run vlab.py
```

This opens the app in your browser (typically `http://localhost:8501`). Use the **Lab Navigator** in the sidebar to move between sections.

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
7. After each operation, click **Record Current Trial** (log at least 4 trials).
8. Complete the **Quiz**, then open **Report Generation**, enter your details and download the PDF.

## Mapping to Real Neo4j (for reference)

| This app | Equivalent in Neo4j / Cypher |
|---|---|
| `CREATE (:Person {name:"Alice"})` | `CREATE (a:Person {name: "Alice"})` |
| `CREATE (Alice)-[:FRIENDS_WITH]->(Bob)` | `MATCH (a:Person {name:"Alice"}), (b:Person {name:"Bob"}) CREATE (a)-[:FRIENDS_WITH]->(b)` |
| `MATCH (n:Person) RETURN n` | `MATCH (n:Person) RETURN n` |
| `MATCH (n {name:"Dave"}) DETACH DELETE n` | `MATCH (n {name:"Dave"}) DETACH DELETE n` |
| Query → Neighbors | `MATCH (a)-[r]-(b) WHERE a.name = "Alice" RETURN b, r` |
| Query → Shortest Path | `MATCH p = shortestPath((a)-[*]-(b)) RETURN p` |

## Submission Notes

- Structure follows the lab template provided by the teacher (Theory, Simulation, Quiz, Report Generation).
- First Review: **21st-22nd September 2026**.
- Deliverable: single Python file (`vlab.py`), run via Streamlit.
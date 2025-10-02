from graphviz import Digraph

# Create directed graph
dot = Digraph(comment="Impacts & Benefits", engine="neato")

# Set overall style
dot.attr(overlap='false', splines='true')

# Define node style
node_style = {
    "shape": "circle",
    "style": "filled",
    "fillcolor": "yellow",
    "fontname": "Helvetica",
    "fontsize": "14",
    "width": "2.5"  # bigger circle so text fits
}

# Central hub
dot.node("Central", "Impacts & Benefits", **node_style)

# Benefits list
benefits = [
    "Digitized FRA claims → eliminates scattered paper records",
    "Centralized FRA Atlas → real-time view for officials",
    "AI-based asset mapping → evidence-driven planning",
    "Decision Support System → smarter scheme targeting",
    "Transparency → reduces disputes and delays",
    "Administrative efficiency → less paperwork, scalable",
    "Economic efficiency → funds reach right beneficiaries",
    "Social empowerment → strengthens tribal rights",
    "Environmental sustainability → alerts on deforestation",
    "Future readiness → real-time satellite, IoT, feedback"
]

# Add each benefit as a node connected to hub
for i, b in enumerate(benefits, start=1):
    node_id = f"benefit{i}"
    dot.node(node_id, b, **node_style)
    dot.edge("Central", node_id)

# Save to file
dot.render("impacts_benefits_graph", format="png", cleanup=True)
print("Graph saved as impacts_benefits_graph.png")

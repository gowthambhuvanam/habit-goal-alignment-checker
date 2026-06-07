import networkx as nx
import plotly.graph_objects as go


SUPPORT_COLOR = "#16a34a"   # green
CONFLICT_COLOR = "#dc2626"  # red
GOAL_COLOR = "#4f46e5"      # indigo
HABIT_POS = "#0ea5e9"       # sky
HABIT_NEG = "#f97316"       # orange
HABIT_NEU = "#94a3b8"       # slate


def score_color(score: int) -> str:
    if score >= 70:
        return "#16a34a"
    if score >= 40:
        return "#d97706"
    return "#dc2626"


def build_graph_figure(data: dict) -> dict:
    """Build an interactive habit-to-goal network graph as a Plotly figure dict."""
    goals = data.get("goals", [])
    habits = data.get("habits", [])
    links = data.get("links", [])

    G = nx.Graph()

    goal_names = set()
    for g in goals:
        name = g.get("name", "")
        if not name:
            continue
        goal_names.add(name)
        G.add_node(name, kind="goal", score=g.get("alignment_score", 0))

    habit_nature = {}
    for h in habits:
        name = h.get("name", "")
        if not name:
            continue
        habit_nature[name] = h.get("nature", "neutral")
        G.add_node(name, kind="habit")

    for link in links:
        h = link.get("habit", "")
        g = link.get("goal", "")
        if h in G and g in G:
            G.add_edge(h, g,
                       relationship=link.get("relationship", "supports"),
                       strength=link.get("strength", 1),
                       reason=link.get("reason", ""))

    if G.number_of_nodes() == 0:
        return go.Figure().to_dict()

    # Layout: spring layout spreads connected nodes apart nicely
    pos = nx.spring_layout(G, k=0.9, iterations=80, seed=42)

    # ── Edge traces (one per edge so each can have its own colour/width) ──
    edge_traces = []
    for u, v, attrs in G.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        rel = attrs.get("relationship", "supports")
        strength = attrs.get("strength", 1)
        color = SUPPORT_COLOR if rel == "supports" else CONFLICT_COLOR
        edge_traces.append(go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None],
            mode="lines",
            line=dict(width=1 + strength * 1.4, color=color),
            opacity=0.55 if rel == "supports" else 0.7,
            hoverinfo="text",
            text=attrs.get("reason", ""),
            showlegend=False,
        ))

    # ── Goal nodes ──
    gx, gy, gtext, gcolor, gsize, ghover = [], [], [], [], [], []
    for n, attrs in G.nodes(data=True):
        if attrs.get("kind") != "goal":
            continue
        x, y = pos[n]
        score = attrs.get("score", 0)
        gx.append(x); gy.append(y)
        gtext.append(n)
        gcolor.append(score_color(score))
        gsize.append(34 + (score / 100) * 16)
        ghover.append(f"GOAL: {n}<br>Alignment: {score}/100")

    goal_trace = go.Scatter(
        x=gx, y=gy, mode="markers+text",
        marker=dict(size=gsize, color=gcolor, line=dict(width=3, color="#ffffff"), symbol="square"),
        text=gtext, textposition="bottom center",
        textfont=dict(size=12, color="#e5e7eb"),
        hoverinfo="text", hovertext=ghover,
        name="Goals", showlegend=False,
    )

    # ── Habit nodes ──
    hx, hy, htext, hcolor, hhover = [], [], [], [], []
    for n, attrs in G.nodes(data=True):
        if attrs.get("kind") != "habit":
            continue
        x, y = pos[n]
        nature = habit_nature.get(n, "neutral")
        hx.append(x); hy.append(y)
        htext.append(n)
        hcolor.append(HABIT_POS if nature == "positive" else HABIT_NEG if nature == "negative" else HABIT_NEU)
        hhover.append(f"HABIT: {n}<br>{nature}")

    habit_trace = go.Scatter(
        x=hx, y=hy, mode="markers+text",
        marker=dict(size=20, color=hcolor, line=dict(width=2, color="#ffffff")),
        text=htext, textposition="top center",
        textfont=dict(size=11, color="#cbd5e1"),
        hoverinfo="text", hovertext=hhover,
        name="Habits", showlegend=False,
    )

    fig = go.Figure(data=edge_traces + [goal_trace, habit_trace])
    fig.update_layout(
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        hovermode="closest",
        font=dict(family="Inter, sans-serif"),
    )
    return fig.to_dict()

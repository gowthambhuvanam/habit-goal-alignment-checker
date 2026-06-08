# Align

**Do your daily habits actually move you toward your goals?** Align maps every habit you have against every goal you set, scores the alignment, and shows you the real connection as an interactive graph.

No AI, no API keys, no accounts. The intelligence is a rule-based matching engine that runs instantly and offline.

**Live demo: https://habit-align.vercel.app**

---

## What it does

- Enter your goals and your daily habits
- Each habit is matched to each goal through a **domain taxonomy** (fitness, money, career, learning, sleep, and more)
- Positive habits **support** a goal, negative habits **conflict** with it, and time or money drains hurt your goals even across domains
- Every goal gets an **alignment score** from 0 to 100
- An interactive **network graph** shows the whole web of connections (green = supports, red = conflicts)
- **Blind spots** flags goals that have no supporting habit at all
- Specific **fixes** tell you what to add or cut

## How the engine works (no LLM)

1. A domain taxonomy maps life areas to keywords
2. Each goal and habit is classified into one or more domains by keyword match
3. A habit lexicon assigns each habit a polarity (positive or negative)
4. A habit links to a goal when they share a domain, or through a related-domain affinity, or via a cross-domain time/money drain
5. Each goal is scored from its supporting versus conflicting links

The result is deterministic, transparent, and instant. The same input always gives the same output, and you can trace exactly why every connection exists.

## Tech stack

| Layer | Technology |
|-------|------------|
| Backend | Python + Flask (serverless on Vercel) |
| Engine | Rule-based matching (domain taxonomy, lexicon, scoring) |
| Graph | NetworkX for the graph model, Plotly for the interactive visualization |
| Frontend | Vanilla JS, HTML, CSS, Plotly.js |

## Running locally

```bash
git clone https://github.com/gowthambhuvanam/habit-goal-alignment-checker.git
cd habit-goal-alignment-checker
pip install -r requirements.txt
cd api && python analyze.py
```

Then open `public/index.html` in a browser, or serve the folder with any static server. The API runs on `http://localhost:5000`.

## Project structure

```
habit-goal-alignment-checker/
├── api/
│   ├── analyze.py   # Flask app: API endpoint + serves the app shell
│   ├── engine.py    # rule-based alignment engine (the core logic)
│   ├── graph.py     # NetworkX + Plotly graph builder
│   └── assets.py    # embedded index.html (generated from public/index.html)
├── public/
│   ├── index.html
│   ├── app.js
│   └── style.css
├── requirements.txt
└── vercel.json
```

## License

MIT

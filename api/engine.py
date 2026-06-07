"""
Rule-based habit-to-goal alignment engine. No LLM, no API.

How it works:
  1. A domain taxonomy maps life areas (fitness, money, career, ...) to keywords.
  2. Each goal and habit is classified into one or more domains by keyword match.
  3. Each habit gets a polarity (positive / negative) from a habit lexicon.
  4. A habit links to a goal if they share a domain (or via a cross-domain drain).
     Positive habit -> supports the goal. Negative habit -> conflicts with it.
  5. Each goal is scored 0-100 from its supporting vs conflicting links.
"""

import re

# ── Domain taxonomy: domain -> keywords that signal it ──────────────────────
DOMAINS = {
    "fitness": ["gym", "workout", "work out", "exercise", "run", "running", "jog",
                "cardio", "lift", "weight", "weights", "fit", "fitness", "muscle",
                "train", "training", "sport", "yoga", "walk", "steps", "swim",
                "cycle", "cycling", "marathon", "pushup", "abs", "strength", "stretch"],
    "nutrition": ["eat", "eating", "diet", "cook", "cooking", "meal", "meals", "food",
                  "takeout", "take out", "junk", "fast food", "soda", "sugar", "snack",
                  "vegetable", "veggies", "protein", "healthy food", "fruit", "water",
                  "hydrate", "calorie", "fasting"],
    "money": ["save", "saving", "savings", "money", "budget", "invest", "investing",
              "debt", "spend", "spending", "buy", "buying", "expensive", "frugal",
              "income", "salary", "house", "rent", "afford", "wealth", "rich", "cash",
              "subscription", "shopping", "shop"],
    "career": ["work", "job", "promotion", "promoted", "senior", "career", "boss",
               "interview", "resume", "network", "networking", "certification",
               "engineer", "developer", "manager", "leadership", "deadline", "client",
               "business", "startup", "freelance"],
    "learning": ["read", "reading", "study", "studying", "learn", "learning", "course",
                 "book", "books", "practice", "practise", "skill", "skills", "knowledge",
                 "lesson", "tutorial", "language", "side project", "project", "code",
                 "coding", "build", "portfolio"],
    "sleep": ["sleep", "sleeping", "rest", "bed", "bedtime", "nap", "wake", "early",
              "8 hours", "snooze", "insomnia", "rested"],
    "productivity": ["focus", "focused", "procrastinate", "procrastination", "scroll",
                     "scrolling", "phone", "social media", "instagram", "tiktok",
                     "youtube", "netflix", "distract", "distraction", "plan", "planning",
                     "organize", "organise", "to-do", "todo", "deep work", "binge"],
    "wellness": ["meditate", "meditation", "stress", "mental", "mindful", "journal",
                 "therapy", "smoke", "smoking", "vape", "drink", "alcohol", "beer",
                 "wine", "screen time", "anxiety", "calm", "breathe"],
    "relationships": ["family", "friend", "friends", "partner", "spouse", "social",
                      "call", "people", "relationship", "date", "time with", "loved ones",
                      "community"],
    "creativity": ["write", "writing", "draw", "drawing", "music", "create", "creating",
                   "content", "art", "paint", "design", "blog", "video", "creative"],
}

# ── Habits that are inherently negative for their domain ────────────────────
NEGATIVE_MARKERS = [
    "scroll", "scrolling", "social media", "instagram", "tiktok", "netflix",
    "youtube", "binge", "procrastinate", "procrastination", "takeout", "take out",
    "order food", "fast food", "junk", "soda", "sugar", "smoke", "smoking", "vape",
    "alcohol", "beer", "wine", "drink too", "skip", "skipping", "oversleep", "snooze",
    "stay up", "late night", "up late", "gambl", "impulse", "overspend", "waste",
    "too much", "doom", "gossip", "gaming", "video games",
]

# ── Drains: time/energy/money wasters that conflict cross-domain ────────────
TIME_DRAINS = ["scroll", "social media", "tiktok", "instagram", "youtube", "netflix",
               "binge", "procrastinate", "phone", "stay up", "late night", "gaming",
               "video games", "doom"]
MONEY_DRAINS = ["takeout", "take out", "order food", "shopping", "impulse", "overspend",
                "gambl", "subscription", "buy", "shop"]

# Domains that represent "achievement" goals hurt by time drains
ACHIEVEMENT_DOMAINS = {"fitness", "career", "learning", "money", "creativity"}

# Affinities: a positive habit in domain X also helps goals in these domains
# (weaker, indirect support). E.g. learning habits help career goals.
AFFINITIES = {
    "learning": ["career", "creativity"],
    "career": ["learning"],
    "nutrition": ["fitness"],
    "fitness": ["wellness"],
    "sleep": ["wellness", "productivity"],
    "productivity": ["career", "learning"],
    "wellness": ["productivity"],
}

# Suggested habit per domain (for blind-spot recommendations)
DOMAIN_SUGGESTION = {
    "fitness": "a short daily workout or a 20-minute walk",
    "nutrition": "cooking one healthy meal a day",
    "money": "an automatic weekly transfer to savings",
    "career": "30 minutes of focused skill practice each day",
    "learning": "reading or one lesson a day",
    "sleep": "a fixed bedtime every night",
    "productivity": "a daily deep-work block with the phone away",
    "wellness": "5 minutes of journaling or meditation",
    "relationships": "a daily check-in with someone you care about",
    "creativity": "a small daily creative session",
}


def _norm(text):
    return " " + re.sub(r"[^a-z0-9 ]", " ", text.lower()) + " "


def _domains_of(text):
    t = _norm(text)
    found = {}
    for domain, kws in DOMAINS.items():
        hits = sum(1 for kw in kws if (" " + kw + " ") in t or kw in t)
        if hits:
            found[domain] = hits
    return found


def _is_negative(text):
    t = _norm(text)
    return any(m in t for m in NEGATIVE_MARKERS)


def _has_any(text, words):
    t = _norm(text)
    return any(w in t for w in words)


def analyze_alignment(goals, habits):
    # Classify
    goal_info = [{"name": g, "domains": _domains_of(g)} for g in goals]
    habit_info = []
    for h in habits:
        domains = _domains_of(h)
        negative = _is_negative(h)
        habit_info.append({
            "name": h,
            "domains": domains,
            "negative": negative,
            "time_drain": _has_any(h, TIME_DRAINS),
            "money_drain": _has_any(h, MONEY_DRAINS),
        })

    links = []
    # Support / conflict via shared domains
    for h in habit_info:
        for g in goal_info:
            shared = set(h["domains"]) & set(g["domains"])
            if shared:
                strength = min(3, max(1, len(shared) + (1 if max(h["domains"].values()) > 1 else 0)))
                rel = "conflicts" if h["negative"] else "supports"
                domain = sorted(shared)[0]
                reason = (f"{h['name']} works against your {domain} goal"
                          if h["negative"] else
                          f"{h['name']} directly builds toward this {domain} goal")
                links.append({"habit": h["name"], "goal": g["name"],
                              "relationship": rel, "strength": strength, "reason": reason})

    existing = {(l["habit"], l["goal"]) for l in links}

    # Affinity support: a positive habit indirectly supports related-domain goals
    for h in habit_info:
        if h["negative"] or not h["domains"]:
            continue
        affinity_targets = set()
        for d in h["domains"]:
            affinity_targets.update(AFFINITIES.get(d, []))
        for g in goal_info:
            if (h["name"], g["name"]) in existing:
                continue
            shared = affinity_targets & set(g["domains"])
            if shared:
                domain = sorted(shared)[0]
                links.append({"habit": h["name"], "goal": g["name"],
                              "relationship": "supports", "strength": 1,
                              "reason": f"{h['name']} indirectly builds toward this {domain} goal"})
                existing.add((h["name"], g["name"]))

    # Cross-domain drains: time drains hurt achievement goals; money drains hurt money goals
    for h in habit_info:
        for g in goal_info:
            if (h["name"], g["name"]) in existing:
                continue
            gd = set(g["domains"])
            if h["time_drain"] and (gd & ACHIEVEMENT_DOMAINS):
                links.append({"habit": h["name"], "goal": g["name"],
                              "relationship": "conflicts", "strength": 1,
                              "reason": f"{h['name']} drains the time this goal needs"})
                existing.add((h["name"], g["name"]))
            elif h["money_drain"] and "money" in gd:
                links.append({"habit": h["name"], "goal": g["name"],
                              "relationship": "conflicts", "strength": 1,
                              "reason": f"{h['name']} drains the money this goal needs"})
                existing.add((h["name"], g["name"]))

    # Score each goal
    goals_out = []
    blind_spots = []
    for g in goal_info:
        sup = sum(l["strength"] for l in links if l["goal"] == g["name"] and l["relationship"] == "supports")
        con = sum(l["strength"] for l in links if l["goal"] == g["name"] and l["relationship"] == "conflicts")

        if sup == 0 and con == 0:
            score = 25
            verdict = "No daily habit touches this goal. It is being neglected."
            blind_spots.append(g["name"])
        elif sup == 0:
            score = max(8, 30 - con * 6)
            verdict = "Your habits are actively working against this goal."
            blind_spots.append(g["name"])
        else:
            score = max(8, min(98, 45 + sup * 13 - con * 15))
            if score >= 70:
                verdict = "Your habits strongly back this goal."
            elif score >= 45:
                verdict = "Some real support, but conflicts or gaps are slowing you down."
            else:
                verdict = "More is dragging this down than lifting it up."

        goals_out.append({"name": g["name"], "alignment_score": int(score), "verdict": verdict})

    habits_out = []
    for h in habit_info:
        nature = "negative" if h["negative"] else ("positive" if h["domains"] else "neutral")
        habits_out.append({"name": h["name"], "nature": nature})

    # Recommendations
    recs = []
    for name in blind_spots:
        g = next((x for x in goal_info if x["name"] == name), None)
        domain = sorted(g["domains"])[0] if g and g["domains"] else None
        suggestion = DOMAIN_SUGGESTION.get(domain, "a small daily habit that moves it forward")
        recs.append({"action": f"Add {suggestion}.", "helps_goal": name})

    # Suggest cutting the strongest conflicts
    conflict_links = sorted([l for l in links if l["relationship"] == "conflicts"],
                            key=lambda l: l["strength"], reverse=True)
    seen_habits = set()
    for l in conflict_links:
        if l["habit"] in seen_habits:
            continue
        seen_habits.add(l["habit"])
        recs.append({"action": f"Cut back on \"{l['habit']}\".", "helps_goal": l["goal"]})
        if len(recs) >= 6:
            break
    recs = recs[:6]

    # Overall summary
    avg = sum(g["alignment_score"] for g in goals_out) / max(1, len(goals_out))
    if avg >= 70:
        tone = "Your daily life is well aligned with your goals. Keep the momentum going."
    elif avg >= 45:
        tone = "You are partly aligned. A few targeted habit changes would close the gap."
    else:
        tone = "There is a real gap between what you want and what you actually do each day."
    if blind_spots:
        tone += f" {len(blind_spots)} of {len(goals_out)} goals have no supporting habit at all."

    return {
        "goals": goals_out,
        "habits": habits_out,
        "links": links,
        "blind_spots": blind_spots,
        "recommendations": recs,
        "overall_summary": tone,
        "overall_score": int(avg),
    }

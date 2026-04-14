import json
from pathlib import Path
import matplotlib.pyplot as plt
from collections import Counter

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent

INPUT_PATH = PROJECT_ROOT / "data" / "interim" / "absa_prototype" / "04_restaurant_scores.json"

def plot_tiers():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    tiers = [info["tier"] for info in data.values()]
    counter = Counter(tiers)

    order = ["S", "A", "B", "C", "D"]
    counts = [counter.get(t, 0) for t in order]
    
    plt.figure()
    plt.bar(order, counts)

    plt.title("Tier Distribution")
    plt.xlabel("Tier")
    plt.ylabel("Number of Restaurants")

    plt.show()
    

def plot_top_restaurants(top_n=10):
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    sorted_data = sorted(
        data.values(),
        key=lambda x: x["overall_score"],
        reverse=True
    )[:top_n]

    names = [d["name"] for d in sorted_data]
    scores = [d["overall_score"] for d in sorted_data]

    plt.figure()
    plt.barh(names[::-1], scores[::-1])  # reverse for top at top

    plt.title(f"Top {top_n} Restaurants")
    plt.xlabel("Score")

    plt.show()

import numpy as np

def plot_radar(restaurant_id):
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    r = data[restaurant_id]

    aspects = [k for k in r.keys() if k not in ["name", "overall_score", "tier"]]
    values = [r[a] for a in aspects]

    angles = np.linspace(0, 2 * np.pi, len(aspects), endpoint=False)

    values += values[:1]
    angles = np.concatenate([angles, [angles[0]]])

    plt.figure()
    ax = plt.subplot(111, polar=True)

    ax.plot(angles, values)
    ax.fill(angles, values, alpha=0.1)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(aspects)

    plt.title(f"{r['name']} Aspect Profile")

    plt.show()


def plot_top_radar():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    #  find top restaurant (with ID)
    top_rid, top_info = max(
        data.items(),
        key=lambda x: x[1]["overall_score"]
    )
    
    print(f"Top restaurant: {top_info['name']} ({top_rid})")
    
    # call your original function
    plot_radar(top_rid)

def main():
    plot_tiers()
    plot_top_restaurants()
    plot_top_radar()


if __name__ == "__main__":
    main()
    

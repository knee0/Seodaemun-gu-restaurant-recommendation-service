import json
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter
from prototype.utils.paths import DATA_DIR

# Korean character breaks on default font
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False


INPUT = DATA_DIR / "with_names.json"

# Plot scores of top_n restaurant for each aspect
def plot_top_restaurants(top_n, aspect):
    with open(INPUT, "r", encoding="utf-8") as f:
        data = json.load(f)

    sorted_data = sorted(
        data.values(),
        key=lambda x: x[aspect],
        reverse=True
    )[:top_n]

    names = [d["name"] for d in sorted_data]
    scores = [d[aspect] for d in sorted_data]

    plt.figure()
    plt.barh(names[::-1], scores[::-1])  # reverse for top at top

    plt.title(f"Top {top_n} Restaurants ({aspect})")
    plt.xlabel("Score")

    plt.show()

# Show scores of each aspect in radar chart
def plot_radar(restaurant_id):
    with open(INPUT, "r", encoding="utf-8") as f:
        data = json.load(f)

    res = data[restaurant_id]

    # Make chart for 5 aspects
    aspects = [k for k in res.keys() if k not in ["name", "Total"]]
    values = [res[a] for a in aspects]

    angles = np.linspace(0, 2 * np.pi, len(aspects), endpoint=False)
    values += values[:1]
    angles = np.concatenate([angles, [angles[0]]])

    plt.figure()

    ax = plt.subplot(111, polar=True)
    # plt draws polar plots at 0 radian (East)
    # Rotate view to align at North
    ax.set_theta_offset(np.pi / 2)
    ax.plot(angles, values)
    ax.fill(angles, values, alpha=0.1)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(aspects)

    plt.title(f"{res['name']} Aspect Chart")

    plt.show()


# Giving top restaurant to plot_radar
def plot_top_radar():
    with open(INPUT, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Find restaurant with highest total score
    top_rid, top_info = max(
        data.items(),
        key=lambda x: x[1]["Total"]
    )
    
    plot_radar(top_rid)

# Simple prototype: upgrade to subplots & grouped bar charts
def main():
    plot_top_restaurants(10, "Total")
    plot_top_restaurants(10, "Taste")
    plot_top_restaurants(10, "Service")
    plot_top_restaurants(10, "Mood")
    plot_top_restaurants(10, "Amount")
    plot_top_restaurants(10, "Price")
    plot_top_radar()

if __name__ == "__main__":
    main()
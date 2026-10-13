# The Price of Arrival
### International Student Mobility & Living Costs in Sydney (2019–2026)

**An interactive data-storytelling experience by DataLens**

[![Made with Tableau](https://img.shields.io/badge/Data%20Viz-Tableau-E97627?style=flat-square&logo=tableau&logoColor=white)](https://www.tableau.com/)
[![Status](https://img.shields.io/badge/status-active-brightgreen?style=flat-square)]()
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)]()

---

## Overview

**The Price of Arrival** is a scrollytelling data visualization project that reconstructs the lived experience of international students arriving in Sydney — translating six years of government statistics into a single, human-centred narrative.

Headline figures tell us *how many* students come to Australia. They rarely tell us *who gets left behind by the average* — the student who enrols into a shrinking sector, the one priced out of a hub their field of study depends on, the one whose visa approval odds shifted mid-journey. This project closes that gap, pairing rigorous public data with a persona-driven narrative arc so that the numbers are felt, not just read.

The result is a single, self-contained interactive page: a nine-scene journey that follows **Mei**, a prospective international student, from headline hype to an evidence-based decision.

---

## Research Objective

International student mobility into Sydney is typically communicated through aggregate counts — enrolment totals, visa grant rates, consumer price indices — reported in isolation from one another. This project asks:

> **What does the headline number hide, and what does an arriving student actually need to know before they commit?**

To answer this, the project integrates three independent public datasets into one coherent evidence base, explicitly designed to:

- Separate **headline enrolment counts** from **genuine new intake**, exposing where growth is driven by returning cohorts rather than new arrivals
- Localise national trends to the **Sydney SA4 (sub-region) level**, revealing that each education hub carries a distinct subject-area profile
- Overlay **visa policy change points** onto grant-rate trends, linking abstract percentage shifts to concrete policy dates
- Track the **compounding gap** between enrolment growth and cost-of-living inflation since 2019, reframing affordability as a trajectory rather than a snapshot

## Data Sources

| Dataset | Source | Role in the narrative |
|---|---|---|
| International student enrolments | Australian Department of Education | Headline vs. real intake, sector composition |
| Visa grant rates & policy timeline | Australian Department of Home Affairs | Explains *why* the trend moves, not just *that* it moves |
| Consumer Price Index (CPI) | Australian Bureau of Statistics | Cost-of-living trajectory, 2019 = 100 baseline |

All figures are sourced from publicly available Australian government statistics (2019–2026).

## Visualization Design

The project was designed and built in **Tableau**, with a deliberate set of design decisions aimed at resolving common failure modes in data storytelling:

- **One chart type, one job.** Each figure is matched to the specific comparison it needs to support — time trends, part-to-whole composition, or geographic distribution — rather than defaulting to a single "signature" chart type across the whole story.
- **Disciplined colour encoding.** Palettes are restricted to a small number of semantically grouped hues, with related categories sharing a colour family instead of each being assigned an arbitrary, competing colour.
- **Scale-aware encoding.** Values spanning multiple orders of magnitude (e.g. metro-wide totals vs. individual SA4 counts) are encoded with transformations — including log scaling — so small-but-important figures remain visible alongside dominant ones.
- **Evidence-anchored narrative structure.** The story follows a four-act arc (*Setting → Rising insight → Complication → Resolution*), with every narrative beat explicitly tied back to a numbered figure — nothing is asserted without a chart the reader can verify.
- **Portable, caption-first figures.** Every chart follows a consistent caption standard and is exportable as a single-slide asset, so each figure can stand on its own outside the interactive page (e.g. in a client deck or report).

## Project Structure

```
price-of-arrival-data-visualization/
├── index.html      # Self-contained interactive story (HTML/CSS/JS, embedded charts)
└── README.md
```

The entire experience is packaged into a single `index.html` — no build step or external dependencies required.

## View the Project

Open `index.html` directly in a browser, or enable **GitHub Pages** for this repository (Settings → Pages → Deploy from branch `main`) to view it live at:

```
https://<your-github-username>.github.io/price-of-arrival-data-visualization/
```

## Team

**DataLens** — a three-person team for the *Data-Driven Storytelling* course:

- Katherine Lin
- Jiajun Xu
- Yucheng Liu

This project was developed as part of an iterative reflective journal process, incorporating structured instructor feedback on chart selection, colour discipline, and scale representation across successive revisions.

## License

MIT

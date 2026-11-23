# Instructions for Claude

## Source inputs: a markdown file alone is not enough

Before building or rebuilding a dashboard, look at what the user gave as the source.

**If the source is only a markdown file (`.md`), or other plain text that describes a dashboard, with no screenshot: stop.
Do not profile the dataset, write a spec or build anything.** Tell the user:

> A markdown file on its own isn't a usable source for a dashboard. It keeps the titles and notes but loses what the
> build depends on: chart types and orientation, sort order, values, colors, change columns and layout. Please send a
> screenshot of the dashboard (the full page, or one image per section) along with the markdown. The HTML or code that
> produced the page also works.

Then wait for the screenshot. Do not guess the visuals from headings and legend text.

**Why:** the helpers map what is *seen* to a visualization type (each catalog's "how to spot it in an image" table). On
2026-11-23 a dashboard built from a markdown export alone ("IMT Advisor Sales and Opportunity Performance (v2)",
[examples/imt-advisor-sales-v2.json](examples/imt-advisor-sales-v2.json)) got every chart type by guesswork. "Sales by
producer level" came out as vertical bars in alphabetical order; the source was horizontal bars sorted by year to date
sales, with a change column.

**Inputs that are fine:**

| Input | Use |
|---|---|
| Screenshot(s) | Enough on its own. Read the values and layout off the image |
| Screenshot + markdown | Best of both: the markdown supplies exact wording for titles, subtitles and notes |
| HTML or code behind the page | Enough on its own: exact values, colors, sort and layout |
| Markdown only | **Not enough. Stop and ask for a screenshot** |

This applies to any request to build from a text description of an *existing* dashboard. A user who describes a new
dashboard in their own words ("a bar chart of sales by region, sorted descending") has given the visuals; go ahead.

## Everything else

See [README.md](README.md) (the spec, house rules, troubleshooting) and [reference/README.md](reference/README.md) (one
catalog per visualization).

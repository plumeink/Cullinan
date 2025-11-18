Architecture assets placeholder

Put generated diagrams (Mermaid/PlantUML/PDF/PNG/SVG) here. Recommended filenames:
- architecture.mmd (Mermaid source)
- architecture.svg
- architecture.png
- architecture.puml (PlantUML source)

To generate PNG from Mermaid:
- Install mermaid-cli: `npm i -g @mermaid-js/mermaid-cli`
- Generate: `mmdc -i architecture.mmd -o architecture.png`

To generate SVG from PlantUML:
- Install plantuml (and java)
- Generate: `plantuml -tsvg architecture.puml`


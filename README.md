# the_green
Helping to make the world more greenified! Social Impact Hackathon 2024

---
Model receives large set of context and list of available datasets.
Agent Workflow:
1. Ask about hypothesis
	1. List relevant data options that are available (and mention unavailable)
2. Ask to add to map (Selectively or completely)
	1. Model sends JSON req to add to map
	2. Optional: create agg index for map
3. Ask about areas of interest
	1. LLM highlights areas of interest on map, changing zoom and map selection
	2. Provide rational/context for a region

# RBSA Reporting Instructions

## Objective
Craft a comprehensive RBSA narrative that summarises the full analytical workflow and outcomes. The reply **must** be valid JSON and adhere to the schema below.

## Response Contract
- Return a single JSON object in the following shape (no extra prose, no Markdown wrapping):

```json
{
  "response": {
    "data_flags": {
      "results_final_has_data": <boolean>,
      "results_desmoothing_has_data": <boolean>,
      "results_approach_A_has_data": <boolean>,
      "results_approach_B_has_data": <boolean>,
      "results_approach_C_has_data": <boolean>,
      "results_approach_D_has_data": <boolean>,
      "results_substitution_has_data": <boolean>
    },
    "Final": {
      "Executive Summary": "<markdown report>",
      "Detailed Summary": "<markdown report>"
    },
    "Process": {
      "De-Smoothing": {
        "Executive Summary": "<markdown report>",
        "Detailed Summary": "<markdown report>"
      },
      "Approach-{for i in ('A','B','C','D')}": {
        "Executive Summary": "<markdown report>",
        "Detailed Summary": "<markdown report>"
      },
      "Substitution": {
        "Executive Summary": "<markdown report>",
        "Detailed Summary": "<markdown report>"
      }
    }
  }
}
```

### Hard Rules
- Populate the `data_flags` object with booleans indicating whether each corresponding `results_*` payload contained data (`true` if non-empty, `false` otherwise).
- If any of the `data_flags` values is `false`, in the `Final → Detailed Summary` create an initial stand-alone paragraph that indicates no results were provided for which ever `data_flags` were false.  Indicate for each with a sentence such as: `**IMPORTANT**: No results for {method}` indicating such.
- Whenever quantitative data is available, include at least one Markdown table summarising the relevant weights, diagnostics, or metrics for that section. Tables must have descriptive column headers.
- Each executive summary should contain a minimum of three well-developed paragraphs followed by a concise bullet list of key takeaways. When data supports it, append a Markdown table immediately after the bullet list.
- Each detailed summary must be substantially longer than its corresponding executive summary, combining paragraphs, bullet lists, and Markdown tables. Explicitly analyse financial and economic implications, risk considerations, and scenario sensitivity.
- Every `<markdown report>` value must be Markdown text (paragraphs, lists, tables allowed).
- Preserve all keys exactly as shown; always include every section even when data is missing (explain the absence explicitly).
- Do NOT invent numbers—only cite metrics present in the supplied JSON.

## Component Guidance

### Final

This is the most important section !!!

**Executive Summary**
- Create an executive summary markdown report, with an overall title called "Executive Summary" in bold. Each of the following is to be included in order
- 1. Markdown table showing the final exposure weights. Include the Index Names as well as the tickers. The title of the table should be "Index Exposures"
- 2. In 2-3 sentences, succinctly highlight primary financial and economic implications, with comments linked to the observed exposures.
- 3. Briefly in a single sentence indicate how well the results fit the objective, commenting just on adjusted R-squared. Do Not make a table with other statistical diagnostics in this Executive Summary.
- 4. ONLY IF RELEVANT: indicate any surprising or unusual results in the exposure weights that deserve specific attention and provide the reason.

**Detailed Summary**
- Provide a comprehensive discussion that is longer than the executive summary and structured with clear subsections.
- Present detailed metrics and rationale supporting the final result using both narrative and tabular summaries.
- Expand on financial/economic interpretation, portfolio construction impact, risk considerations, and scenario sensitivities.
- Walk through the full workflow:
  1. Desmoothing diagnostics.
  2. Approaches A–D. Include a paragraph of approximately 2-3 sentences on each, describing method and primary results, and a table for each showing the key results of the respective approach, ending with the exposure weights the method would recommend.
  3. Provide details on the Substitution screen.
  4. Final selection decision.
- Conclude with commentary on analysis effectiveness and explicit next steps or monitoring items. Include expanded markdown table of final relevant statistics.

### Process
Provide focused narratives for each phase.

#### De-Smoothing
**Executive Summary**
- 3–4 sentences describing technique purpose and whether it was required, followed by a short bullet list highlighting the most material implications.
- Include a table of key diagnostics (p-values, coefficients) when data is available.

**Detailed Summary**
- Multi-paragraph exposition that covers methodology, diagnostics, supporting statistics, and practical implications.
- Supplement narrative with bullet lists for risks/considerations and at least one Markdown table summarising diagnostic outputs if provided.

#### Approach-{A,B,C,D}
**Executive Summary**
- Two to three paragraphs on fit, economic insights, and caveats, followed by a bullet list of actionable observations.
- Reference key numbers (weights, error metrics, diagnostics) when available and present them in a Markdown table.

**Detailed Summary**
- Deliver a deep dive combining paragraphs, bullet lists, and tables that analyse strengths/weaknesses of the technique.
- Discuss inputs, intermediate calculations/logs, and quantitative outcomes, and relate them to financial/economic implications.
- Provide an effectiveness verdict and recommended follow-up steps or monitoring.

#### Substitution
**Executive Summary**
- 3–4 sentence overview of the substitution workflow and whether it triggered, followed by a brief bullet list of practical impacts.
- Include a Markdown table comparing substituted versus original assets if data exists.

**Detailed Summary**
- Comprehensive narrative (longer than the executive summary) detailing methodology, diagnostics, observed impacts, and financial consequences.
- Use bullet lists to highlight risks/opportunities and provide tables for any comparative metrics or ranking outputs.

## Context Provided to the Model
The assistant receives JSON payloads assembled from project artefacts. Placeholders in double braces are substituted before the request.

### System Role Payload
```json
{
  "system_prompt": "{{<system_prompt.md>}}",
  "additional_context": {
    "overview_desmoothing": "{{<overview_desmoothing.md>}}",
    "overview_approach_A": "{{<overview_approach_A.md>}}",
    "overview_approach_B": "{{<overview_approach_B.md>}}",
    "overview_approach_C": "{{<overview_approach_C.md>}}",
    "overview_approach_D": "{{<overview_approach_D.md>}}",
    "overview_substitution": "{{<overview_substition.md>}}"
  },
  "config.yaml": "{{<config.yaml>}}"
}
```

### User Role Payload
```json
{
  "analysis_results": {
    "results_final": {{<results_final>}},
    "results_process": {
      "results_desmoothing": {{<results_desmoothing>}},
      "results_approach_A": {{<results_approach_A>}},
      "results_approach_B": {{<results_approach_B>}},
      "results_approach_C": {{<results_approach_C>}},
      "results_approach_D": {{<results_approach_D>}},
      "results_substitution": {{<results_substitution>}}
    }
  }
}
```

Each `results_*` placeholder is replaced with JSON produced by the analytics pipeline.

## Style Requirements
- Maintain a professional, investment-analytics tone.
- Keep paragraphs concise and data-driven; use bullet lists where clarity improves.
- Cite data from the payloads; if a metric is missing, acknowledge the gap.
- When data is absent, state what follow-up analysis is required.
- Ensure final JSON is syntactically valid and complies with this contract.

I want to you to create a prompt for me that will achieve the following

Please provide me with the best prompt for this

## JSON response

I want the LLM to produce the following in a json response with structure

```json
{
    "response": {
        "Final" : {
            "Executive Summary": "<markdown report>",
            "Detailed Summary": "<markdown report>"
        },
        "Process" : {
            "De-Smoothing": {
                "Executive Summary": "<markdown report>",
                "Detailed Summary": "<markdown report>"
            },
            "Approach-{for i in ('A','B','C','D'}": { 
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

## JSON Component Instructions
Following provides instructions for the components of the json response

### `Final`

1. **`Executive Summary`** 
This will include:
    
    1. two to three paragraphs about the result indicating whether it is a good fit or not; and primary financial economic implications; any concerns with using the results
    2. key data (i.e. weights, one or two summary statisstics)

2. **`Detailed Summary`**
This will include:
    1. Description of the overall process which included a sequence of steps
        1. Checking for need for desmoothing
        2. Overview of the four approaches (approximately 3-5 sentences on each):
            - Approach A: nnls (iterative)
            - Approach B: elastic net
            - Approach C: bayesian
            - Approach D: clustering
        3. Substitution Process
        4. Final Selection
    2. Summary and detailed data for the final result.
    3. Financial and economic discussion.
    4. Concluding commentary on effectiveness of the analysis.
   

### `Process`

The process section will have summaries for each phase of the process


#### `De-Smoothing`

1. **`Executive Summary`**
This will include:
    1. Description of the technique (3-4 sentences)
    2. Summary about whether it was needed in the current process

2. **`Detailed Summary`**
This will include:
    1. Greater details about the technique (1-2 paragraphs)
    2. Greater detail about the diagnostic results

#### `Approach-{for i in ('A','B','C','D'}`

1. **`Executive Summary`**
This will include:
    1. two to three paragraphs about the result indicating whether it is a good fit or not; and primary financial economic implications; any concerns with using the results
    2. key data (i.e. weights, one or two summary statisstics)
2. **`Detailed Summary`**
    1. Detailed discussion of the technique with strengths and weaknesses.
    2. Summary and detailed data.
    3. Interim calculation results if present (e.g. logs)
    3. Financial and economic discussion.
    4. Commentary on effectiveness of the analysis.

#### `Substitution`

1. **`Executive Summary`**
This will include:
    1. Description of the technique (3-4 sentences)
    2. Summary about whether it was needed in the current process

2. **`Detailed Summary`**
This will include:
    1. Greater details about the technique (1-2 paragraphs)
    2. Greater detail about the diagnostic results

## Context: JSON payloads LLM will Receive

The LLM will receive a system prompt with additional context about each major step in the process. In addition, the configuration file for the process will be included because it has additional useful information. This will be presented to the LLM in a JSON string payload that will be concatenated for context as follows:


### INPUT

#### System Role 

You will receive the following JSON inputs:

```json
{
    "system_prompt": "{{<system_prompt.md>}}",
    "additional_context": {
        "overview_desmoothing": "{{<overview_desmoothing.md>}}",
        "overview_approach_A": "{{<overview_approach_A.md>}}",
        "overview_approach_B": "{{<overview_approach_B.md>}}",
        "overview_approach_C": "{{<overview_approach_C.md>}}",
        "overview_approach_D": "{{<overview_approach_D.md>}}",
        "overview_substitution": "{{<overview_substition.md>}}",
    },
    "config.yaml": "{{<config.yaml>}}",
}
```
#### User Role

```json
{
    "Analysis Results": {
        "results_final" : {{<results_final>}},
        "results_process" : {
            "results_desmoothing": {{<results_desmoothing>}},
            "results_approach_A": {{<results_approach_A>}},
            "results_approach_B": {{<results_approach_B>}},
            "results_approach_C": {{<results_approach_C>}},
            "results_approach_D": {{<results_approach_D>}},
            "results_substitution": {{<results_substitution>}},
        }
    },
}
```

Each of the results will be json.


Use all of this material to prepare your output summaries.


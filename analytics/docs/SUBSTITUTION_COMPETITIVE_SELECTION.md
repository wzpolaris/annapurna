# Competitive Substitution Selection: IWB vs SPY

## Overview

When IWF (Russell 1000 Growth) and IWD (Russell 1000 Value) are selected together, we test **both** IWB (Russell 1000 Total) and SPY (S&P 500) as potential substitutes and **choose the best one** based on Adjusted R².

## Rationale

**Problem:** IWF + IWD overlap significantly with both IWB and SPY:
- **IWB** = Russell 1000 Total (IWF + IWD by definition)
- **SPY** = S&P 500 (large cap subset, ~75% overlap with R1000)

**Solution:** Exclude SPY from initial selection, test both as substitutes, use whichever fits better.

## Configuration Changes

### Universe (config.yaml)

```yaml
universe:
  tickers:
    # SPY excluded from initial - tested as substitute for IWF+IWD
    - IWM   # US Small Cap
    - IWF   # US Large Growth
    - IWD   # US Large Value
    # IWB, SPY excluded - both tested as substitutes for IWF+IWD, best one used
    ...

  substitution_only:
    - IWB   # Russell 1000 Total (consolidation target for IWF+IWD)
    - SPY   # S&P 500 (alternative consolidation target for IWF+IWD)
    ...
```

### Substitution Rules (config.yaml)

```yaml
substitutions:
  # Test IWB as substitute
  - name: "R1000 for Large Growth+Value"
    direction: "bottom-up"
    substitute: "IWB"
    components: ["IWF", "IWD"]
    level: 1

  # Test SPY as substitute
  - name: "SPY for Large Growth+Value"
    direction: "bottom-up"
    substitute: "SPY"
    components: ["IWF", "IWD"]
    level: 1
```

## Algorithm

### 1. Initial Selection
- IWF and IWD available for selection
- SPY and IWB **excluded** from initial universe
- Approaches A, B, C, D may select IWF, IWD, both, or neither

### 2. Substitution Testing
When IWF + IWD are **both** present in a candidate:

**Test IWB:**
```
Original: IWF(0.287) + IWD(0.236) + others
Substitute: IWB(0.523) + others
→ Adj-R² = 0.979121
```

**Test SPY:**
```
Original: IWF(0.287) + IWD(0.236) + others
Substitute: SPY(0.523) + others
→ Adj-R² = 0.978456
```

### 3. Best Substitute Selection
- Compare Adj-R² for all viable substitutes
- **Choose highest Adj-R²** (parsimony-adjusted fit)
- Apply only the best substitution

Example output:
```
✓ Multiple substitutes tested for IWD + IWF:
  - IWB: Adj-R²=0.979121
  - SPY: Adj-R²=0.978456
  → Choosing BEST: IWB (Adj-R²=0.979121)
```

## Implementation

### Modified Function: `apply_recommended_substitutions()`

**Key Changes:**
1. **Group by components:** Track all substitutes for same component set
2. **Rank substitutes:** Sort by Adj-R² within each group
3. **Apply best only:** Use highest-ranked substitute per component group

```python
# Group substitution tests by components
component_groups = {}
for test in candidate_result.get("substitution_tests", []):
    if "recommend_substitution" in result and result["recommend_substitution"]:
        components = tuple(sorted(result["components"]))

        if components not in component_groups:
            component_groups[components] = []

        component_groups[components].append({
            "substitute": result["substitute"],
            "adj_r2": result["adj_r2_substituted"],
            "result": result
        })

# Apply only the BEST substitute for each component group
for components, substitutes in component_groups.items():
    substitutes.sort(key=lambda x: x["adj_r2"], reverse=True)
    best = substitutes[0]
    # Apply best["result"]...
```

## Selection Criteria

**Why Adjusted R²?**
- Penalizes complexity (number of assets)
- IWB, SPY same parsimony (1 asset vs 2)
- Adj-R² reflects true explanatory power
- Consistent with in-sample analysis mode

**Alternative Criteria (if needed):**
- **BIC:** More conservative penalty for complexity
- **Composite score:** Multi-factor evaluation (R², AIC, residuals)
- **Economic preference:** e.g., prefer IWB for style fidelity, SPY for liquidity

## Expected Outcomes

### Scenario 1: IWB Wins
```
Original: IWF(28.7%) + IWD(23.6%)
Best substitute: IWB(52.3%)
Interpretation: Russell 1000 style components meaningful
```

### Scenario 2: SPY Wins
```
Original: IWF(28.7%) + IWD(23.6%)
Best substitute: SPY(52.3%)
Interpretation: S&P 500 sufficient, no marginal value from R1000
```

### Scenario 3: No Substitution
```
Original: IWF(28.7%) + IWD(23.6%)
Both substitutes rejected (Adj-R² declines)
Interpretation: Growth/Value split is meaningful
```

## Benefits

1. **Eliminates redundancy:** SPY not competing with IWF+IWD in initial selection
2. **Objective comparison:** Both substitutes tested on same candidate
3. **Parsimony:** Reduces assets if consolidation doesn't hurt fit
4. **Flexibility:** Best substitute chosen per candidate (may differ across candidates)

## Edge Cases

### Only IWF Selected (no IWD)
- Neither IWB nor SPY tested (need both components)
- IWF remains in final model

### Only IWD Selected (no IWF)
- Neither IWB nor SPY tested (need both components)
- IWD remains in final model

### Neither IWF nor IWD Selected
- No substitution testing occurs
- Model proceeds without large cap style exposure

## Future Extensions

### Level 2: SPY → IWB Consolidation
If SPY is chosen as best substitute, could test further:
```
substitutions:
  - name: "R1000 for SPY"
    direction: "bottom-up"
    substitute: "IWB"
    components: ["SPY"]
    description: "Replace S&P 500 with Russell 1000 for broader coverage"
```

### Multi-Way Comparison
Test 3+ substitutes simultaneously:
```
components: ["IWF", "IWD"]
substitutes: ["IWB", "SPY", "IWV"]  # Include Russell 3000
→ Choose best among all three
```

## Testing

Run notebook with portfolio containing known large cap exposure:
1. Verify SPY excluded from initial selection
2. Verify both IWB and SPY tested when IWF+IWD present
3. Verify only best substitute applied
4. Verify output shows comparison and selection

## Related Files

- **config.yaml:** Universe and substitution rules
- **rbsa/substitution.py:** `apply_recommended_substitutions()` function
- **notebooks/RBSA_Notebook.ipynb:** Substitution analysis cell

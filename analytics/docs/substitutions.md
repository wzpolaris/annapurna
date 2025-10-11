# Asset Substitution Rules

This file defines **hierarchical substitution rules** for testing whether combinations of highly correlated assets can be replaced with simpler composite indices.

## Philosophy: Bottom-Up Analysis with Post-Hoc Simplification

We use a **bottom-up approach**:
1. **Initial Selection**: Use granular components (IWF, IWD, IWM) to capture true style/size tilts
2. **Post-Hoc Substitution**: Test if composite indices (IWB, VTHR) provide similar fit with fewer assets
3. **Hierarchical Testing**: Apply substitutions in order from smallest to largest combinations

### Why Bottom-Up?

- **Preserves information**: A growth-tilted fund shows as 40% IWF + 5% IWD, not 45% IWB
- **Diagnostically valuable**: Weight swaps and substitution tests reveal if distinctions matter
- **Flexible**: Can simplify when appropriate, keep granular when meaningful
- **Avoids multicollinearity**: Composite indices are excluded from initial selection

## Russell Index Hierarchy

```
IWV (Russell 3000 - Total Market)
├── IWB (Russell 1000 - Large Cap)
│   ├── IWF (Russell 1000 Growth)
│   └── IWD (Russell 1000 Value)
└── IWM (Russell 2000 - Small Cap)
    ├── IWO (Russell 2000 Growth)
    └── IWN (Russell 2000 Value)
```

## Substitution Rules (Applied Bottom-Up)

### Level 1: Style Consolidation Within Size Segments

**IWB (R1000) for IWF + IWD**
- Components: Russell 1000 Growth + Russell 1000 Value
- Substitute: Russell 1000 Total
- Rationale: If growth/value distinction doesn't matter, use total index
- Test: Weight swap (IWF ↔ IWD) + substitution with IWB
- Threshold: R² decline < 0.001 OR Adjusted R² improves

**IWM remains as-is** (R2000)
- Note: IWO and IWN are not in selection universe
- Future: Could split IWM into IWO + IWN and test consolidation

### Level 2: Size Consolidation (Future)

**IWM (R2000) for IWO + IWN** (when implemented)
- Components: Russell 2000 Growth + Russell 2000 Value
- Substitute: Russell 2000 Total (current IWM)
- Status: Not yet implemented (requires adding IWO, IWN to substitution_only)

### Level 3: Market-Wide Consolidation (Future)

**IWV (R3000) for IWB + IWM** (or IWF + IWD + IWM)
- Components: Large + Small (or Growth + Value + Small)
- Substitute: Russell 3000 Total Market
- Depends on: Whether Level 1 substitution was applied
- Status: Not yet implemented

## Configuration

### Selection Universe (config.yaml)
Assets available for initial model selection:
```yaml
universe:
  tickers:
    - IWF   # R1000 Growth
    - IWD   # R1000 Value
    - IWM   # R2000 Total
    # IWB excluded - composite
```

### Substitution-Only Assets
Available for substitution testing but excluded from initial selection:
```yaml
universe:
  substitution_only:
    - IWB   # R1000 Total
    - IWO   # R2000 Growth
    - IWN   # R2000 Value
    - IWV   # R3000 Total
```

### Substitution Rules
```yaml
substitutions:
  - name: "R1000 for Large Growth+Value"
    substitute: "IWB"
    components: ["IWF", "IWD"]
    level: 1
    r2_threshold: 0.001
```

## Interpretation

### When Substitution is Recommended

✓ **Use IWB** if:
- Weight swap (IWF ↔ IWD) makes no meaningful difference (ΔR² < 0.001)
- Substitution maintains R² (decline < 0.001) OR improves Adjusted R²
- **Conclusion**: Growth/value distinction is noise, not signal

### When Original Components are Kept

✗ **Keep IWF + IWD** if:
- Weight swap changes fit meaningfully (ΔR² ≥ 0.001)
- Substitution degrades R² beyond threshold AND worsens Adjusted R²
- **Conclusion**: Growth/value distinction captures real fund characteristics

## Adding New Substitution Rules

1. Add the substitute asset to `substitution_only` in config.yaml
2. Add the substitution rule with appropriate level
3. Ensure data is available for the substitute ticker

Example for Level 2:
```yaml
universe:
  substitution_only:
    - IWO  # Add this
    - IWN  # Add this

substitutions:
  - name: "R2000 for Small Growth+Value"
    substitute: "IWM"
    components: ["IWO", "IWN"]
    level: 2
    r2_threshold: 0.001
```

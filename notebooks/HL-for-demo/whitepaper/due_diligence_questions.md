# Due Diligence Questions for Hamilton Lane Private Assets Fund

**Prepared:** November 13, 2025  
**Context:** Structural factor model analysis reveals significant asymmetric downside risk (2.2x), high TAIL factor exposure, and 378% downside capture ratio.

---

## 6 Specific Questions for Hamilton Lane

### 1. **Return Smoothing and Serial Correlation**

**Question:**  
*"Our analysis of the fund's reported monthly returns shows an AR(1) serial correlation coefficient of 0.43, meaning that 43% of this month's return is statistically predictable from last month's return. This is significantly higher than what we observe in liquid public markets (typically 0.0-0.1) and suggests that valuations may not be updated to reflect current market conditions each month. Can you help us understand: (a) What percentage of portfolio holdings are marked-to-market each month using current information vs carried forward from prior marks? (b) Has Hamilton Lane considered publishing 'desmoothed' returns that better reflect the true economic volatility investors are exposed to? (c) The reported volatility is 5.95% annualized, but our structural model suggests the true economic volatility is closer to 29%. How should we think about this 5x difference when assessing risk?"*

**Why This Matters:**  
Return smoothing creates a dangerous illusion of stability. It makes risk metrics like Sharpe ratios appear artificially attractive, understates correlation with other assets during portfolio construction, and can lead to significant over-allocation to private equity. More importantly, investors who believe they're in a 6% volatility asset may panic and redeem at the worst possible time when they discover (during a crisis) that the true volatility is 29%. Understanding the magnitude and source of smoothing is foundational to proper risk assessment.

**Expected Answer Format:**  
- Detailed explanation of monthly valuation update process
- Percentage of NAV re-marked each month vs carried forward
- Acknowledgment of smoothing and guidance on how to adjust for it in risk models
- Comparison to peer fund-of-funds smoothing levels

---

### 2. **Portfolio Company Leverage and Credit Stress Exposure**

**Question:**  
*"What is the weighted-average Net Debt/EBITDA ratio across the underlying portfolio companies as of the most recent quarter? Can you provide a distribution showing what percentage of the portfolio is at leverage levels above 5x, 6x, and 7x EBITDA? During the 2022 rate hiking cycle, what percentage of portfolio companies experienced covenant violations or had to renegotiate credit terms?"*

**Why This Matters:**  
Our analysis shows a TAIL beta of 0.225, indicating significant exposure to credit/liquidity crises. When VIX spikes (averaging -58% in down markets), the fund experiences -13.2% losses primarily through credit channel stress. Understanding the leverage profile directly explains this vulnerability and helps assess refinancing risk in a higher-rate environment.

**Expected Answer Format:**  
- Distribution table: % of NAV by leverage bucket (0-4x, 4-5x, 5-6x, 6-7x, 7x+)
- Historical covenant violation rates during 2022-2023
- Average credit spread paid vs benchmarks by leverage tier

---

### 3. **Valuation Frequency and Marking Methodology in Stress Periods**

**Question:**  
*"During the March 2020 COVID crisis and the Q4 2022 rate shock, what percentage of the portfolio was marked using (a) actual transaction prices, (b) recent comparable transactions, (c) updated DCF models, and (d) carried-forward valuations? What is your policy for triggering interim revaluations outside the standard quarterly cycle when public market comparables drop more than 20%?"*

**Why This Matters:**  
The fund exhibits an AR(1) coefficient of 0.43, indicating significant return smoothing. Reported volatility is 5.95% vs our structural estimate of 29.3%—a 5x difference. This smoothing masks true risk and creates misleading Sharpe ratios. Understanding the marking triggers during volatility spikes is critical to assessing whether the fund accurately reflects economic reality or lags market movements by 1-2 quarters.

**Expected Answer Format:**  
- Breakdown of valuation methodologies used during Q1 2020 and Q4 2022
- Policy document on interim revaluation triggers
- Historical comparison of HLPAF marks vs public PE comp valuations during drawdowns

---

### 4. **All-In Fee Structure and Net Return Decomposition**

**Question:**  
*"Can you provide a complete fee waterfall showing: (a) HLPAF management fee rate, (b) HLPAF performance fee structure and hurdle, (c) weighted-average underlying GP management fees, (d) weighted-average underlying GP carried interest terms, (e) fund-level operating expenses, and (f) any other costs borne by investors? Over the past 3 years, what has been the total drag on returns from all fees and expenses combined—expressed as basis points per year?"*

**Why This Matters:**  
Our model assumes 12% expected return for HLPAF vs 10% for S&P 500. However, fund-of-funds structures can have 2-3 layers of fees. If the all-in fee drag is 300-400bps, the actual risk premium vs public markets may be minimal (or negative on a risk-adjusted basis). Investors need transparency on whether the 2% expected excess return is sufficient compensation for 80% higher volatility, 2x tail risk, and illiquidity.

**Expected Answer Format:**  
- Fee waterfall table showing each layer with actual rates
- Historical 3-year average total fee drag (bps/year)
- Comparison to industry-standard fund-of-funds fee structures

---

### 5. **Actual Redemption Experience and Liquidity Constraints**

**Question:**  
*"For the past 24 months, please provide monthly data on: (a) total redemption requests received ($ and % of NAV), (b) redemptions fulfilled within 90 days ($ and %), (c) redemptions deferred or queued ($ and %), and (d) any periods where redemption gates were implemented or NAV was marked 'indicative only'. What is the maximum quarterly redemption the fund can accommodate without having to conduct forced asset sales at discounts?"*

**Why This Matters:**  
The fund markets quarterly liquidity as a key benefit vs traditional PE funds. However, our analysis shows 91.4% idiosyncratic risk during downturns—meaning HLPAF has PE-specific stress beyond market movements. During March 2020 or Q4 2022, if 10-15% of investors attempted to redeem simultaneously, the fund may have faced forced selling into illiquid markets. Understanding actual redemption experience reveals whether the liquidity feature is real or theoretical.

**Expected Answer Format:**  
- Monthly redemption data table (24 months)
- Disclosure of any redemption queues or gates implemented
- Stress test showing maximum quarterly redemption capacity

---

### 6. **Downside Performance During Historical Crises**

**Question:**  
*"Can you provide monthly returns for HLPAF (or a representative predecessor fund with similar strategy) during: (a) March-April 2020 (COVID crash), (b) Q4 2018 (volatility spike), (c) Q4 2022 (rate shock), and (d) any other periods where S&P 500 declined more than 10% in a quarter? For comparison, please also provide the S&P 500 returns and VIX levels during those same months. Were there any months where interim marks were not updated despite significant public market moves?"*

**Why This Matters:**  
Our structural model shows 378% downside capture—when S&P drops 3.7%, HLPAF drops 13.8%. This is driven by the TAIL factor (VIX) spiking -58% vs market -5%, contributing -13.2% losses. However, this is based on structural betas applied to historical factors. We need actual historical performance during crisis periods to validate whether the model accurately captures real-world behavior or if smoothing/lagging masks the true downside.

**Expected Answer Format:**  
- Monthly return table for crisis periods with S&P 500 and VIX comparisons
- Explanation of any months where marks were carried forward
- Analysis of downside capture ratio vs public PE indices (e.g., LPX, MSCI Private Equity)

---

## 3 Recommended Further Analyses

### Analysis 1: **Liquidity Stress Testing - Redemption Cascade Simulation**

**Objective:**  
Model the fund's behavior under various redemption scenarios to understand how forced liquidations would impact remaining investors.

**Methodology:**
1. **Obtain liquidity tiers:** Classify underlying investments by how quickly they can be sold (0-3 months, 3-6 months, 6-12 months, 12+ months)
2. **Redemption scenarios:** Simulate 5%, 10%, 15%, and 25% quarterly redemption requests
3. **Liquidation waterfall:** Model which assets must be sold first (most liquid), what discounts must be accepted, and how remaining portfolio NAV is impacted
4. **Cascade effects:** Calculate how forced selling affects remaining investors through:
   - NAV dilution from selling liquid assets at discounts
   - Increased concentration in illiquid positions
   - Rising expense ratios as fixed costs spread over smaller AUM

**Expected Insights:**
- At what redemption level does the fund breach "orderly liquidation" capacity?
- What is the first-mover advantage—how much better off are early redeemers vs those who wait?
- Does the quarterly liquidity feature create a run-risk similar to open-end mutual funds during the 2008 crisis?

**Data Needed from Hamilton Lane:**
- Current portfolio liquidity tier breakdown
- Historical asset sale transaction data (prices achieved vs marks)
- Redemption queue policies and pro-rata allocation rules

---

### Analysis 2: **Decomposition of Idiosyncratic Risk - Manager Skill vs Structural Factors**

**Objective:**  
Our model shows 91.4% of downside variance is idiosyncratic (not explained by S&P 500). Decompose this into: (a) additional systematic factors we're missing, (b) manager alpha/skill, and (c) true idiosyncratic company-specific risk.

**Methodology:**
1. **Add macro factors:** Expand the model to include:
   - Corporate earnings growth (forward EPS estimates)
   - Credit spread widening (BBB-Treasury spread, not just HYG)
   - USD strength (particularly relevant for international holdings)
   - M&A volume (proxy for exit environment)
   
2. **Manager selection analysis:**
   - Compare HLPAF's underlying GP selections vs peer PE fund-of-funds
   - Analyze whether HLPAF systematically invests in higher-beta vs lower-beta GPs
   - Regression of GP returns vs GP characteristics (vintage year, sector focus, fund size)

3. **Company-level risk:**
   - If available, obtain portfolio company industry exposures
   - Compare to S&P 500 sector weights to measure concentration risk
   - Stress test: How would portfolio perform if top 3 sectors each declined 50%?

**Expected Insights:**
- Is the 91.4% idiosyncratic risk due to missing factors (fixable by better modeling) or true stock-picking risk?
- Does Hamilton Lane demonstrate skill in GP selection that justifies the risk, or is performance in-line with passive PE exposure?
- Which industries/sectors drive the downside asymmetry?

**Data Needed from Hamilton Lane:**
- Portfolio company industry breakdown (GICS sector level)
- List of underlying GPs with vintage years and fund sizes
- Any available data on GP selection criteria and monitoring

---

### Analysis 3: **Forward-Looking Scenario Analysis - Rate Normalization & Credit Cycle**

**Objective:**  
Our Monte Carlo simulation uses historical factor volatilities from 2010-2025, which includes ZIRP era. Model how HLPAF would perform in scenarios with normalized rates, tighter credit, and recession.

**Methodology:**
1. **Define scenarios:**
   - **Scenario A - Soft Landing:** Rates stable at 4-5%, moderate growth, VIX 15-20
   - **Scenario B - Stagflation:** Rates 5-6%, low growth, persistent inflation, VIX 25-30
   - **Scenario C - Credit Crunch:** Rates 4-5% but credit spreads blow out 300bps+, VIX 40-50
   - **Scenario D - Recession:** Rates cut to 2-3%, earnings decline 20%, VIX 35-45

2. **Calibrate factor assumptions:**
   - For each scenario, specify SC, CS, INNOV, TAIL factor expected values and volatilities
   - Adjust correlations (e.g., in Scenario C, correlation between CS and TAIL spikes)
   - Use regime-switching model rather than assuming i.i.d. normal factors

3. **Portfolio stress testing:**
   - Apply scenario factor paths to calibrated betas
   - Calculate 1-year and 3-year return distributions under each scenario
   - Compare to S&P 500 and 60/40 portfolio performance

4. **Breakeven analysis:**
   - Under each scenario, calculate required expected return premium to justify HLPAF's risk
   - Determine in which scenarios HLPAF provides positive risk-adjusted value vs alternatives

**Expected Insights:**
- HLPAF's TAIL beta of 0.225 suggests it's highly vulnerable to Scenario C (credit crunch)
- In a normalized rate environment, refinancing risk may increase losses beyond historical experience
- Identify scenarios where HLPAF is attractive vs those where public markets dominate

**Data Needed from Hamilton Lane:**
- Portfolio company interest rate hedging (% floating vs fixed debt)
- Maturity schedule of portfolio company debt (refinancing calendar)
- Historical sensitivity of portfolio marks to credit spread changes

---

## Summary Priorities

**Before Investment Decision:**
- **Questions 1, 2, 3, 6** are highest priority—address return smoothing, leverage, valuation practices, and actual crisis performance
- **Analysis 1** should be conducted immediately if considering investment—liquidity risk is underappreciated

**For Ongoing Monitoring:**
- **Questions 4, 5** provide transparency on fees and redemption experience
- **Analyses 2-3** offer deeper understanding of risk sources and forward-looking positioning

**Red Flags to Watch:**
- If Hamilton Lane cannot provide granular leverage data or crisis performance → **high concern**
- If redemption data shows queuing or gates during 2020/2022 → **liquidity is not real**
- If all-in fees exceed 300bps and returns are smoothed → **risk-adjusted value is questionable**


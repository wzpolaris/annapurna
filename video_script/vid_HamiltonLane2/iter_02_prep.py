
# --TURN--

delay = 1.0
pause = True

cardType = "user-assistant"

userText = "go ahead with the desmoothing"

assistantBlocks_type = "markdown"
assistantBlocks_content = """
Analysis indicates an extremely high level of smoothing. \n
\n
So much so, that it can be seen in simple visual inspection in plots:
"""
# Then show the image
assistantBlocks_type = "image"
assistantBlocks_content = "hlpaf_returns_and_growth.png"

assistantBlocks_type = "markdown"
assistantBlocks_content = """
Statistical results confirm:
- Monthly return is nearly constant at ~1.5% return per month -- this is not realistic at all
"""

# Then show the image
assistantBlocks_type = "html"
assistantBlocks_content = """
<table border="1" cellpadding="4" cellspacing="0">
  <caption>Regression Summary</caption>
  <thead>
    <tr>
      <th>Variable</th>
      <th>Coeff</th>
      <th>StdErr</th>
      <th>t-stat</th>
      <th>Statistical Significance</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Constant</td>
      <td>0.0149</td>
      <td>0.003</td>
      <td>5.787</td>
      <td>highly significant / not zero</td>
    </tr>
    <tr>
      <td>FundRet AR(1)</td>
      <td>-0.2237</td>
      <td>0.130</td>
      <td>-1.716</td>
      <td>indistinguishable from zero</td>
    </tr>
  </tbody>
  <tfoot>
    <tr>
      <td colspan="5">R-squared: 0.0492 (very low explanatory power)</td>
    </tr>
  </tfoot>
</table>
"""

assistantBlocks_type = "markdown"
assistantBlocks_content = """
- As a result, desmoothing does not yield a series that has any meaningful information.
"""

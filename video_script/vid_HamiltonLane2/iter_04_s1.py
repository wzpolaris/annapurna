
# --TURN--


# --TURN--

delay = 1.0
pause = True

cardType = "user-assistant"

userText = "ready"

assistantBlocks_type = "markdown"
assistantBlocks_content = """
We will use the Fund's allocations to PE Buyout and Venture Capital strategies to combine the structural models"""


# Then show the image
assistantBlocks_type = "image"
assistantBlocks_content = "donuts.png"



assistantBlocks_type = "html"
assistantBlocks_content = """
<table border="1" cellpadding="6" cellspacing="0">
  <thead>
    <tr>
      <th>Fund - Buyout %</th>
      <th>Fund - VC %</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Fund - Buyout %</th>
      <td style="text-align:center;">79%</td>
    <tr>
      <th>Fund - VC %</th>
      <td style="text-align:center;">21%</td>
    </tr>
  </tbody>
</table>
"""

assistantBlocks_type = "html"
assistantBlocks_content = """
<table border="1" cellpadding="6" cellspacing="0">
  <thead>
    <tr>
      <th>Model</th>
      <th>Equity Market<br>(SC)</th>
      <th>Credit Market<br>(SPRD)</th>
      <th>Innovation<br>(INNOV)</th>
      <th>Tail Risk/Crisis<br>(TAIL)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="text-align:center;">Fund</td>
      <td style="text-align:center;">1.47</td>
      <td style="text-align:center;">0.75</td>
      <td style="text-align:center;">0.21</td>
      <td style="text-align:center;">1.29</td>
    </tr>
  </tbody>
</table>

"""

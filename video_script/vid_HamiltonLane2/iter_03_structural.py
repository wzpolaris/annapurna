


# --TURN--

delay = 3.0
pause = True

cardType = "user-assistant"


userText = "Tell me how the model works"


# Then show the image
assistantBlocks_type = "image"
assistantBlocks_content = "structural-model.png"


assistantBlocks_type = "html"
assistantBlocks_content = '''
<p>
$$
r_{PE_t} = \beta_{SC_t} {\small SC_t} + \beta_{SPRD_t}{\small SPRD_t} + \beta_{INNOV_t}{\small INNOV_t} + \beta_{TAIL_t} {\small TAIL_t} +  \epsilon_{t} 
$$
</p>
'''


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
      <td style="text-align:center;">Buyout</td>
      <td style="text-align:center;">1.5</td>
      <td style="text-align:center;">0.8</td>
      <td style="text-align:center;">0.1</td>
      <td style="text-align:center;">1.2</td>
    </tr>
    <tr>
      <td style="text-align:center;">VC</td>
      <td style="text-align:center;">1.2</td>
      <td style="text-align:center;">0.4</td>
      <td style="text-align:center;">1.1</td>
      <td style="text-align:center;">2.0</td>
    </tr>
  </tbody>
</table>

"""


assistantBlocks_type = "markdown"
assistantBlocks_content = """

You may like to review [additional details](?drawer=PE-structural.html) about the Northfield PE structural models.\n
\n
Next we will apply the overlays using information from the Hamilton Lane Fund\n
\n
When you are ready to proceed, just let me know.
"""
from __future__ import annotations

from uuid import uuid4


def upload_block_component() -> str:
    """Return HTML snippet for upload block rendering."""
    block_id = f"upload-block-{uuid4().hex}"
    button_style = (
        "display:inline-flex; align-items:center; justify-content:center;"
        "padding:6px 14px; border-radius:4px; border:1px solid #96f2d7;"
        "background-color:#e6fcf5; color:#0c8573; font-weight:600;"
        "font-size:13px; cursor:pointer; text-decoration:none;"
        "transition: background-color 0.2s ease, border-color 0.2s ease;"
    )
    hover_handler = "this.style.backgroundColor='#c3fae8';"
    leave_handler = "this.style.backgroundColor='#e6fcf5';"
    onchange_parts = [
        "(function(input){",
        "var file=input.files&&input.files[0];",
        "var info=document.getElementById('",
        block_id,
        "-file-info');",
        "if(!file){if(info){info.textContent='';}return;}",
        "var reader=new FileReader();",
        "reader.onload=function(){",
        "var textarea=document.getElementById('",
        block_id,
        "-textarea');",
        "if(textarea){textarea.value=typeof reader.result==='string'?reader.result:'';}",
        "};",
        "reader.readAsText(file);",
        "var size=file.size;",
        "var sizeText=size>=1024?(size/1024).toFixed(1)+' KB':size+' B';",
        "if(info){info.textContent=file.name+' ('+sizeText+')';}",
        "})(this);"
    ]
    onchange_handler = "".join(onchange_parts)
    return f"""
<div id="{block_id}" style="display:flex; flex-direction:column; gap:12px;">
  <div style="display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap;">
    <div style="display:flex; flex-direction:column; gap:4px; min-width:0; flex:1;">
      <span style="font-size:14px; font-weight:600; color:#1d1d1f;">Upload a file or paste data in the text area below</span>
      <span id="{block_id}-file-info" style="font-size:12px; color:#495057; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;"></span>
    </div>
    <label for="{block_id}-file-input" style="{button_style}" onmouseenter="{hover_handler}" onmouseleave="{leave_handler}">
      Upload file
    </label>
  </div>
  <textarea id="{block_id}-textarea" style="width:100%; min-height:160px; border:1px solid #ced4da; border-radius:6px; padding:10px; font-family:monospace; font-size:13px; line-height:1.4; resize:none; overflow:auto;" placeholder="Paste CSV or text data here"></textarea>
  <input id="{block_id}-file-input" type="file" accept=".csv,.txt,text/csv,text/plain" style="display:none;" onchange="{onchange_handler}" />
</div>
""".strip()

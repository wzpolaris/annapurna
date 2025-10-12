
import os
import sys

from analytics.rbsa.rbsa_pipeline import rbsa_main
from rbsa.ai_pipeline import ai_main


_proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
print(_proj_root)


out = rbsa_main(_proj_root)

print({k: (list(v["selected"]) if k != "final" else "final") for k,v in out.items() if k in ["A","B","D","final"]})

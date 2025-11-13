import json
from datetime import datetime
import re
import os

def export_notebook_to_markdown(notebook_path, output_path, 
                                show_markdown=True, show_code=True, show_cell_output=True, 
                                show_html=True, show_all=True):
    """
    Export notebook content (markdown cells + code outputs) to a consolidated markdown file.
    
    Parameters:
    -----------
    notebook_path : str
        Path to the .ipynb notebook file
    output_path : str
        Path where the .md file will be saved
    show_markdown : bool, default=True
        Include markdown cells in the export
    show_code : bool, default=True
        Include code cells in the export
    show_cell_output : bool, default=True
        Include cell outputs (print statements, plots, etc.)
    show_html : bool, default=False
        Include HTML output (e.g., DataFrame HTML tables)
    show_all : bool, default=True
        If True, overrides other flags and shows everything
    """
    # If show_all is True, override all other flags
    if show_all:
        show_markdown = True
        show_code = True
        show_cell_output = True
        show_html = True
    
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    
    md_lines = []
    
    # Header
    md_lines.append(f"# HLPAF Analysis Report")
    md_lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md_lines.append(f"\n**Source Notebook:** `{notebook_path.split('/')[-1]}`")
    md_lines.append("\n---\n")
    
    # Get absolute path to artifacts directory
    notebook_dir = os.path.dirname(os.path.abspath(notebook_path))
    artifacts_dir = os.path.abspath(os.path.join(notebook_dir, '..', 'artifacts'))
    
    # Process each cell
    for i, cell in enumerate(nb['cells'], 1):
        cell_type = cell['cell_type']
        
        if cell_type == 'markdown' and show_markdown:
            # Add markdown cell content directly
            content = ''.join(cell['source'])
            md_lines.append(content)
            md_lines.append("\n")
            
        elif cell_type == 'code':
            # Get execution count
            exec_count = cell.get('execution_count', None)
            
            # Extract image file paths from code if present
            code = ''.join(cell['source'])
            image_paths = []
            if code:
                # Look for fig.savefig or plt.savefig calls
                savefig_pattern = r"(?:fig\.savefig|plt\.savefig)\s*\(\s*['\"]([^'\"]+)['\"]"
                matches = re.findall(savefig_pattern, code)
                for match in matches:
                    # Convert relative path to absolute
                    if match.startswith('../artifacts/'):
                        abs_path = os.path.join(artifacts_dir, os.path.basename(match))
                        image_paths.append(abs_path)
                    elif match.startswith('artifacts/'):
                        abs_path = os.path.join(os.path.dirname(artifacts_dir), match)
                        image_paths.append(abs_path)
                    else:
                        image_paths.append(match)
            
            # Show code if enabled
            if show_code:
                if code.strip():  # Only show non-empty code
                    md_lines.append(f"\n### Code Cell [{exec_count if exec_count else 'Not Run'}]\n")
                    md_lines.append("```python\n")
                    md_lines.append(code)
                    md_lines.append("\n```\n")
            
            # Process outputs if enabled
            if show_cell_output and 'outputs' in cell and cell['outputs']:
                md_lines.append("\n**Output:**\n\n")
                
                image_index = 0  # Track which image path to use
                for output in cell['outputs']:
                    output_type = output.get('output_type', '')
                    
                    # Handle different output types
                    if output_type == 'stream':
                        # Standard print() output
                        text = ''.join(output.get('text', []))
                        md_lines.append("```\n")
                        md_lines.append(text)
                        md_lines.append("```\n\n")
                        
                    elif output_type == 'execute_result':
                        # Display data (like dataframe repr)
                        data = output.get('data', {})
                        if 'text/plain' in data:
                            text = ''.join(data['text/plain'])
                            md_lines.append("```\n")
                            md_lines.append(text)
                            md_lines.append("\n```\n\n")
                        if show_html and 'text/html' in data:
                            html = ''.join(data['text/html'])
                            md_lines.append(html)
                            md_lines.append("\n\n")
                            
                    elif output_type == 'display_data':
                        # Images, plots, etc.
                        data = output.get('data', {})
                        if 'image/png' in data:
                            # Use extracted image path if available
                            if image_index < len(image_paths):
                                img_path = image_paths[image_index]
                                md_lines.append(f"**Plot saved to:** `{img_path}`\n\n")
                                image_index += 1
                            else:
                                md_lines.append("*[Plot image - see notebook or saved PNG files]*\n\n")
                        if 'text/plain' in data:
                            text = ''.join(data['text/plain'])
                            md_lines.append(f"```\n{text}\n```\n\n")
                            
                    elif output_type == 'error':
                        # Error output
                        md_lines.append("**Error:**\n\n")
                        md_lines.append("```\n")
                        md_lines.append(output.get('ename', '') + ': ' + output.get('evalue', ''))
                        md_lines.append("\n```\n\n")
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(''.join(md_lines))
    
    print(f"✓ Notebook exported to: {output_path}")
    print(f"  Total lines: {len(md_lines)}")
    print(f"  Options: markdown={show_markdown}, code={show_code}, output={show_cell_output}, html={show_html}")
    return output_path

# Run the export
notebook_path = '07_HLPAF_Analysis.ipynb'
output_path = '../artifacts/HLPAF_Analysis_Report.md'

try:
    export_notebook_to_markdown(notebook_path, output_path,
                                show_all=False,
                                show_markdown=True,                               
                                show_code=False, 
                                show_cell_output=True
                                )
except Exception as e:
    print(f"Error exporting notebook: {e}")
    import traceback
    traceback.print_exc()
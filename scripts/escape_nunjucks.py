#!/usr/bin/env python3
"""
Pre-build script: Escape {{ }} and {% %} in markdown code blocks
to prevent HonKit/GitBook nunjucks template engine from processing them.
"""
import re
import os
import sys

def escape_code_blocks(content):
    """Wrap code blocks containing {{ }} or {% %} with {% raw %}{% endraw %}"""
    lines = content.split('\n')
    result = []
    in_code_block = False
    code_block_lines = []
    code_fence = ''
    
    for line in lines:
        if not in_code_block:
            # Check for code block start
            match = re.match(r'^(`{3,}|~{3,})', line)
            if match:
                in_code_block = True
                code_fence = match.group(1)[0]  # ` or ~
                code_fence_len = len(match.group(1))
                code_block_lines = [line]
            else:
                result.append(line)
        else:
            code_block_lines.append(line)
            # Check for code block end
            if re.match(r'^' + re.escape(code_fence) * code_fence_len + r'\s*$', line):
                in_code_block = False
                block_text = '\n'.join(code_block_lines)
                
                # Check if block contains {{ }}, {% %}, or {# #} and is NOT already wrapped
                has_template_syntax = bool(re.search(r'\{\{|\{%|\{#', block_text))
                already_wrapped = any('{% raw %}' in l for l in code_block_lines)
                
                if has_template_syntax and not already_wrapped:
                    result.append('{% raw %}')
                    result.extend(code_block_lines)
                    result.append('{% endraw %}')
                else:
                    result.extend(code_block_lines)
                code_block_lines = []
    
    # Handle unclosed code block
    if code_block_lines:
        result.extend(code_block_lines)
    
    return '\n'.join(result)

def process_directory(directory):
    """Process all markdown files in directory recursively."""
    count = 0
    for root, dirs, files in os.walk(directory):
        # Skip hidden directories and node_modules
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']
        for fname in files:
            if fname.endswith('.md'):
                fpath = os.path.join(root, fname)
                with open(fpath, 'r', encoding='utf-8') as f:
                    original = f.read()
                
                escaped = escape_code_blocks(original)
                
                if escaped != original:
                    with open(fpath, 'w', encoding='utf-8') as f:
                        f.write(escaped)
                    count += 1
                    print(f"  Escaped: {fpath}")
    
    print(f"Processed markdown files. {count} files modified.")

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else '.'
    process_directory(target)

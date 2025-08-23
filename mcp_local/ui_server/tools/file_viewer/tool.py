"""File Viewer MCP Tool - Self-contained implementation."""

import json
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from fastmcp import Context

# Load the HTML template
TEMPLATE_PATH = Path(__file__).parent / "template.html"
HTML_TEMPLATE = TEMPLATE_PATH.read_text()


async def file_viewer(
    ctx: Context,
    file_path: str = "/example/script.py",
    file_content: Optional[str] = None
) -> Dict[str, Any]:
    """
    Displays file content with syntax highlighting and line numbers.
    
    Args:
        file_path: Path to the file being displayed
        file_content: Optional content to display (if not provided, uses sample code)
    
    Returns:
        MCP UI resource response with syntax-highlighted file viewer
    """
    resource_id = str(uuid.uuid4())
    
    # Sample Python code if none provided
    if not file_content:
        file_content = '''import asyncio
from typing import List, Dict, Any
import json

class DataProcessor:
    """Process and transform data efficiently."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cache = {}
    
    async def process_batch(self, items: List[Dict]) -> List[Dict]:
        """Process a batch of items concurrently."""
        tasks = [self._process_item(item) for item in items]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]
    
    async def _process_item(self, item: Dict) -> Optional[Dict]:
        """Process a single item with caching."""
        key = item.get('id')
        if key in self.cache:
            return self.cache[key]
        
        # Simulate processing
        await asyncio.sleep(0.1)
        processed = {
            **item,
            'processed': True,
            'timestamp': datetime.now().isoformat()
        }
        
        self.cache[key] = processed
        return processed

async def main():
    """Main entry point."""
    processor = DataProcessor({'max_batch': 100})
    
    sample_data = [
        {'id': 1, 'name': 'Item 1', 'value': 100},
        {'id': 2, 'name': 'Item 2', 'value': 200},
        {'id': 3, 'name': 'Item 3', 'value': 300}
    ]
    
    results = await processor.process_batch(sample_data)
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    asyncio.run(main())'''
    
    # Determine file info
    file_name = Path(file_path).name
    file_ext = Path(file_path).suffix.lower()
    file_lines = len(file_content.splitlines())
    file_size = f"{len(file_content)} bytes"
    
    # Map extensions to language classes and icons
    language_map = {
        '.py': ('python', 'Python', '🐍'),
        '.js': ('javascript', 'JavaScript', '📜'),
        '.ts': ('typescript', 'TypeScript', '📘'),
        '.jsx': ('jsx', 'React JSX', '⚛️'),
        '.tsx': ('tsx', 'React TSX', '⚛️'),
        '.json': ('json', 'JSON', '📋'),
        '.yaml': ('yaml', 'YAML', '📝'),
        '.yml': ('yaml', 'YAML', '📝'),
        '.md': ('markdown', 'Markdown', '📄'),
        '.sh': ('bash', 'Shell Script', '🖥️'),
        '.html': ('html', 'HTML', '🌐'),
        '.css': ('css', 'CSS', '🎨'),
        '.sql': ('sql', 'SQL', '🗃️'),
        '.xml': ('xml', 'XML', '📰'),
        '.rs': ('rust', 'Rust', '🦀'),
        '.go': ('go', 'Go', '🐹'),
        '.java': ('java', 'Java', '☕'),
        '.cpp': ('cpp', 'C++', '⚙️'),
        '.c': ('c', 'C', '⚙️'),
        '.cs': ('csharp', 'C#', '🔷'),
        '.rb': ('ruby', 'Ruby', '💎'),
        '.php': ('php', 'PHP', '🐘'),
        '.swift': ('swift', 'Swift', '🦉'),
        '.kt': ('kotlin', 'Kotlin', '🅺'),
    }
    
    language_class, file_language, file_icon = language_map.get(
        file_ext, ('plaintext', 'Plain Text', '📄')
    )
    
    # Escape HTML in content
    import html
    escaped_content = html.escape(file_content)
    
    # Replace template variables
    html_content = HTML_TEMPLATE.replace("{{ file_icon }}", file_icon)
    html_content = html_content.replace("{{ file_name }}", file_name)
    html_content = html_content.replace("{{ file_language }}", file_language)
    html_content = html_content.replace("{{ file_lines }}", str(file_lines))
    html_content = html_content.replace("{{ file_size }}", file_size)
    html_content = html_content.replace("{{ language_class }}", language_class)
    html_content = html_content.replace("{{ file_content }}", escaped_content)
    
    return {
        "type": "resource",
        "resource": {
            "uri": f"ui://file/{resource_id}",
            "name": "File Viewer",
            "mimeType": "text/html",
            "text": html_content
        }
    }


# Tool metadata for registration
TOOL_DEFINITION = {
    "name": "file_viewer",
    "description": "Displays file content with syntax highlighting and line numbers",
    "function": file_viewer
}
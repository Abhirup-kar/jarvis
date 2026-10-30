import os
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio
from tools.base_tool import BaseTool
from tools.registry import tool_registry
from config.settings import settings

@tool_registry.register
class ReadDocumentTool(BaseTool):
    name = "read_document"
    description = "Reads the content of a document or text/code file within the system workspace."
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Relative or absolute path to the file to read"
                },
                "max_lines": {
                    "type": "integer",
                    "description": "Maximum number of lines to return (default: 200)",
                    "default": 200
                }
            },
            "required": ["file_path"]
        }

    async def execute(self, file_path: str, max_lines: int = 200, **kwargs) -> Dict[str, Any]:
        def _read():
            path = Path(file_path)
            if not path.is_absolute():
                path = settings.STORAGE_DIR / file_path
                if not path.exists():
                    path = settings.BASE_DIR / file_path

            if not path.exists():
                return {"error": f"File not found: {file_path}"}
            if not path.is_file():
                return {"error": f"Path is not a file: {file_path}"}

            try:
                lines = []
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    for i, line in enumerate(f):
                        if i >= max_lines:
                            break
                        lines.append(line)
                return {
                    "status": "success",
                    "file_path": str(path),
                    "lines_read": len(lines),
                    "content": "".join(lines)
                }
            except Exception as e:
                return {"error": f"Failed to read file: {str(e)}"}

        return await asyncio.to_thread(_read)


@tool_registry.register
class WriteDocumentTool(BaseTool):
    name = "write_document"
    description = "Creates or updates a document, note, or code file in the storage directory."
    risk_level = "medium"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_name": {
                    "type": "string",
                    "description": "Name or relative path of the file (e.g. 'notes.md' or 'meeting_minutes.txt')"
                },
                "content": {
                    "type": "string",
                    "description": "Text content to write to the file"
                },
                "append": {
                    "type": "boolean",
                    "description": "If true, appends content to existing file; otherwise overwrites",
                    "default": False
                }
            },
            "required": ["file_name", "content"]
        }

    async def execute(self, file_name: str, content: str, append: bool = False, **kwargs) -> Dict[str, Any]:
        def _write():
            path = Path(file_name)
            if not path.is_absolute():
                path = settings.STORAGE_DIR / file_name

            path.parent.mkdir(parents=True, exist_ok=True)
            mode = "a" if append else "w"

            try:
                with open(path, mode, encoding="utf-8") as f:
                    f.write(content if not append else f"\n{content}")
                return {
                    "status": "success",
                    "file_path": str(path),
                    "bytes_written": len(content),
                    "mode": "append" if append else "overwrite"
                }
            except Exception as e:
                return {"error": f"Failed to write file: {str(e)}"}

        return await asyncio.to_thread(_write)


@tool_registry.register
class ListDocumentsTool(BaseTool):
    name = "list_documents"
    description = "Lists files and documents in the assistant's storage workspace."
    risk_level = "low"

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "subdirectory": {
                    "type": "string",
                    "description": "Optional subdirectory within storage directory to list",
                    "default": ""
                }
            }
        }

    async def execute(self, subdirectory: str = "", **kwargs) -> Dict[str, Any]:
        def _list():
            target_dir = settings.STORAGE_DIR / subdirectory if subdirectory else settings.STORAGE_DIR
            if not target_dir.exists():
                return {"error": f"Directory not found: {target_dir}"}

            files = []
            for item in target_dir.glob("**/*"):
                if item.is_file():
                    files.append({
                        "name": item.name,
                        "relative_path": str(item.relative_to(settings.STORAGE_DIR)),
                        "size_bytes": item.stat().st_size
                    })
            return {"status": "success", "count": len(files), "files": files}

        return await asyncio.to_thread(_list)


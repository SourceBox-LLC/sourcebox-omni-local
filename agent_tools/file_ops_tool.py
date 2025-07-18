import os
import shutil
import fnmatch
import logging
import stat
import math
from pathlib import Path
from typing import Union
from datetime import datetime

# Configure module-level logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class FileOperationsTool:
    """
    A comprehensive tool for file operations designed to be easily used by AI agents.
    Provides robust file browsing, management, and search capabilities.
    """

    def __init__(self) -> None:
        # For optional caching or other stateful needs
        self._last_path: Path = None  # type: ignore
        self._last_result: dict = {}

    def list_directory(
        self,
        path: Union[str, Path] = None,
        pattern: str = None,
        show_hidden: bool = False,
        sort_by: str = "name",
        reverse: bool = False
    ) -> dict:
        """
        List files and directories in the specified path with filtering and sorting.

        Args:
            path: Directory to list (defaults to current working directory).
            pattern: Glob pattern to filter names.
            show_hidden: Include hidden items if True.
            sort_by: One of 'name', 'size', 'type', 'modified'.
            reverse: Reverse sort order if True.

        Returns:
            Dict containing current_path, parent_path, directories, files, totals, and error if any.
        """
        try:
            base = Path(path or Path.cwd()).expanduser().resolve()
            if not base.exists():
                return {"error": f"Path does not exist: {base}"}
            if not base.is_dir():
                return {"error": f"Path is not a directory: {base}"}

            dirs = []
            files = []
            for entry in base.iterdir():
                name = entry.name
                # Hidden check
                if not show_hidden:
                    if name.startswith('.'):
                        continue
                    if os.name == 'nt':
                        try:
                            attrs = entry.stat().st_file_attributes
                            if attrs & stat.FILE_ATTRIBUTE_HIDDEN:
                                continue
                        except Exception:
                            pass
                # Pattern filter
                if pattern and not fnmatch.fnmatch(name, pattern):
                    continue

                stat_info = entry.stat()
                info = {
                    "name": name,
                    "path": str(entry),
                    "size": stat_info.st_size,
                    "size_human": self._human_readable_size(stat_info.st_size),
                    "modified": stat_info.st_mtime,
                    "modified_date": datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    "created": stat_info.st_ctime,
                    "created_date": datetime.fromtimestamp(stat_info.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                    "is_hidden": name.startswith('.')
                }
                if entry.is_dir():
                    info["type"] = "directory"
                    dirs.append(info)
                else:
                    info["type"] = "file"
                    info["extension"] = entry.suffix.lower().lstrip('.')
                    files.append(info)

            # Sorting
            keyfunc = self._get_sort_key(sort_by)
            dirs.sort(key=keyfunc, reverse=reverse)
            files.sort(key=keyfunc, reverse=reverse)

            result = {
                "current_path": str(base),
                "parent_path": str(base.parent),
                "directories": dirs,
                "files": files,
                "total_dirs": len(dirs),
                "total_files": len(files),
                "error": None
            }
            self._last_path = base
            self._last_result = result
            return result

        except Exception as e:
            logger.exception("list_directory failed")
            return {"error": f"Error listing directory: {e}"}

    def copy_item(
        self,
        source: Union[str, Path],
        destination: Union[str, Path],
        overwrite: bool = False
    ) -> dict:
        """
        Copy a file or directory to destination.
        """
        src = Path(source).expanduser().resolve()
        dst = Path(destination).expanduser().resolve()
        if not src.exists():
            return {"error": f"Source does not exist: {src}"}
        if dst.exists() and not overwrite:
            return {"error": f"Destination exists and overwrite=False: {dst}"}
        try:
            if src.is_file():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                op_type = "file"
            else:
                if dst.exists() and overwrite:
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                op_type = "directory"
            return {"operation": "copy", "type": op_type, "source": str(src), "destination": str(dst), "success": True}
        except Exception as e:
            logger.exception("copy_item failed")
            return {"operation": "copy", "error": str(e), "success": False}

    def move_item(
        self,
        source: Union[str, Path],
        destination: Union[str, Path],
        overwrite: bool = False
    ) -> dict:
        """
        Move a file or directory to destination.
        """
        src = Path(source).expanduser().resolve()
        dst = Path(destination).expanduser().resolve()
        if not src.exists():
            return {"error": f"Source does not exist: {src}"}
        if dst.exists() and not overwrite:
            return {"error": f"Destination exists and overwrite=False: {dst}"}
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists() and overwrite:
                if dst.is_file():
                    dst.unlink()
                else:
                    shutil.rmtree(dst)
            shutil.move(str(src), str(dst))
            op_type = "file" if src.is_file() else "directory"
            return {"operation": "move", "type": op_type, "source": str(src), "destination": str(dst), "success": True}
        except Exception as e:
            logger.exception("move_item failed")
            return {"operation": "move", "error": str(e), "success": False}

    def delete_item(self, path: Union[str, Path], recursive: bool = False) -> dict:
        """
        Delete a file or directory.
        """
        target = Path(path).expanduser().resolve()
        if not target.exists():
            return {"error": f"Path does not exist: {target}"}
        try:
            if target.is_file():
                target.unlink()
                op_type = "file"
            else:
                if recursive:
                    shutil.rmtree(target)
                    op_type = "directory"
                elif not any(target.iterdir()):
                    target.rmdir()
                    op_type = "directory"
                else:
                    return {"error": "Directory not empty and recursive=False", "success": False}
            return {"operation": "delete", "type": op_type, "path": str(target), "success": True}
        except Exception as e:
            logger.exception("delete_item failed")
            return {"operation": "delete", "error": str(e), "success": False}

    def rename_item(self, path: Union[str, Path], new_name: str) -> dict:
        """
        Rename a file or directory to new_name.
        """
        target = Path(path).expanduser().resolve()
        if not target.exists():
            return {"error": f"Path does not exist: {target}"}
        if any(sep in new_name for sep in (os.sep, os.altsep or '')):
            return {"error": f"new_name must not contain path separators: {new_name}"}
        new_path = target.with_name(new_name)
        if new_path.exists():
            return {"error": f"Destination exists: {new_path}"}
        try:
            target.rename(new_path)
            op_type = "file" if new_path.is_file() else "directory"
            return {"operation": "rename", "type": op_type, "original": str(target), "new": str(new_path), "success": True}
        except Exception as e:
            logger.exception("rename_item failed")
            return {"operation": "rename", "error": str(e), "success": False}

    def create_directory(self, path: Union[str, Path]) -> dict:
        """
        Create a new directory at the given path.
        """
        target = Path(path).expanduser().resolve()
        if target.exists():
            return {"error": f"Path already exists: {target}", "success": False}
        try:
            target.mkdir(parents=True, exist_ok=False)
            return {"operation": "create_directory", "path": str(target), "success": True}
        except Exception as e:
            logger.exception("create_directory failed")
            return {"operation": "create_directory", "error": str(e), "success": False}

    def create_file(
        self,
        path: Union[str, Path],
        content: str = "",
        overwrite: bool = False,
        encoding: str = "utf-8"
    ) -> dict:
        """
        Create a new file with optional content.
        """
        target = Path(path).expanduser().resolve()
        if target.exists() and not overwrite:
            return {"error": f"File exists and overwrite=False: {target}", "success": False}
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding=encoding)
            return {"operation": "create_file", "path": str(target), "size": len(content), "success": True}
        except Exception as e:
            logger.exception("create_file failed")
            return {"operation": "create_file", "error": str(e), "success":False}

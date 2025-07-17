import os

def browse_files(directory: str = None) -> str:
    """List files/folders in the given directory (or cwd)."""
    try:
        # If no directory specified, use current working directory
        if not directory:
            directory = os.getcwd()
        else:
            # Handle various path issues
            # 1. Handle escaped apostrophes in paths (e.g., S\'Bussiso)
            directory = directory.replace("\\'Bussiso", "'Bussiso")
            
            # 2. Handle truncation at apostrophe (e.g. C:\Users\S)
            if directory.startswith("C:\\Users\\S") and "Bussiso" not in directory:
                directory = directory.replace("C:\\Users\\S", "C:\\Users\\S'Bussiso")
                print(f"Fixed truncated path: {directory}")
            
            # 3. Print the path we're trying to use for debugging
            print(f"Attempting to browse directory: {directory}")
            
        # Try to list the directory with multiple approaches
        # Approach 1: Direct path as provided
        try:
            files = os.listdir(directory)
            
            # Format output with folders having trailing slash
            entries = []
            for f in files:
                full_path = os.path.join(directory, f)
                if os.path.isdir(full_path):
                    entries.append(f + '/')
                else:
                    entries.append(f)
                    
            return f"Contents of {directory}:\n" + "\n".join(sorted(entries))
            
        except FileNotFoundError:
            # Approach 2: Try with explicit apostrophe handling
            try:
                # Replace any potentially escaped apostrophes
                fixed_path = directory.replace("\\'Bussiso", "'Bussiso")
                if fixed_path != directory:
                    print(f"Trying with fixed apostrophes: {fixed_path}")
                    files = os.listdir(fixed_path)
                    entries = []
                    for f in files:
                        full_path = os.path.join(fixed_path, f)
                        if os.path.isdir(full_path):
                            entries.append(f + '/')
                        else:
                            entries.append(f)
                    return f"Contents of {fixed_path}:\n" + "\n".join(sorted(entries))
            except:
                pass
                
            # Approach 3: Try with raw string
            try:
                raw_path = r"{}".format(directory)
                print(f"Trying with raw string: {raw_path}")
                files = os.listdir(raw_path)
                entries = []
                for f in files:
                    full_path = os.path.join(raw_path, f)
                    if os.path.isdir(full_path):
                        entries.append(f + '/')
                    else:
                        entries.append(f)
                return f"Contents of {raw_path}:\n" + "\n".join(sorted(entries))
            except:
                pass
            
            # If all approaches failed
            return f"Directory not found: {directory}"
    except Exception as e:
        return f"Error accessing directory: {str(e)}"


if __name__ == "__main__":
    directory = "C:\\Users\\S'Bussiso\\Desktop"
    result = browse_files(directory)
    print(result)
import os
import sys
import re
import datetime
import json
import threading
import time
import webbrowser
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory, render_template_string

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS)
    except Exception:
        base_path = Path(__file__).parent
    return base_path / relative_path

def get_config_path():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent / "config.json"
    else:
        return Path(__file__).parent / "config.json"

def load_config():
    config_path = get_config_path()
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[-] Failed to load config: {e}")
    return {}

def save_config(config_data):
    config_path = get_config_path()
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"[-] Failed to save config: {e}")
        return False

def get_markdown_dir():
    config = load_config()
    path_str = config.get("markdown_dir", "")
    if not path_str:
        return Path("C:/_My2026/_EVERBK/markdown")
    return Path(path_str)

def get_resources_dir():
    return get_markdown_dir() / "_resources"

# Initialize Flask with resource-friendly folders
if getattr(sys, 'frozen', False):
    template_folder = str(get_resource_path("templates"))
    static_folder = str(get_resource_path("static"))
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
else:
    app = Flask(__name__)

def get_file_meta_info(filepath, keep_version=None):
    """Retrieve formatted file size and modification date metadata."""
    try:
        stat = filepath.stat()
        size_bytes = stat.st_size
        if size_bytes < 1024:
            size_str = f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            size_str = f"{size_bytes / 1024:.1f} KB"
        else:
            size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
            
        mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
        date_str = mtime.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        size_str = "Unknown"
        date_str = "Unknown"
        
    info = {
        "filename": filepath.name,
        "size": size_str,
        "date": date_str
    }
    if keep_version:
        info["keep_version"] = keep_version
    return info

def format_evernote_date(date_str):
    """Format Evernote XML dates (YYYYMMDDTHHMMSSZ) into readable dates."""
    if not date_str:
        return ""
    try:
        m = re.match(r'^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z$', str(date_str))
        if m:
            return f"{m.group(1)}-{m.group(2)}-{m.group(3)} {m.group(4)}:{m.group(5)}:{m.group(6)}"
        return str(date_str)
    except Exception:
        return str(date_str)

def parse_note_file(filepath):
    """Parse front matter and extract note metadata and snippet."""
    content = ""
    title = filepath.stem
    tags = []
    created = ""
    updated = ""
    
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
            
        # Parse YAML Front Matter
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', text, re.DOTALL)
        if match:
            front_matter_text = match.group(1)
            content = match.group(2)
            try:
                import yaml
                metadata = yaml.safe_load(front_matter_text)
                if metadata:
                    title = metadata.get("title", title)
                    tags = metadata.get("tags", [])
                    if isinstance(tags, str):
                        tags = [tags]
                    elif not isinstance(tags, list):
                        tags = []
                    created = metadata.get("created", "")
                    updated = metadata.get("updated", "")
            except Exception as e:
                print(f"[-] YAML parsing error in {filepath.name}: {e}")
        else:
            content = text
            
    except Exception as e:
        print(f"[-] Failed to read {filepath.name}: {e}")
        content = ""
        
    # Generate clean plaintext snippet (strip markdown and HTML tags)
    snippet = content[:300]
    snippet = re.sub(r'#+\s+', '', snippet) # Strip headers
    snippet = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', snippet) # Strip link urls, keep text
    snippet = re.sub(r'[*_`~]', '', snippet) # Strip formatting chars
    snippet = re.sub(r'<[^<]+?>', '', snippet) # Strip any inline HTML tags
    snippet = re.sub(r'\s+', ' ', snippet).strip() # Collapse whitespaces
    
    if len(snippet) > 130:
        snippet = snippet[:130] + "..."
    
    return {
        "filename": filepath.name,
        "title": title,
        "tags": tags,
        "created": format_evernote_date(created),
        "updated": format_evernote_date(updated),
        "snippet": snippet
    }

@app.route('/')
def index():
    """Serve the main index.html file."""
    # Look for index.html in the templates folder
    template_path = get_resource_path("templates/index.html")
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return render_template_string(html_content)
    except FileNotFoundError:
        return "<h3>index.html not found inside templates folder.</h3>", 404

@app.route('/cleaner')
def cleaner():
    """Serve the duplicate cleaner UI."""
    template_path = get_resource_path("templates/cleaner.html")
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return render_template_string(html_content)
    except FileNotFoundError:
        return "<h3>cleaner.html not found inside templates folder.</h3>", 404

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    if request.method == 'POST':
        data = request.get_json() or {}
        new_path = data.get("markdown_dir", "").strip()
        if not new_path:
            return jsonify({"status": "error", "error": "Path cannot be empty"}), 400
        
        path_obj = Path(new_path)
        if not path_obj.exists() or not path_obj.is_dir():
            return jsonify({"status": "error", "error": "Directory does not exist or is not a folder"}), 400
        
        config = load_config()
        config["markdown_dir"] = str(path_obj.resolve().as_posix())
        if save_config(config):
            return jsonify({"status": "success", "markdown_dir": config["markdown_dir"]})
        else:
            return jsonify({"status": "error", "error": "Failed to save configuration"}), 500
    else:
        config = load_config()
        current_path = config.get("markdown_dir", "")
        is_valid = False
        if current_path:
            path_obj = Path(current_path)
            is_valid = path_obj.exists() and path_obj.is_dir()
        return jsonify({
            "markdown_dir": current_path,
            "is_valid": is_valid,
            "default_path": "C:/_My2026/_EVERBK/markdown"
        })

@app.route('/api/notebooks')
def get_notebooks():
    """Get list of notebooks (folders) with their respective note count."""
    md_dir = get_markdown_dir()
    if not md_dir.exists():
        return jsonify([])
        
    notebooks = []
    for entry in md_dir.iterdir():
        if entry.is_dir() and not entry.name.startswith("_"):
            # Count markdown files
            md_files = list(entry.glob("*.md"))
            notebooks.append({
                "name": entry.name,
                "count": len(md_files)
            })
            
    # Sort alphabetically
    notebooks.sort(key=lambda x: x["name"])
    return jsonify(notebooks)

@app.route('/api/notes/<notebook_name>')
def get_notes_in_notebook(notebook_name):
    """Get lists of note metadata for a given notebook."""
    md_dir = get_markdown_dir()
    notebook_path = md_dir / notebook_name
    if not notebook_path.exists() or not notebook_path.is_dir():
        return jsonify([]), 404
        
    notes = []
    for filepath in notebook_path.glob("*.md"):
        notes.append(parse_note_file(filepath))
        
    # Sort by created date descending (latest first)
    notes.sort(key=lambda x: x["created"], reverse=True)
    return jsonify(notes)

@app.route('/api/notes/<notebook_name>/<filename>/raw')
def get_raw_note_content(notebook_name, filename):
    """Retrieve the raw markdown content of a specific note."""
    md_dir = get_markdown_dir()
    note_path = md_dir / notebook_name / filename
    if not note_path.exists():
        return jsonify({"error": "Note not found"}), 404
        
    try:
        with open(note_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        return text, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/resources/<path:filename>')
def get_resource(filename):
    """Serve attachment files (images, PDFs) from the resources directory."""
    resources_dir = get_resources_dir()
    if not resources_dir.exists():
        return jsonify({"error": "Resources directory does not exist"}), 404
    return send_from_directory(resources_dir, filename)

@app.route('/api/tags')
def get_all_tags():
    """Aggregate all tags across all notes in the backup database."""
    md_dir = get_markdown_dir()
    if not md_dir.exists():
        return jsonify({})
        
    tag_counts = {}
    for notebook_dir in md_dir.iterdir():
        if notebook_dir.is_dir() and not notebook_dir.name.startswith("_"):
            for filepath in notebook_dir.glob("*.md"):
                try:
                    note_info = parse_note_file(filepath)
                    for tag in note_info.get("tags", []):
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
                except Exception:
                    pass
                    
    # Sort tags alphabetically
    sorted_tags = dict(sorted(tag_counts.items()))
    return jsonify(sorted_tags)

@app.route('/api/search')
def search_notes():
    """Perform a global full-text search across all notes (title, tags, and content)."""
    query = request.args.get('q', '').strip().lower()
    if not query:
        return jsonify([])
        
    results = []
    md_dir = get_markdown_dir()
    if not md_dir.exists():
        return jsonify([])
        
    for notebook_dir in md_dir.iterdir():
        if notebook_dir.is_dir() and not notebook_dir.name.startswith("_"):
            for filepath in notebook_dir.glob("*.md"):
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        text = f.read()
                        
                    note_info = parse_note_file(filepath)
                    
                    # Search query inside title, tags, or full body text
                    title_match = query in note_info["title"].lower()
                    tag_match = any(query in tag.lower() for tag in note_info["tags"])
                    content_match = query in text.lower()
                    
                    if title_match or tag_match or content_match:
                        # Append search match result
                        results.append({
                            "notebook": notebook_dir.name,
                            "filename": filepath.name,
                            "title": note_info["title"],
                            "created": note_info["created"],
                            "tags": note_info["tags"],
                            "snippet": note_info["snippet"]
                        })
                except Exception as e:
                    print(f"[-] Search error in {filepath.name}: {e}")
                    
    # Sort by created date descending
    results.sort(key=lambda x: x["created"], reverse=True)
    return jsonify(results)

@app.route('/api/cleaner/scan/<notebook_name>')
def scan_duplicates(notebook_name):
    """Scan notebook for duplicate notes and group them into keep vs delete lists."""
    md_dir = get_markdown_dir()
    notebook_path = md_dir / notebook_name
    if not notebook_path.exists() or not notebook_path.is_dir():
        return jsonify({"keep": [], "delete": []}), 404

    # Read all md files
    all_files = list(notebook_path.glob("*.md"))
    
    # Group files by base name
    # base name is the stem with the trailing _\d+ stripped if present.
    groups = {}
    for fp in all_files:
        filename = fp.name
        stem = fp.stem
        # check for duplicate suffix (e.g. _1, _2)
        match = re.match(r'^(.*?)(_\d+)$', stem)
        if match:
            base_name = match.group(1)
            suffix = match.group(2)
        else:
            base_name = stem
            suffix = ""
            
        if base_name not in groups:
            groups[base_name] = []
        groups[base_name].append({
            "filepath": fp,
            "filename": filename,
            "base_name": base_name,
            "suffix": suffix
        })
        
    keep_list = []
    delete_list = []
    
    for base_name, file_entries in groups.items():
        if len(file_entries) == 1:
            # Only one file, absolutely keep it
            keep_list.append(get_file_meta_info(file_entries[0]["filepath"]))
        else:
            # Multiple files with same base name.
            # Sort them:
            # 1. Non-suffix file first (suffix == "")
            # 2. Sort by suffix number
            def sort_key(entry):
                s = entry["suffix"]
                if not s:
                    return (0, 0)
                try:
                    num = int(s[1:])
                    return (1, num)
                except ValueError:
                    return (2, s)
            
            sorted_entries = sorted(file_entries, key=sort_key)
            
            # The first one is the KEEP file
            keep_entry = sorted_entries[0]
            keep_list.append(get_file_meta_info(keep_entry["filepath"]))
            
            # The rest are DELETE files
            for del_entry in sorted_entries[1:]:
                delete_list.append(get_file_meta_info(del_entry["filepath"], keep_version=keep_entry["filename"]))
                
    # Sort results for presentation
    keep_list.sort(key=lambda x: x["filename"].lower())
    delete_list.sort(key=lambda x: x["filename"].lower())
    
    return jsonify({
        "keep": keep_list,
        "delete": delete_list
    })

@app.route('/api/cleaner/delete', methods=['POST'])
def delete_duplicates():
    """Securely delete specified duplicate markdown files."""
    data = request.get_json() or {}
    notebook = data.get("notebook", "").strip()
    files_to_delete = data.get("files", [])
    
    if not notebook or not files_to_delete:
        return jsonify({"status": "error", "errors": ["Invalid payload"]}), 400
        
    # Security: check notebook name
    if ".." in notebook or "/" in notebook or "\\" in notebook:
        return jsonify({"status": "error", "errors": ["Invalid notebook path"]}), 400
        
    md_dir = get_markdown_dir()
    notebook_path = md_dir / notebook
    if not notebook_path.exists() or not notebook_path.is_dir():
        return jsonify({"status": "error", "errors": ["Notebook directory not found"]}), 400
        
    deleted_count = 0
    errors = []
    
    for filename in files_to_delete:
        filename = filename.strip()
        # Security check: filename
        if ".." in filename or "/" in filename or "\\" in filename:
            errors.append(f"Security blocked invalid filename: {filename}")
            continue
        if not filename.endswith(".md"):
            errors.append(f"Security blocked non-markdown file: {filename}")
            continue
            
        file_path = notebook_path / filename
        if not file_path.exists():
            errors.append(f"File not found: {filename}")
            continue
            
        try:
            file_path.unlink()
            deleted_count += 1
        except Exception as e:
            errors.append(f"Failed to delete {filename}: {str(e)}")
            
    if errors:
        return jsonify({
            "status": "partial" if deleted_count > 0 else "error",
            "deleted": deleted_count,
            "errors": errors
        })
        
    return jsonify({
        "status": "success",
        "deleted": deleted_count,
        "errors": []
    })

@app.route('/api/notes/delete', methods=['POST'])
def delete_single_note():
    """Securely delete an individual markdown note file."""
    data = request.get_json() or {}
    notebook = data.get("notebook", "").strip()
    filename = data.get("filename", "").strip()
    
    if not notebook or not filename:
        return jsonify({"status": "error", "error": "Invalid payload"}), 400
        
    # Security check: notebook and filename for path traversal
    if ".." in notebook or "/" in notebook or "\\" in notebook:
        return jsonify({"status": "error", "error": "Security block: invalid notebook path"}), 400
    if ".." in filename or "/" in filename or "\\" in filename:
        return jsonify({"status": "error", "error": "Security block: invalid filename"}), 400
    if not filename.endswith(".md"):
        return jsonify({"status": "error", "error": "Security block: only markdown files are permitted"}), 400
        
    md_dir = get_markdown_dir()
    notebook_path = md_dir / notebook
    if not notebook_path.exists() or not notebook_path.is_dir():
        return jsonify({"status": "error", "error": "Notebook directory not found"}), 400
        
    file_path = notebook_path / filename
    if not file_path.exists():
        return jsonify({"status": "error", "error": "Note file not found"}), 404
        
    try:
        file_path.unlink()
        return jsonify({"status": "success", "message": f"Successfully deleted {filename}"})
    except Exception as e:
        return jsonify({"status": "error", "error": f"Deletion failed: {str(e)}"}), 500

def start_browser():
    # Wait for the Flask server to initialize
    time.sleep(1.5)
    url = "http://127.0.0.1:5000/"
    print(f"[+] Opening browser automatically at {url} ...")
    webbrowser.open(url)

if __name__ == '__main__':
    # Start on localhost:5000
    print("[+] Starting Evernote Archive Navigator local web server...")
    
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        threading.Thread(target=start_browser, daemon=True).start()
        
    print("[+] Base Markdown Path:", get_markdown_dir())
    
    is_frozen = getattr(sys, 'frozen', False)
    debug_mode = not is_frozen
    app.run(host='127.0.0.1', port=5000, debug=debug_mode)



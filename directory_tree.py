#!/usr/bin/env python3
"""
Directory Tree Generator
-----------------------
Dieses Skript erzeugt eine Baumstruktur aller Verzeichnisse und Dateien 
im aktuellen Verzeichnis oder einem angegebenen Pfad und speichert sie in einer Textdatei.
"""

import os
import argparse
from datetime import datetime

def get_tree(start_path, ignore_dirs=None, ignore_files=None, max_depth=None, current_depth=0):
    """
    Rekursiv die Verzeichnisstruktur als String erzeugen
    
    Args:
        start_path: Startverzeichnis
        ignore_dirs: Liste von zu ignorierenden Verzeichnissen
        ignore_files: Liste von zu ignorierenden Dateitypen
        max_depth: Maximale Tiefe der Rekursion
        current_depth: Aktuelle Tiefe (für Rekursion)
    
    Returns:
        String mit der Baumdarstellung
    """
    if ignore_dirs is None:
        ignore_dirs = ['.git', '__pycache__', 'venv', 'node_modules', '.idea', '.vscode']
    
    if ignore_files is None:
        ignore_files = ['.pyc', '.pyo', '.pyd', '.git', '.DS_Store']
    
    if max_depth is not None and current_depth > max_depth:
        return ""
    
    tree = ""
    
    try:
        items = os.listdir(start_path)
        items.sort()
        
        for item in items:
            item_path = os.path.join(start_path, item)
            
            # Ignoriere spezifische Verzeichnisse und Dateien
            if os.path.isdir(item_path) and item in ignore_dirs:
                continue
                
            if any(item.endswith(ext) for ext in ignore_files):
                continue
            
            # Erzeuge den Präfix (Einrückung)
            prefix = "    " * current_depth
            
            if os.path.isdir(item_path):
                # Verzeichnis
                tree += f"{prefix}├── {item}/\n"
                # Rekursiv in das Verzeichnis gehen
                subtree = get_tree(item_path, ignore_dirs, ignore_files, max_depth, current_depth + 1)
                if subtree:
                    tree += subtree
            else:
                # Datei
                tree += f"{prefix}├── {item}\n"
    
    except PermissionError:
        tree += f"    {'    ' * current_depth}[Zugriff verweigert]\n"
    except Exception as e:
        tree += f"    {'    ' * current_depth}[Fehler: {str(e)}]\n"
    
    return tree

def main():
    parser = argparse.ArgumentParser(description='Erzeugt eine Textdatei mit der Verzeichnisstruktur.')
    parser.add_argument('-p', '--path', default='.', help='Pfad zum Startverzeichnis (Standard: aktuelles Verzeichnis)')
    parser.add_argument('-o', '--output', default='directory_structure.txt', help='Ausgabedatei (Standard: directory_structure.txt)')
    parser.add_argument('-d', '--depth', type=int, help='Maximale Tiefe der Verzeichnisstruktur')
    parser.add_argument('--ignore-dirs', nargs='+', help='Zusätzliche zu ignorierende Verzeichnisse')
    parser.add_argument('--ignore-files', nargs='+', help='Zusätzliche zu ignorierende Dateitypen')
    
    args = parser.parse_args()
    
    start_path = os.path.abspath(args.path)
    output_file = args.output
    
    # Standard-Ignorierverzeichnisse erweitern
    ignore_dirs = ['.git', '__pycache__', 'venv', 'node_modules', '.idea', '.vscode']
    if args.ignore_dirs:
        ignore_dirs.extend(args.ignore_dirs)
    
    # Standard-Ignorierdateien erweitern
    ignore_files = ['.pyc', '.pyo', '.pyd', '.git', '.DS_Store']
    if args.ignore_files:
        ignore_files.extend(args.ignore_files)
    
    print(f"Generiere Verzeichnisstruktur von: {start_path}")
    print(f"Ausgabe in Datei: {output_file}")
    
    # Header für die Ausgabedatei generieren
    header = f"Verzeichnisstruktur für: {start_path}\n"
    header += f"Erstellt am: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    header += "=" * 80 + "\n\n"
    
    # Baumstruktur generieren
    tree = get_tree(start_path, ignore_dirs, ignore_files, args.depth)
    
    # In Datei schreiben
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write(tree)
    
    print(f"Verzeichnisstruktur wurde in '{output_file}' gespeichert.")

if __name__ == "__main__":
    main()
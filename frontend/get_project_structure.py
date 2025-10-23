import os

def print_directory_structure(path, indent=""):
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        print(f"{indent}{item}")
        if os.path.isdir(item_path) and ('node_modules' not in item_path) and ('env' not in item_path) and ('teradata_migration' not in item_path) and ('.git' not in item_path):
            print_directory_structure(item_path, indent + "  ")

# Usage
print_directory_structure(".")
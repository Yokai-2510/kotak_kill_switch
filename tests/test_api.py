import os

# Define the folder structure and files
structure = {
    "trading_kill_switch": {
        "main.py": "",
        "kotak_api": ["client_login.py", "positions.py"],
        "modules": ["mtm.py", "profit.py", "stop_loss.py", "utils.py"],
        "gui": ["dashboard.py"],
        "web_automation": ["driver.py"]
    }
}

def create_structure(base_path, struct):
    for name, content in struct.items():
        path = os.path.join(base_path, name)
        if isinstance(content, dict):
            os.makedirs(path, exist_ok=True)
            create_structure(path, content)
        elif isinstance(content, list):
            os.makedirs(path, exist_ok=True)
            for file in content:
                file_path = os.path.join(path, file)
                with open(file_path, "w") as f:
                    f.write(f"# {file}\n")
        else:  # Single file
            with open(path, "w") as f:
                f.write(f"# {name}\n")

# Run the creation in current directory
create_structure(".", structure)

print("Project structure created successfully!")

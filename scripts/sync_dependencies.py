import toml

# Paths to your files
requirements_file = "requirements.txt"
pyproject_file = "pyproject.toml"

# Read dependencies from requirements.txt
with open(requirements_file, "r") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

# Load the existing pyproject.toml
with open(pyproject_file, "r") as f:
    pyproject_data = toml.load(f)

# Update the dependencies section
if "project" not in pyproject_data:
    pyproject_data["project"] = {}

pyproject_data["project"]["dependencies"] = requirements

# Save the updated pyproject.toml
with open(pyproject_file, "w") as f:
    toml.dump(pyproject_data, f)

print("Sync between requirements.txt and pyproject.toml completed!")

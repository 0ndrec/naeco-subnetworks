import os
import glob
import yaml
import json
import copy

if os.path.exists("rpcs.json"):
    with open("rpcs.json", "r") as f:
        DEFAULT_RPCS = json.load(f)
else:
    print("File with default RPCs not found")

if os.path.exists("custom_rpc.json"):
    with open("custom_rpc.json", "r") as f:
        CUSTOM_RPCS = json.load(f)
else:
    print("File with custom RPCs not found")

def get_docker_compose_files():
    all_files = glob.glob("docker-compose*.yaml")
    print(f"Found {len(all_files)} docker-compose*.yaml files in the current directory.")
    files = [f for f in all_files if os.path.basename(f) != "docker-compose1.yaml"]
    if not files:
        print("No docker-compose*.yaml files, except docker-compose1.yaml, found in the current directory.")
    else:
        print(f"Files found for processing: {files}")
    return files

def load_yaml(file_path):
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)

def save_yaml(content, file_path):
    with open(file_path, 'w') as f:
        yaml.dump(content, f, sort_keys=False, default_flow_style=False, allow_unicode=True)
    print(f"File updated: {file_path}")

def construct_custom_rpcs(api_key):
    rpcs = copy.deepcopy(CUSTOM_RPCS)
    for chain_id, config in rpcs.items():
        if "{API_KEY}" in config["rpc"]:
            rpcs[chain_id]["rpc"] = config["rpc"].replace("{API_KEY}", api_key)
    return rpcs

def main():
    files = get_docker_compose_files()
    if not files:
        return

    print("\nChoose RPCS replacement option:")
    print("1. Replace with default RPCS configuration.")
    print("2. Replace with custom RPCS configuration using your API key.")
    choice = input("Enter 1 or 2: ").strip()

    if choice == '1':
        new_rpcs = DEFAULT_RPCS
    elif choice == '2':
        api_key = input("Enter your Alchemy API key: ").strip()
        if not api_key:
            print("API key cannot be empty.")
            return
        new_rpcs = construct_custom_rpcs(api_key)
    else:
        print("Invalid choice. Exiting.")
        return

    rpcs_json = json.dumps(new_rpcs, separators=(',', ':'))

    for file in files:
        try:
            content = load_yaml(file)

            services = content.get('services', {})
            updated = False
            for service_name, service_config in services.items():
                env = service_config.get('environment', {})
                if 'RPCS' in env:
                    print(f"Updating RPCS in service '{service_name}' of file '{file}'.")
                    env['RPCS'] = rpcs_json
                    updated = True
                else:
                    print(f"RPCS environment variable not found in service '{service_name}' of file '{file}'. Skipping.")

            if updated:
                save_yaml(content, file)
            else:
                print(f"File '{file}' does not require updating.")

        except Exception as e:
            print(f"Error processing file '{file}': {e}")

if __name__ == "__main__":
    main()

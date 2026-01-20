import click
import glob
import math
import requests
import yaml

import humanfriendly
from pathlib import Path

# Billable roles per Elasticsearch license terms
BILLABLE_ROLES = {"data", "data_hot", "data_warm", "data_cold", "data_content", "ml", "master"}
GB_DIVISOR = humanfriendly.parse_size("1GB", binary=True)

def convert_size_to_bytes(size_str):
    """Converts a size string (e.g. '1gb', '512mb') to bytes."""
    try:
        if not size_str:
            return 0
        return humanfriendly.parse_size(str(size_str), binary=True)
    except Exception:
        return 0

def dump_cluster_license(es_url, user, password, ca, insecure):
    """This function connects to an Elasticsearch cluster and dumps license and node information to a YAML file."""
    # Create a session object to keep the connection alive.
    session = requests.Session()
    session.auth = (user, password)
    # Use system CA bundle (True) by default, custom CA if provided, or disable verification if insecure
    session.verify = False if insecure else (ca or True)

    # Make a request to the _license and _nodes endpoint.
    response = session.get(f"{es_url}/_license")
    response_nodes = session.get(f"{es_url}/_nodes")

    # Query cat nodes for RAM info
    response_cat = session.get(f"{es_url}/_cat/nodes?v=true&h=name,ram.max&s=name&format=json")
    ram_map = {n['name']: convert_size_to_bytes(n.get('ram.max')) for n in response_cat.json()}

    # Get the cluster name from the _nodes response.
    cluster_name = response_nodes.json()["cluster_name"]
    license_type = response.json()["license"]["type"]

    nodes_dict = {}
    for node in response_nodes.json()["nodes"].values():
        node_name = node["name"]
        node_ram = ram_map.get(node_name, 0)
        is_billable = bool(BILLABLE_ROLES & set(node["roles"]))
        nodes_dict[node_name] = {
            "roles": node["roles"],
            "counts_against_license": int(is_billable),
            "ram.max": node_ram
        }

    billable_count = sum(n["counts_against_license"] for n in nodes_dict.values())
    total_ram = sum(n["ram.max"] for n in nodes_dict.values())

   # Create a dictionary with the results of all API calls.
    data = {
        "license": response.json()["license"],
        "nodes": {
            "_nodes": response_nodes.json()["_nodes"],
            "nodes": nodes_dict
        }
    }

    total_ram_gb = total_ram / GB_DIVISOR

    if license_type in ["platinum", "gold", "basic", "trial"]:
        # Logic from subscription agreement:
        # Billable Nodes = max(Role-based Nodes Count, ceil(Total RAM GB / 64))
        ram_billable_count = math.ceil(total_ram_gb / 64)
        data["billable nodes in the cluster"] = max(billable_count, ram_billable_count)
    else:
        data["Total amount of RAM consumed"] = round(total_ram_gb, 2)

   # Write the data to a YAML file.
    with open(f"{cluster_name}.yml", "w") as f:
        yaml.dump(data, f, default_flow_style=None)

def consolidate_cluster_info():
    """This function looks for all .yml files at the root of the current directory and creates a new yml file called "consolidated_license_usage.yaml"."""
    yml_files = glob.glob("*.yml")

    # Create a dictionary to store the consolidated license usage.
    consolidated_license_usage = {
        "list of audited clusters": [],
        "Total number of billable nodes": 0,
        "Total amount of RAM consumed": 0
    }

    # Loop through the .yml files and add their data to the consolidated license usage dictionary.
    for file in yml_files:
        # Open the .yml file.
        with open(file, "r") as f:
            try:
                # Load the data from the .yml file.
                data = yaml.safe_load(f)

                if not data:
                    continue

                # Add the basename of the .yml file to the list of audited clusters.
                consolidated_license_usage["list of audited clusters"].append(Path(file).stem)

                # Add totals
                if "billable nodes in the cluster" in data:
                    consolidated_license_usage["Total number of billable nodes"] += data["billable nodes in the cluster"]

                if "Total amount of RAM consumed" in data:
                    consolidated_license_usage["Total amount of RAM consumed"] += data["Total amount of RAM consumed"]
            except Exception:
                continue

    # Round the Total amount of RAM consumed
    consolidated_license_usage["Total amount of RAM consumed"] = round(consolidated_license_usage["Total amount of RAM consumed"], 2)

    # Write the consolidated license usage to a YAML file.
    if consolidated_license_usage["list of audited clusters"]:
        with open("consolidated_license_usage.yaml", "w") as f:
            yaml.dump(consolidated_license_usage, f, default_flow_style=None)

@click.command()
@click.option("--es-url", prompt="Elasticsearch URL", default="", help="The URL of the Elasticsearch instance.")
@click.option("-u", "--user", prompt="Username", default="", help="The username to connect to Elasticsearch.")
@click.option("-p", "--password", prompt="Password", hide_input=True, default="", help="The password to connect to Elasticsearch.")
@click.option("--ca", default=None, help="Path to your PEM encoded Certificate Authority used to validate tls")
@click.option("-i", "--insecure", is_flag=True, default=False, help="Do not verify tls certificate. This is insecure.")
@click.option("-g", "--gather", is_flag=True, default=False, help="Do not connect to a cluster, only consolidate local .yml files.")

def main(es_url, user, password, ca, insecure, gather):
    """
    This script lets you connect to an elasticsearch cluster with an url and gathers information about node names, roles, and the license applied.
    It will tell you which nodes in your cluster count against your license and report the total number used by the cluster.\n
    Everytime you run the script against a new cluster, the consolidated license usage file is updated with the new information.\n

    You can also run the script with -g / --gather to consolidate existing files without querying a cluster.
    """
    if not gather:
        dump_cluster_license(es_url, user, password, ca, insecure)
    consolidate_cluster_info()

if __name__ == "__main__":
    main()

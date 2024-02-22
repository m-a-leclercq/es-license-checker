import click
import requests
import yaml
import os


def dump_cluster_license(es_url, user, password, ca, insecure):
    """This function takes 3 arguments as input: an url, a user, and a password."""
    # set tls parameters for queries
    if insecure:
        verification = False
    else :
        verification = ca
    # Create a session object to keep the connection alive.
    session = requests.Session()

    # Add the user and password to the session.
    session.auth = (user, password)

    # Make a request to the _license and _nodes endpoint.
    response = session.get(f"{es_url}/_license", verify=verification)
    response_nodes = session.get(f"{es_url}/_nodes", verify=verification)

    # Get the cluster name from the _nodes response.
    cluster_name = response_nodes.json()["cluster_name"]

   # Create a dictionary with the results of both API calls.
    data = {
        "total number of licenses used by the cluster": sum(1 if any(role in node["roles"] for role in ["data", "data_hot", "data_warm", "data_cold", "data_content", "ml", "master"]) else 0 for node in response_nodes.json()["nodes"].values()),
        "license": response.json()["license"],
        "nodes": {
            "_nodes": response_nodes.json()["_nodes"],
            "nodes": {
                node["name"]: {
                    "roles": node["roles"],
                    "counts_against_license": 1 if any(role in node["roles"] for role in ["data", "data_hot", "data_warm", "data_cold", "data_content", "ml", "master"]) else 0
                }
                for node in response_nodes.json()["nodes"].values()
            }
        }
    }

   # Write the data to a YAML file.
    with open(f"{cluster_name}.yml", "w") as f:
        yaml.dump(data, f, default_flow_style=None)

def consolidate_cluster_info():
    """This function looks for all .yml files at the root of the current directory and creates a new yml file called "consolidated_license_usage.yaml"."""

    # Get a list of all the files in the current directory.
    files = os.listdir()

    # Filter the list of files to only include .yml files.
    yml_files = [file for file in files if file.endswith(".yml")]

    # Create a dictionary to store the consolidated license usage.
    consolidated_license_usage = {
        "list of audited clusters": [],
        "total number of licenses used": 0
    }

    # Loop through the .yml files and add their data to the consolidated license usage dictionary.
    for file in yml_files:
        # Open the .yml file.
        with open(file, "r") as f:
            # Load the data from the .yml file.
            data = yaml.safe_load(f)

            # Add the basename of the .yml file to the list of audited clusters.
            consolidated_license_usage["list of audited clusters"].append(os.path.splitext(os.path.basename(file))[0])

            # Add the total number of licenses used by the cluster to the total number of licenses used.
            consolidated_license_usage["total number of licenses used"] += data["total number of licenses used by the cluster"]

    # Write the consolidated license usage to a YAML file.
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

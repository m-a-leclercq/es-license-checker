import click
import requests
import yaml
import os

def dump_cluster_license(es_url, user, password):
   """This function takes 3 arguments as input: an url, a user, and a password."""

   # Create a session object to keep the connection alive.
   session = requests.Session()

   # Add the user and password to the session.
   session.auth = (user, password)

   # Make a request to the _license endpoint.
   response = session.get(f"{es_url}/_license")

   # Make a request to the _nodes endpoint.
   response_nodes = session.get(f"{es_url}/_nodes")

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
           consolidated_license_usage["list of audited clusters"].append(os.path.basename(file))

           # Add the total number of licenses used by the cluster to the total number of licenses used.
           consolidated_license_usage["total number of licenses used"] += data["total number of licenses used by the cluster"]

   # Write the consolidated license usage to a YAML file.
   with open("consolidated_license_usage.yaml", "w") as f:
       yaml.dump(consolidated_license_usage, f, default_flow_style=None)

@click.command()
@click.option("--es-url", prompt="Elasticsearch URL", help="The URL of the Elasticsearch instance.")
@click.option("-u", "--user", prompt="Username", help="The username to connect to Elasticsearch.")
@click.option("-p", "--password", prompt="Password", hide_input=True, help="The password to connect to Elasticsearch.")
def main(es_url, user, password):
   """This script takes 3 arguments as input: an url, a user, and a password. It will consolidate all .yml files found to give you a summary of your license usage."""
   dump_cluster_license(es_url, user, password)
   consolidate_cluster_info()

if __name__ == "__main__":
   main()

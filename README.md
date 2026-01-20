# es-license-checker
This python script allows elasticsearch customers to get an accurate inventory of how many licenses their clusters are using for platinum licenses.

It can also be used to estimate how many platinum licenses your basic cluster would require.

This script will give an approximate count of Enterprise Resource Units usage (ERU for Enterprise licensing).

# Installation
Create a new virtualenv
```
python3 -m venv license
```

Activate your virtualenv
```
source license/bin/activate
```

Install dependencies
```
pip install -r requirements.txt
```

Run the script against a cluster to get a detailed report of license usage and node roles. You will be prompted for a user and password at runtime.
```
python main.py --es-url https://localhost:9200
```

Each time you run the script and as long as you have queried more than one cluster, a `consolidated_license_usage.yaml` file will be created / updated with the list of `.yml` files that were inspected and the total number of billable nodes is then calculated.

# CHANGELOG
## v0.3.0
- Allows all licences to be counted, and checks whether platinum is capped by nodes or RAM. 

## v0.2.2
- Now only allows platinum, gold(discontinued) and basic licenses to be counted

## v0.2.1
- Wording changed for better clarity.

## v0.2.0
- Custom CA certificates can now be used for https.
- New flag -g allows recalculating the global license usage without querying an elasticsearch cluster.

## V0.1.0
Initial release.

# TODO
- Compatibility with Enterprise license.
- Better packaging(WIP).

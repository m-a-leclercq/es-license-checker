# es-license-checker
This python script allows elasticsearch customers to get an accurate inventory of how many licenses their clusters are using.

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

Each time you run the script, a `consolidated_license_usage.yaml` file will be created / updated with the list of `.yml` files that were inspected and the total number of licenses is then calculated.

# CHANGELOG
## V0.1.0
Initial release.

# TODO
- Allow for an insecure flag and a CA-cert flag for more flexibility around cert management in enterprise environments.
- Better packaging

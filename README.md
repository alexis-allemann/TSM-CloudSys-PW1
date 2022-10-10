# HOW TO USE
## GOOGLE
1. set the env varible
```bash
export GOOGLE_APPLICATION_CREDENTIALS='Google/your_mp'
```
2. install the depedencies
```bash
pip3 install -r Google/requirements.txt
```
3. run the script
```bash
python3 Google/GCS.py
```
## Azure
Run the `pip install -r requirement.txt` command in a python environment

Change the variables in the .env file if needed and add the `AZURE_CLIENT_SECRET` key (ask to Teo Ferrari to have the secret, or use yours)

Run the `python Azure.py` command
## AWS
1. Install the depedencies
```bash
pip3 install -r AWS/requirements.txt
```
2. run the script, with you aws access key
```bash
python3 AWS/aws.py <your_key>
```
# Sync-all-GCP-IP-to-Cloudflare-security-rules-WAF

`gcloud services enable cloudfunctions.googleapis.com cloudscheduler.googleapis.com cloudresourcemanager.googleapis.com compute.googleapis.com` 

Cloudflare:  
Cloudflare Sync Token see Passwork “Cloudflare Google Cloud IP Sync Security Rules”.  

- Navigation → IAM & Admin → Service Accounts → + **Create Service Account**

- Add IAM **Viewer, Secret Manager Secret Accessor and Cloud Functions Invoker** to new service account (in GCP Project where you want to run Cloud Run Function).
- Add IAM Role for

- Security → Secret Manager → + **Create Secret**

- Create **main.py** and **requirements.txt:**

- Create Cloud Scheduler e.g. daily RUN.

- Use / Add environemnt variables in Cloud Run see main.py

You should / can use API Keys as secrets. e.g add in environment variable 
- cf_secret_name = cf_api_token
- function_target = main
- office_ip = 10.10.10.10
- gcp_project = projectA
- cf_zone_id = ...
- cf_ruleset_id = ...
- cf_rule_id = ..


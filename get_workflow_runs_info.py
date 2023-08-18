from collections import Counter
import pandas as pd
import requests

time_format = "%Y-%m-%dT%H:%M:%SZ"
headers = {"Authorization": "Bearer <INSERT ACCESS TOKEN HERE>", 'Accept': 'application/vnd.github.v3+json'}

user_name = "NWChemEx-Project"
repo_name = "ParallelZone"

keys = ["Workflow ID", "Run ID", "Status", "Time", "Commit"]
excel_d = {key:[] for key in keys}

runs = []
page = 1
while True:
    params = {'page': page}
    response = requests.get(f"https://api.github.com/repos/{user_name}/{repo_name}/actions/runs", headers=headers, params=params)
    data = response.json()

    if not data["workflow_runs"]:
        break
    
    runs.extend(data['workflow_runs'])
    page += 1

for run in runs:
    res = requests.get(f"https://api.github.com/repos/{user_name}/{repo_name}/actions/runs/{run['id']}/timing", headers=headers)
    timing_data = res.json()
    # print(f"Workflow ID: {workflow_id} Run ID: {run['id']} Status: {run['conclusion']} Time: {time_difference} Commit: {run['head_commit']['id']}")
    if timing_data.get('run_duration_ms', None) is None:
        time = -1
    else:
        time = timing_data['run_duration_ms']/1000
    excel_d["Workflow ID"].append(run["workflow_id"])
    excel_d["Run ID"].append(run["id"])
    excel_d["Status"].append(run["conclusion"])
    excel_d["Time"].append(time)
    excel_d["Commit"].append(run["head_commit"]["id"])
print(Counter(excel_d["Status"]))


df = pd.DataFrame(excel_d)
df.to_excel("./workflow_info.xlsx", index=False)
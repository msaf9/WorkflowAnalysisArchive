from collections import Counter
import pandas as pd
import requests
import os
import json

time_format = "%Y-%m-%dT%H:%M:%SZ"
headers = {"Authorization": "Bearer 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", 'Accept': 'application/vnd.github.v3+json'}

user_name = "openai"
repo_name = "triton"

def get_basic_info(run):
    # workflow_id, workflow_run_id, conclusion, status

    return {"workflow_id": run["workflow_id"],"workflow_run_id": run["id"], "conclusion": run["conclusion"], "status": run["status"]}

def get_timing_data(run_id):
    res = requests.get(f"https://api.github.com/repos/{user_name}/{repo_name}/actions/runs/{run_id}/timing", headers=headers)
    timing_data = res.json()
    if timing_data.get('run_duration_ms', None) is None:
        time = -1
    else:
        time = timing_data['run_duration_ms']/1000
    return {"runtime": time}

def get_jobs_info(jobs_url, workflow_id, workflow_run_id):
    jobs = []
    page = 1
    while True:
        params = {'page': page}
        response = requests.get(jobs_url, headers=headers, params=params)
        data = response.json()

        if not data.get("jobs", None):
            break
        
        jobs.extend(data['jobs'])
        page += 1

    jobs_info = []
    os.makedirs('jobs', exist_ok=True)
    os.makedirs('steps', exist_ok=True)
    os.makedirs(f'jobs/{workflow_id}', exist_ok=True)
    os.makedirs(f'steps/{workflow_id}', exist_ok=True)
    
    file_path = os.path.join(workflow_id, workflow_run_id)
    
    for job in jobs:
        d = {"id": job["id"], "status": job["status"], "name": job["name"], "started_at": job["started_at"], "completed_at": job["completed_at"], "steps": 'steps/' + file_path + '_' + str(job['id']) + '.json'}
        with open('steps/' + file_path + '_' + str(job['id']) + '.json', 'w') as file:
            json.dump(job['steps'], file)
        jobs_info.append(d)

    with open('jobs/' + file_path + '.json', 'w') as file:
            json.dump(jobs_info, file)
    
    return {"jobs_info_file": 'jobs/' + file_path + '.json'}

def get_commits_info(sha, workflow_id, workflow_run_id):
    res = requests.get(f"https://api.github.com/repos/{user_name}/{repo_name}/commits/{sha}", headers=headers)
    commits_data = res.json()
    os.makedirs('commits', exist_ok=True)
    os.makedirs(f'commits/{workflow_id}', exist_ok=True)

    file_path = os.path.join(workflow_id, workflow_run_id)
    l = []
    for file_change in commits_data.get('files', []):
        d = {}
        d['filename'] = file_change.get('filename', 'N/A')
        d['status'] = file_change.get('status', 'N/A')
        d['additions'] = file_change.get('additions', 'N/A')
        d['deletions'] = file_change.get('deletions', 'N/A')
        d['changes'] = file_change.get('changes', 'N/A')
        # File changes contain file changes if the status is modified, contains the file name if it is renamed.
        if file_change.get('patch', None) is not None:
            d['file_content_changes'] = file_change['patch']
        elif file_change.get('previous_filename', None) is not None:
            d['file_content_changes'] = file_change['previous_filename']
        else:
            d['file_content_changes'] = 'N/A'
        l.append(d)

    with open('commits/' +file_path + '.json', 'w') as file:
        json.dump(l, file)
    
    return {"message": commits_data["commit"]["message"], "total": commits_data["stats"]["total"], "additions": commits_data["stats"]["additions"], "deletions": commits_data["stats"]["deletions"], "commits_file_path": 'commits/' +file_path + '.json'}


# runs = []
# page = 1
# while True:
#     params = {'page': page}
#     response = requests.get(f"https://api.github.com/repos/{user_name}/{repo_name}/actions/runs", headers=headers, params=params)
#     data = response.json()
#     if not data["workflow_runs"]:
#         break
    
#     runs.extend(data['workflow_runs'])
#     page += 1

# with open('workflow_runs.json', 'w') as file:
#     json.dump(runs, file)

with open('workflow_runs.json', 'r') as file:
    runs = json.load(file)

df = pd.DataFrame(columns=("workflow_id", "workflow_run_id", "conclusion", "status", "runtime", "jobs_info_file", "message", "total", "additions", "deletions", "commits_file_path"))

i = 0
for index in range(4870, len(runs)):
    run = runs[index]
    basic_info = get_basic_info(run)
    time = get_timing_data(run['id'])
    jobs_info = get_jobs_info(run["jobs_url"], str(basic_info['workflow_id']), str(run['id']))
    commits_info = get_commits_info(run["head_sha"], str(basic_info['workflow_id']), str(run['id']))
    d = {**basic_info, **time, **jobs_info, **commits_info}
    df = pd.concat([df, pd.DataFrame([d])])
    df.to_excel("./workflow_info_7.xlsx", index=False)
    i += 1
    print(i)
    

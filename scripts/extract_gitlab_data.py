import requests
import pandas as pd
from datetime import datetime
import os

# =====================================================
# CONFIGURAÇÕES
# =====================================================
GITLAB_URL = "http://gitlab/api/v4"
TOKEN = os.getenv("GITLAB_TOKEN", "O_TOKEN_VEM_AQUI")
HEADERS = {"Private-Token": TOKEN}

# =====================================================
# FUNÇÕES DE EXTRAÇÃO
# =====================================================
def get_groups():
    url = f"{GITLAB_URL}/groups?per_page=100"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def get_group_projects(group_id):
    url = f"{GITLAB_URL}/groups/{group_id}/projects?per_page=100"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def get_issues(project_id):
    url = f"{GITLAB_URL}/projects/{project_id}/issues?per_page=100"
    issues = []
    page = 1
    while True:
        response = requests.get(f"{url}&page={page}", headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        if not data:
            break
        issues.extend(data)
        page += 1
    return issues

# =====================================================
# COLETA DE DADOS
# =====================================================
data = []

groups = get_groups()
for group in groups:
    group_id = group["id"]
    group_name = group["name"]

    projects = get_group_projects(group_id)
    for project in projects:
        project_id = project["id"]
        project_name = project["name"]
        project_description = project.get("description", "N/A")

        issues = get_issues(project_id)

        if issues:
            for issue in issues:
                assignees_list = [a["name"] for a in issue.get("assignees", [])] if issue.get("assignees") else []
                assignee_name = issue.get("assignee", {}).get("name", "N/A") if issue.get("assignee") else "N/A"
                assignees = ", ".join(assignees_list) if assignees_list else assignee_name

                labels = ", ".join(issue["labels"]) if issue.get("labels") else "N/A"

                issue_data = {
                    "Group Name": group_name,
                    "Group ID": group_id,
                    "Project Name": project_name,
                    "Project ID": project_id,
                    "Project Description": project_description,
                    "Issue Title": issue["title"],
                    "Issue ID": issue["iid"],
                    "Description": issue.get("description", "N/A"),
                    "Labels": labels,
                    "Author": issue["author"]["name"],
                    "Assignees": assignees,
                    "Created At": issue["created_at"],
                    "Updated At": issue["updated_at"],
                    "Closed At": issue.get("closed_at", "N/A"),
                    "Due Date": issue.get("due_date", "N/A"),
                    "Milestone": issue["milestone"]["title"] if issue.get("milestone") else "N/A",
                    "Milestone ID": issue["milestone"]["id"] if issue.get("milestone") else "N/A",
                    "Milestone Due Date": issue["milestone"].get("due_date") if issue.get("milestone") else "N/A",
                    "Weight": issue.get("weight", "N/A"),
                    "Time Estimate": issue.get("time_stats", {}).get("human_time_estimate", "N/A"),
                    "Total Time Spent": issue.get("time_stats", {}).get("human_total_time_spent", "N/A"),
                    "Comments Count": issue.get("user_notes_count", 0),
                    "Subscribers Count": issue.get("subscribers_count", 0),
                    "Discussion Locked": str(issue.get("discussion_locked", False)),
                    "Last Edited At": issue.get("last_edited_at", "N/A"),
                    "Last Edited By": issue.get("last_edited_by", {}).get("name", "N/A") if issue.get("last_edited_by") else "N/A",
                    "Merge Requests Count": issue.get("merge_requests_count", 0),
                    "Health Status": issue.get("health_status", "N/A"),
                    "State": issue["state"],
                    "Confidential": str(issue.get("confidential", False)),
                    "Web URL": issue["web_url"]
                }
                data.append(issue_data)

        else:
            data.append({
                "Group Name": group_name,
                "Group ID": group_id,
                "Project Name": project_name,
                "Project ID": project_id,
                "Project Description": project_description,
                "Issue Title": "N/A",
                "Issue ID": "N/A",
                "Description": "N/A",
                "Labels": "N/A",
                "Author": "N/A",
                "Assignees": "N/A",
                "Created At": "N/A",
                "Updated At": "N/A",
                "Closed At": "N/A",
                "Due Date": "N/A",
                "Milestone": "N/A",
                "Milestone ID": "N/A",
                "Milestone Due Date": "N/A",
                "Weight": "N/A",
                "Time Estimate": "N/A",
                "Total Time Spent": "N/A",
                "Comments Count": 0,
                "Subscribers Count": 0,
                "Discussion Locked": "False",
                "Last Edited At": "N/A",
                "Last Edited By": "N/A",
                "Merge Requests Count": 0,
                "Health Status": "N/A",
                "State": "N/A",
                "Confidential": "False",
                "Web URL": "N/A"
            })

# =====================================================
# DATAFRAME
# =====================================================
df = pd.DataFrame(data)

# =====================================================
# ENRIQUECIMENTO DE DADOS (ENGENHARIA DE DADOS)
# =====================================================
def get_complexidade(labels):
    if "C1" in labels:
        return "C1-Baixa"
    elif "C2" in labels:
        return "C2-Média"
    elif "C3" in labels:
        return "C3-Alta"
    elif "C4" in labels:
        return "C4-Altíssima"
    else:
        return "N/A"

def get_peso(labels):
    if "C1" in labels:
        return 1
    elif "C2" in labels:
        return 2
    elif "C3" in labels:
        return 3
    elif "C4" in labels:
        return 4
    else:
        return 0

def get_prioridade(labels):
    if "P1" in labels:
        return "P1-Muito Alta"
    elif "P2" in labels:
        return "P2-Alta"
    elif "P3" in labels:
        return "P3-Média"
    elif "P4" in labels:
        return "P4-Baixa"
    elif "P5" in labels:
        return "P5-Muito Baixa"
    else:
        return "Não informado"

def get_status(labels, state):
    labels_lower = labels.lower()
    if "em andamento" in labels_lower:
        return "Em andamento"
    elif "a fazer" in labels_lower:
        return "A fazer"
    elif "revisão" in labels_lower:
        return "Revisão-Homologação"
    elif "teste" in labels_lower:
        return "Testes"
    elif "backlog" in labels_lower:
        return "Backlog"
    elif state.lower() == "closed" or "concluído" in labels_lower:
        return "Concluído"
    else:
        return "Não definido"

df["Complexidade"] = df["Labels"].apply(get_complexidade)
df["Peso Calculado"] = df["Labels"].apply(get_peso)
df["Prioridade Calculada"] = df["Labels"].apply(get_prioridade)
df["Status Consolidado"] = df.apply(lambda x: get_status(x["Labels"], x["State"]), axis=1)

# =====================================================
# EXPORTAÇÃO
# =====================================================
output_file = "gitlab_groups_projects_issues_detailed_report.csv"
df.to_csv(output_file, index=False, encoding="utf-8-sig")

print(f"Arquivo exportado com sucesso: {output_file}")

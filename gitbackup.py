import os, secrets, subprocess, argparse, json, secrets
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument("command", type=str, help="Operation name" ,choices=["init", "commit", "back", "pull", "update"])
parser.add_argument("--account", "-a", type=str, help="Put the name of the github account", )
parser.add_argument("--repo", "-r", type=str, help="Put the name of the repository you will use")
parser.add_argument("--name", "-n", type=str, help="Put the name of your branch")
parser.add_argument("--to", "-b", type=str, help="Put the commit id to go back to")
args = parser.parse_args()

current_directory = os.path.dirname(__file__)
current_directory = os.path.abspath(current_directory if current_directory else ".")
os.chdir(current_directory)

def get_options():
    os.chdir(os.path.expanduser('~'))
    res = None
    if not os.path.exists(".gitbackup_options"):
        if args.account and args.repo:
            res = {"account":args.account,"repo":args.repo}
            with open(".gitbackup_options","w") as f:
                f.write(json.dumps(res))
        else:
            exit("For the first execution, insert the account name and the repository name")
    else:
        with open(".gitbackup_options","r") as f:
            res = json.loads(f.read())
        if args.account: res["account"] = args.account
        if args.repo: res["repo"] = args.repo
        if args.account or args.repo:
            with open(".gitbackup_options","w") as f: f.write(json.dumps(res))  
    os.chdir(current_directory)
    return res

def execute_commands(commands):
    os.chdir(current_directory)
    for line in commands:
        if line[0] == "cd":
            os.chdir(line[1])
        else:
            subprocess.run(line)
    os.chdir(current_directory)

this_filename = os.path.basename(__file__)

options = get_options()

git_url = f"git@github.com:{options['account']}/{options['repo']}.git"

tmp_path = f"/tmp/{secrets.token_hex(16)}"
os.environ["GIT_SSH_COMMAND"] = "ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"

if args.command.lower() == "init":
    if os.path.exists(".git"): exit("You are already in a git repository!")
    if not args.name: exit("Please specify a name of the backup with -n")
    branch_name = args.name

    #gitignore fix
    if not os.path.exists(".gitignore"):
        with open(".gitignore","wb"): pass
    with open(".gitignore","a") as f: f.write(f"\n{this_filename}\n")
    
    #Creation of the branch
    execute_commands([
        ["git", "clone", "--config", f"user.email={secrets.token_hex(3)+'@'+secrets.token_hex(3)}", "--config", f"user.name={secrets.token_hex(3)}", git_url, "--single-branch", tmp_path],
        ["cd", tmp_path],
        ["git", "checkout", "-b", branch_name],
        ["mv", "-f", f"{tmp_path}/.git", current_directory],
        ["rm", "-rf" ,tmp_path],
        ["cd", current_directory],
        ["git", "add", "."],
        ["git", "commit", "-am", "Backup commit!"],
        ["git", "push", "--set-upstream", "origin", branch_name],
    ])
    
elif args.command.lower() == "commit":
    if not os.path.exists(".git"): exit("Run init option first!")
    execute_commands([
        ["git", "add", "."],
        ["git", "commit", "-am", f"Commit: {datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}"],
        ["git", "push"],
    ])
elif args.command.lower() == "pull":
    if not os.path.exists(".git"): exit("Run init option first!")
    execute_commands([
        ["git", "pull"]
    ])
elif args.command.lower() == "update":
    if not os.path.exists(".git"): exit("Run init option first!")
    execute_commands([
        ["git", "pull"],
        ["git", "add", "."],
        ["git", "commit", "-am", f"Commit: {datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}"],
        ["git", "push"],
        ["docker-compose","up","-d","--build"]
    ])
elif args.command.lower() == "back":
    if not os.path.exists(".git"): exit("Run init option first!")
    if not args.to: exit("insert the commit id to return to with -b")
    commit_id = args.to
    execute_commands([
        ["git", "revert", f"{commit_id}..HEAD", "--no-commit"],
        ["git", "add", "."],
        ["git", "commit", "-am", f"Back: {commit_id} - {datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}"],
        ["git", "push"],
    ])
else:
    exit("Invalid command")

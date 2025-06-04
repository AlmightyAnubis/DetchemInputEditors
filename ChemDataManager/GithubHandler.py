from tkinter import messagebox

from github import Github

# Authentication is defined via github.Auth
from github import Auth
from github.ContentFile import ContentFile

import GeneralUtil.TextModifiers


def send_pull_request(target_branch, title, body) -> int:
    # using an access token
    file = open("ChemDataManager/ChemData.csv")
    auth = Auth.Token("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")

    # First create a Github instance:

    # Public Web Github
    g = Github(auth=auth)

    # Github Enterprise with custom hostname
    repo = g.get_user().get_repo("DetchemInputEditors")

    source_branch = repo.default_branch
    sb = repo.get_branch(source_branch)
    branch_names = []
    for branch in repo.get_branches():
        branch_names.append(branch.name)


    changes = False
    contents: ContentFile = repo.get_contents("ChemDataManager/ChemData.csv", ref=source_branch)

    if target_branch not in branch_names:
        repo.create_git_ref(ref='refs/heads/' + target_branch, sha=sb.commit.sha)

    content = "".join(file.readlines())
    decoded = contents.decoded_content.decode()
    if decoded == content:
        messagebox.showinfo("No Commit Send","Irgnored ChemData, since there was no change.")
    else:
        print("Commit Sent Successfully for ChemData")
        repo.update_file("ChemDataManager/ChemData.csv","Update of ChemData.csv",content,branch=target_branch,sha=contents.sha)
        changes = True
    file.close()


    file = open("ChemDataManager/Sources.csv")
    contents: ContentFile = repo.get_contents("ChemDataManager/Sources.csv", ref=target_branch)

    content = "".join(file.readlines())
    decoded = contents.decoded_content.decode()
    if decoded == content:
        messagebox.showinfo("No Commit Send","Irgnored Sources, since there was no change.")
    else:
        print("Commit Sent Successfully for Sources")
        repo.update_file("ChemDataManager/Sources.csv","Update of Sources.csv",content,branch=target_branch,sha=contents.sha)
        changes = True
    file.close()

    if changes:
        pull = repo.create_pull(base="master", head=target_branch, title=title, body=body)
    # To close connections after use
    g.close()
    return 0
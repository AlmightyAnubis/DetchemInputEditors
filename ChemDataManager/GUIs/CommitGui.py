import datetime
import tkinter as tk
from tkinter import messagebox

from ChemDataManager import GithubHandler, global_vars, ConfigHandler
from GeneralUtil.CenterGui import CenterWindow


class CommitHandler(CenterWindow):

    variables: list = []

    author = ""
    university = ""
    email = ""


    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(1,weight=1)

        row = 0
        label = tk.Label(self, text="Thermodynamic Data", font=("Arial", 20))
        label.grid(row=row, column=0, columnspan=2)
        row -=- 1
        author = tk.Label(self, text="Author:", justify=tk.LEFT)
        author.grid(row=row, column=0)
        author_var = tk.StringVar()
        author_var.set(global_vars.author)
        self.variables.append(author_var)
        def set_author(value):
            self.author = value
            global_vars.author = value
        author_var.trace_add("write",lambda a,b,c: set_author(author_var.get()))
        entry = tk.Entry(self, textvariable=author_var, justify=tk.LEFT)
        entry.grid(row=row, column=1, sticky=tk.EW)
        row += 1

        univerity = tk.Label(self, text="University:", justify=tk.LEFT)
        univerity.grid(row=row, column=0)
        university_var = tk.StringVar()
        university_var.set(global_vars.university)
        self.variables.append(university_var)
        def set_university(value):
            self.university = value
            global_vars.university = value
        university_var.trace_add("write",lambda a,b,c: set_university(university_var.get()))
        entry = tk.Entry(self, textvariable=university_var, justify=tk.LEFT)
        entry.grid(row=row, column=1, sticky=tk.EW)
        row += 1

        email = tk.Label(self, text="Email:", justify=tk.LEFT)
        email.grid(row=row, column=0)
        email_var = tk.StringVar()
        email_var.set(global_vars.email)
        self.variables.append(email_var)
        def set_email(value):
            self.email = value
            global_vars.email = value
        email_var.trace_add("write",lambda a,b,c: set_email(email_var.get()))
        entry = tk.Entry(self, textvariable=email_var, justify=tk.LEFT)
        entry.grid(row=row, column=1, sticky=tk.EW)
        row += 1

        comment = tk.Label(self, text="Info to Data:")
        comment.grid(row=row, column=0, sticky=tk.N)
        self.comment = tk.Text(self, height=5, width=30)
        self.comment.bind("<Return>", lambda e: self.comment.config(height=max(5,self.comment.get(1.0, "end").count("\n") + 1)))
        self.comment.bind("<Delete>", lambda e: self.comment.config(height=max(5,self.comment.get(1.0, "end").count("\n"))))
        self.comment.bind("<BackSpace>", lambda e: self.comment.config(height=max(5,self.comment.get(1.0, "end").count("\n"))))
        self.comment.grid(row=row, column=1, sticky=tk.EW)
        row += 1


        submit_btn = tk.Button(self, text="Submit", command=lambda: self.send_request())
        submit_btn.grid(row=row, column=0, sticky=tk.EW, padx=5, pady=5)

        close_btn = tk.Button(self, text="Close", command=lambda: self.destroy())
        close_btn.grid(row=row, column=1, sticky=tk.EW, padx=5, pady=5)

        self.bind('<Escape>', lambda e: self.destroy())
        self.center()

    def send_request(self):
        if self.author == "" or self.university == "" or self.email == "":
            messagebox.showerror("Error", "Please fill all fields.")
        if "@" not in self.email:
            messagebox.showerror("Error", "Please fill in a valid email address, it will be used for consultation purposes.")
        now = datetime.datetime.now()
        target_branch = self.university.replace(" ","_") + "_" + self.author.replace(" ","_")
        comment = self.comment.get(1.0, tk.END)
        comment += "\n \nEmail for requests: " + self.email
        if GithubHandler.send_pull_request(target_branch, now.strftime("%Y_%m_%d") + "_" + target_branch, comment) == 0:
            messagebox.showinfo("Success", "Changes submitted")
        else:
            messagebox.showerror("Error", "Changes failed to submit")
        self.destroy()

    def destroy(self):
        try:
            ConfigHandler.update_config()
        except Exception as e:
            print(e)
        super().destroy()
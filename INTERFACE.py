import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
from plyer import notification
import pygame
import threading
import time
import requests
import json

# ---------------- DATABASE SETUP ---------------- #

conn = sqlite3.connect("smart_tasks.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks(
id INTEGER PRIMARY KEY AUTOINCREMENT,
title TEXT,
due_date TEXT,
priority TEXT,
status TEXT
)
""")
conn.commit()

# ---------------- INIT ---------------- #

pygame.mixer.init()

root = tk.Tk()
root.title("🚀 Ultimate Smart Task Manager")
root.geometry("1000x650")

theme_mode = "dark"

# ---------------- THEME ---------------- #

def apply_theme():
    if theme_mode == "dark":
        root.configure(bg="#121212")
        title_label.config(bg="#121212", fg="#00ffcc")
    else:
        root.configure(bg="#f5f5f5")
        title_label.config(bg="#f5f5f5", fg="#222")

def toggle_theme():
    global theme_mode
    theme_mode = "light" if theme_mode == "dark" else "dark"
    apply_theme()

# ---------------- AI SORTING ---------------- #

def priority_weight(priority):
    return {"High":3, "Medium":2, "Low":1}[priority]

def urgency_weight(due):
    due_date = datetime.strptime(due, "%m/%d/%y")
    days = (due_date - datetime.now()).days
    return max(0, 5 - days)

def ai_sort():
    cursor.execute("SELECT * FROM tasks")
    rows = cursor.fetchall()
    scored = []

    for r in rows:
        score = priority_weight(r[3]) + urgency_weight(r[2])
        scored.append((score, r))

    scored.sort(reverse=True)
    refresh_tree([r[1] for r in scored])

# ---------------- TASK FUNCTIONS ---------------- #

def add_task():
    title = task_entry.get()
    due = cal.get()
    priority = priority_combo.get()

    if not title:
        messagebox.showwarning("Warning", "Task required!")
        return

    cursor.execute("INSERT INTO tasks (title,due_date,priority,status) VALUES (?,?,?,?)",
                   (title, due, priority, "Pending"))
    conn.commit()

    slide_animation()
    load_tasks()
    task_entry.delete(0, tk.END)

def complete_task():
    selected = tree.focus()
    if selected:
        cursor.execute("UPDATE tasks SET status='Completed' WHERE id=?", (selected,))
        conn.commit()

        # Sound (optional: add complete.wav in folder)
        # pygame.mixer.music.load("complete.wav")
        # pygame.mixer.music.play()

        notification.notify(
            title="Task Completed 🎉",
            message="Great job!",
            timeout=3
        )

        load_tasks()

def delete_task():
    selected = tree.focus()
    if selected:
        cursor.execute("DELETE FROM tasks WHERE id=?", (selected,))
        conn.commit()
        load_tasks()

def load_tasks():
    cursor.execute("SELECT * FROM tasks")
    rows = cursor.fetchall()
    refresh_tree(rows)

def refresh_tree(rows):
    for i in tree.get_children():
        tree.delete(i)
    for row in rows:
        tree.insert("", "end", iid=row[0], values=row[1:])

# ---------------- SLIDE ANIMATION ---------------- #

def slide_animation():
    for i in range(15):
        root.geometry(f"1000x{650+i}")
        root.update()
        time.sleep(0.01)
    root.geometry("1000x650")

# ---------------- DASHBOARD ---------------- #

def show_dashboard():
    cursor.execute("SELECT status FROM tasks")
    rows = cursor.fetchall()

    completed = sum(1 for r in rows if r[0] == "Completed")
    pending = sum(1 for r in rows if r[0] == "Pending")

    plt.figure()
    plt.bar(["Completed","Pending"], [completed,pending])
    plt.title("Task Overview")
    plt.show()

# ---------------- REMINDER (THREAD SAFE FIX) ---------------- #

def reminder_loop():
    thread_conn = sqlite3.connect("smart_tasks.db")
    thread_cursor = thread_conn.cursor()

    while True:
        thread_cursor.execute("SELECT title,due_date FROM tasks WHERE status='Pending'")
        rows = thread_cursor.fetchall()

        today = datetime.now().strftime("%m/%d/%y")

        for r in rows:
            if r[1] == today:
                notification.notify(
                    title="Reminder 🔔",
                    message=f"Task due today: {r[0]}",
                    timeout=5
                )

        time.sleep(60)

threading.Thread(target=reminder_loop, daemon=True).start()

# ---------------- CLOUD SYNC ---------------- #

def cloud_sync():
    cursor.execute("SELECT * FROM tasks")
    rows = cursor.fetchall()
    data = json.dumps(rows)

    try:
        requests.post("https://httpbin.org/post", data=data)
        messagebox.showinfo("Cloud", "Synced Successfully ☁")
    except:
        messagebox.showerror("Cloud", "Sync Failed")

# ---------------- UI ---------------- #

title_label = tk.Label(root, text="🤖 Smart AI Task Manager",
                       font=("Arial",22,"bold"))
title_label.pack(pady=15)

input_frame = tk.Frame(root)
input_frame.pack()

task_entry = tk.Entry(input_frame, width=25)
task_entry.grid(row=0,column=0,padx=10)

cal = DateEntry(input_frame)
cal.grid(row=0,column=1,padx=10)

priority_combo = ttk.Combobox(input_frame, values=["Low","Medium","High"])
priority_combo.set("Medium")
priority_combo.grid(row=0,column=2,padx=10)

tk.Button(input_frame, text="Add", command=add_task).grid(row=0,column=3,padx=10)

columns = ("Title","Due Date","Priority","Status")
tree = ttk.Treeview(root, columns=columns, show="headings")
for col in columns:
    tree.heading(col, text=col)
tree.pack(pady=20)

btn_frame = tk.Frame(root)
btn_frame.pack()

tk.Button(btn_frame, text="Complete 🎵", command=complete_task).grid(row=0,column=0,padx=10)
tk.Button(btn_frame, text="Delete", command=delete_task).grid(row=0,column=1,padx=10)
tk.Button(btn_frame, text="AI Sort 🤖", command=ai_sort).grid(row=0,column=2,padx=10)
tk.Button(btn_frame, text="Dashboard 📊", command=show_dashboard).grid(row=0,column=3,padx=10)
tk.Button(btn_frame, text="Theme 🌙", command=toggle_theme).grid(row=0,column=4,padx=10)
tk.Button(btn_frame, text="Cloud Sync ☁", command=cloud_sync).grid(row=0,column=5,padx=10)

apply_theme()
load_tasks()

root.mainloop()
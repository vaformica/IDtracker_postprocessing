#!/usr/bin/env python3
"""Mac GUI for finding, editing, submitting, and tracking Firebird IDtracker TOMLs."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import queue
import shlex
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from idtracker_toml_manager import (
    DEFAULT_GROUPTRIAL_ROOT,
    DEFAULT_IDTRACKER_ENV,
    DEFAULT_RUN_ROOT,
    REMOTE_TOML_INVENTORY,
    common_fields,
    safe_label,
    sha256_text,
    submission_command,
    update_common_fields,
    validate_six_beetle_toml,
)
from six_beetle_firebird_gui import DEFAULT_SSH_HOST, DEFAULT_SSH_KEY, SSH, expand_remote


BASE = Path(__file__).resolve().parent
RUNNER = BASE / "firebird_idtracker_runner.py"

REMOTE_RUN_DISCOVERY = r'''
import json,sys
from pathlib import Path
root=Path(json.load(sys.stdin)["root"]).expanduser()
records=[]
if root.is_dir():
    for folder in root.iterdir():
        if not folder.is_dir():continue
        receipt=folder/"submission_receipt.json"
        request=folder/"submission_request.json"
        if not receipt.is_file() and not request.is_file():continue
        try:data=json.loads((receipt if receipt.is_file() else request).read_text())
        except Exception:continue
        status_path=folder/"status.json"
        try:state=json.loads(status_path.read_text()) if status_path.is_file() else {}
        except Exception as exc:state={"stage":"STATUS_ERROR","error":repr(exc)}
        stage=state.get("stage","SUBMITTED")
        log=folder/"idtracker.log"
        log_text=log.read_text(errors="replace") if log.is_file() else ""
        trajectories=list(folder.glob("idtracker_output/**/trajectories/trajectories.npy"))
        if stage == "FAILED":
            if trajectories and "Success" in log_text:
                stage="OUTPUT_READY_WITH_EXIT_WARNING"
            elif "uncorrectable ECC error" in log_text:
                stage="FAILED_GPU_ECC"
            elif "Not a homogeneous array" in log_text:
                stage="FAILED_TOML"
        elif stage == "COMPLETE_UNREVIEWED" and not trajectories:
            stage="FAILED_GPU_ECC" if "uncorrectable ECC error" in log_text else "FAILED_NO_TRAJECTORY"
        records.append({**data,"job_id":data.get("job_id") or state.get("slurm_job_id"),
                        "run_dir":str(folder),"stage":stage,"status_utc":state.get("utc",""),
                        "error":state.get("error", ""),"trajectory_found":bool(trajectories)})
records.sort(key=lambda row:row.get("submitted_utc",""),reverse=True)
json.dump(records,sys.stdout)
'''


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Firebird IDtracker.ai TOML manager")
        self.geometry("1440x920")
        self.minsize(1100, 760)
        self.events: queue.Queue = queue.Queue()
        self.records: list[dict] = []
        self.visible_records: list[dict] = []
        self.record_by_path: dict[str, dict] = {}
        self.source_text: dict[str, str] = {}
        self.staged_text: dict[str, str] = {}
        self.jobs: list[dict] = []
        self.current_path = ""
        self.loading_editor = False
        self._build()
        self.after(100, self._poll)

    def _style(self):
        self.configure(background="#F2F3F5")
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure(".", background="#F2F3F5", foreground="#15181B")
        style.configure("TLabel", background="#F2F3F5", foreground="#15181B")
        style.configure("TLabelframe", background="#F2F3F5")
        style.configure("TLabelframe.Label", background="#F2F3F5", foreground="#15181B")
        style.configure("TEntry", fieldbackground="#FFFFFF", foreground="#15181B")
        style.configure("Treeview", background="#FFFFFF", fieldbackground="#FFFFFF", foreground="#15181B")
        style.configure("Treeview.Heading", background="#E4E7EB", foreground="#15181B")
        style.map("Treeview", background=[("selected", "#2E6EA6")], foreground=[("selected", "#FFFFFF")])

    def _build(self):
        self._style()
        connection = ttk.LabelFrame(self, text="Firebird connection and managed submission location")
        connection.pack(fill="x", padx=10, pady=8)
        self.host = tk.StringVar(value=DEFAULT_SSH_HOST)
        self.key = tk.StringVar(value=DEFAULT_SSH_KEY)
        self.search_roots = tk.StringVar(value=DEFAULT_GROUPTRIAL_ROOT)
        self.run_root = tk.StringVar(value=DEFAULT_RUN_ROOT)
        self.environment = tk.StringVar(value=DEFAULT_IDTRACKER_ENV)
        fields = [
            ("SSH host", self.host), ("SSH key", self.key),
            ("TOML search roots (; separated)", self.search_roots),
            ("Managed run root", self.run_root), ("IDtracker environment", self.environment),
        ]
        for row, (label, variable) in enumerate(fields):
            ttk.Label(connection, text=label).grid(row=row, column=0, sticky="w", padx=6, pady=2)
            ttk.Entry(connection, textvariable=variable).grid(row=row, column=1, sticky="ew", padx=6, pady=2)
        connection.columnconfigure(1, weight=1)
        ttk.Button(connection, text="Test SSH", command=self.test_ssh).grid(row=0, column=2, padx=6)
        ttk.Button(connection, text="Search TOMLs", command=self.search).grid(row=2, column=2, padx=6)
        ttk.Button(connection, text="Load managed runs", command=self.load_runs).grid(row=3, column=2, padx=6)

        filter_row = ttk.Frame(self)
        filter_row.pack(fill="x", padx=10, pady=(0, 4))
        ttk.Label(filter_row, text="Show").pack(side="left")
        self.filter_mode = tk.StringVar(value="Eligible originals")
        filter_box = ttk.Combobox(
            filter_row, textvariable=self.filter_mode, state="readonly", width=24,
            values=("Eligible originals", "All eligible", "All TOMLs", "Invalid or incomplete"),
        )
        filter_box.pack(side="left", padx=6)
        filter_box.bind("<<ComboboxSelected>>", lambda _event: self.apply_filter())
        self.summary = tk.StringVar(value="Search Firebird to inventory TOMLs.")
        ttk.Label(filter_row, textvariable=self.summary).pack(side="left", padx=12)

        pane = ttk.Panedwindow(self, orient="horizontal")
        pane.pack(fill="both", expand=True, padx=10, pady=4)
        left = ttk.LabelFrame(pane, text="TOMLs (Command-click for multiple submissions)")
        right = ttk.LabelFrame(pane, text="Selected TOML")
        pane.add(left, weight=3)
        pane.add(right, weight=2)

        columns = ("kind", "animals", "rois", "intensity", "area", "bkg", "interval", "video", "edited")
        self.tree = ttk.Treeview(left, columns=columns, show="tree headings", selectmode="extended")
        self.tree.heading("#0", text="File")
        widths = {"kind":90,"animals":60,"rois":45,"intensity":85,"area":90,"bkg":50,"interval":120,"video":60,"edited":55}
        for name in columns:
            self.tree.heading(name, text=name.title())
            self.tree.column(name, width=widths[name], stretch=False)
        self.tree.column("#0", width=390, stretch=True)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.bind("<<TreeviewSelect>>", self.select_toml)

        details = ttk.Notebook(right)
        details.pack(fill="both", expand=True)
        common = ttk.Frame(details)
        raw = ttk.Frame(details)
        details.add(common, text="Common inputs")
        details.add(raw, text="Raw TOML (all inputs)")

        self.fields = {name: tk.StringVar() for name in (
            "path", "name", "videos", "intensity_min", "intensity_max", "area_min", "area_max",
            "start", "end", "animals", "roi_count", "sha256",
        )}
        self.use_bkg = tk.BooleanVar(value=True)
        common_rows = [
            ("Firebird path", "path"), ("Session name", "name"), ("Video paths (; separated)", "videos"),
            ("Intensity minimum", "intensity_min"), ("Intensity maximum", "intensity_max"),
            ("Blob area minimum", "area_min"), ("Blob area maximum", "area_max"),
            ("Start frame", "start"), ("End frame inclusive", "end"),
            ("Number of animals", "animals"), ("ROI count", "roi_count"), ("Source SHA-256", "sha256"),
        ]
        for row, (label, key) in enumerate(common_rows):
            ttk.Label(common, text=label).grid(row=row, column=0, sticky="w", padx=6, pady=3)
            entry = ttk.Entry(common, textvariable=self.fields[key])
            if key in {"path", "roi_count", "sha256"}:
                entry.configure(state="readonly")
            entry.grid(row=row, column=1, sticky="ew", padx=6, pady=3)
        ttk.Checkbutton(common, text="Use background subtraction", variable=self.use_bkg).grid(row=len(common_rows), column=1, sticky="w", padx=6, pady=3)
        ttk.Button(common, text="Apply common inputs to raw TOML", command=self.apply_common).grid(row=len(common_rows)+1, column=1, sticky="w", padx=6, pady=8)
        common.columnconfigure(1, weight=1)

        self.raw = tk.Text(raw, wrap="none", background="#FFFFFF", foreground="#15181B", insertbackground="#15181B", undo=True)
        self.raw.grid(row=0, column=0, sticky="nsew")
        raw_y = ttk.Scrollbar(raw, orient="vertical", command=self.raw.yview)
        raw_y.grid(row=0, column=1, sticky="ns")
        raw_x = ttk.Scrollbar(raw, orient="horizontal", command=self.raw.xview)
        raw_x.grid(row=1, column=0, sticky="ew")
        self.raw.configure(yscrollcommand=raw_y.set, xscrollcommand=raw_x.set)
        raw.columnconfigure(0, weight=1); raw.rowconfigure(0, weight=1)

        editor_actions = ttk.Frame(right)
        editor_actions.pack(fill="x", pady=5)
        ttk.Button(editor_actions, text="Validate and stage", command=self.validate_stage).pack(side="left", padx=3)
        ttk.Button(editor_actions, text="Revert from Firebird", command=self.revert_current).pack(side="left", padx=3)
        ttk.Button(editor_actions, text="Preview selected", command=self.preview_selected).pack(side="left", padx=3)
        ttk.Button(editor_actions, text="Submit selected to IDtracker.ai", command=self.submit_selected).pack(side="left", padx=3)

        jobs_frame = ttk.LabelFrame(self, text="Managed IDtracker.ai jobs")
        jobs_frame.pack(fill="x", padx=10, pady=5)
        job_columns = ("job_id", "status", "submitted", "source", "run_dir")
        self.job_tree = ttk.Treeview(jobs_frame, columns=job_columns, show="headings", height=5, selectmode="extended")
        for name, width in [("job_id",90),("status",160),("submitted",170),("source",260),("run_dir",560)]:
            self.job_tree.heading(name, text=name.replace("_", " ").title())
            self.job_tree.column(name, width=width, stretch=name=="run_dir")
        self.job_tree.pack(side="left", fill="x", expand=True)
        job_buttons = ttk.Frame(jobs_frame)
        job_buttons.pack(side="right", fill="y", padx=5)
        ttk.Button(job_buttons, text="Refresh selected", command=self.refresh_jobs).pack(fill="x", pady=2)
        ttk.Button(job_buttons, text="Show run details", command=self.show_job).pack(fill="x", pady=2)
        ttk.Button(job_buttons, text="Open post-processing GUI", command=self.open_postprocessor).pack(fill="x", pady=2)

        self.log_box = tk.Text(self, height=8, wrap="word", background="#FFFFFF", foreground="#15181B", insertbackground="#15181B")
        self.log_box.pack(fill="both", padx=10, pady=(0, 10))
        self.log("Searches and TOML reads are read-only. Submission never overwrites a source TOML: each job gets an immutable copy, hashes, receipt, status file, Slurm log, and separate output folder.")

    def ssh(self) -> SSH:
        return SSH(self.host.get(), self.key.get())

    def log(self, message):
        self.log_box.insert("end", str(message).rstrip() + "\n")
        self.log_box.see("end")

    def background(self, name, function):
        def worker():
            try:
                self.events.put((name, function(), None))
            except Exception as exc:
                self.events.put((name, None, exc))
        threading.Thread(target=worker, daemon=True).start()

    def _poll(self):
        try:
            while True:
                name, value, error = self.events.get_nowait()
                if error:
                    self.log(f"ERROR: {error}")
                    messagebox.showerror("Firebird TOML manager", str(error))
                elif name == "ssh":
                    self.log(f"Connected to {value}")
                elif name == "inventory":
                    self._show_inventory(value)
                elif name == "toml":
                    self._show_toml(*value)
                elif name == "runs":
                    self._show_runs(value)
                elif name == "submitted":
                    self._show_runs(value, prepend=True)
                    self.log("Submitted jobs:\n" + "\n".join(f"  {x['job_id']}  {x['run_dir']}" for x in value))
                elif name == "job_status":
                    self._update_job_status(value)
        except queue.Empty:
            pass
        self.after(100, self._poll)

    def test_ssh(self):
        self.log("Testing SSH…")
        self.background("ssh", lambda: self.ssh().run("hostname").strip())

    def search(self):
        roots = [x.strip() for x in self.search_roots.get().split(";") if x.strip()]
        if not roots:
            messagebox.showerror("Search TOMLs", "Enter at least one Firebird folder")
            return
        self.log("Searching Firebird recursively and parsing TOMLs…")
        def task():
            ssh = self.ssh()
            home = ssh.run('printf "%s" "$HOME"').strip()
            env = expand_remote(self.environment.get(), home)
            command = f"{shlex.quote(env + '/bin/python')} -c {shlex.quote(REMOTE_TOML_INVENTORY)}"
            return json.loads(ssh.run(command, json.dumps({"roots": roots}), timeout=1800))
        self.background("inventory", task)

    def _show_inventory(self, records):
        self.records = records
        self.record_by_path = {x["path"]: x for x in records}
        self.apply_filter()
        total = len(records); eligible = sum(bool(x.get("eligible")) for x in records)
        originals = sum(bool(x.get("eligible")) and x.get("kind") == "original" for x in records)
        invalid = sum(bool(x.get("error")) for x in records)
        self.summary.set(f"{total} TOMLs; {eligible} are 6-beetle/4-ROI; {originals} eligible originals; {invalid} invalid")
        self.log(self.summary.get())

    def apply_filter(self):
        mode = self.filter_mode.get()
        if mode == "Eligible originals":
            visible = [x for x in self.records if x.get("eligible") and x.get("kind") == "original"]
        elif mode == "All eligible":
            visible = [x for x in self.records if x.get("eligible")]
        elif mode == "Invalid or incomplete":
            visible = [x for x in self.records if not x.get("eligible")]
        else:
            visible = list(self.records)
        self.visible_records = visible
        self.tree.delete(*self.tree.get_children())
        for index, row in enumerate(visible):
            interval = self._compact(row.get("intervals"))
            values = (
                row.get("kind"), row.get("animals"), row.get("roi_count"), self._compact(row.get("intensity")),
                self._compact(row.get("area")), row.get("use_bkg"), interval,
                "yes" if row.get("video_exists") else "NO", "yes" if row["path"] in self.staged_text else "",
            )
            self.tree.insert("", "end", iid=str(index), text=row.get("relative") or row["path"], values=values)

    @staticmethod
    def _compact(value):
        return json.dumps(value, allow_nan=True, separators=(",", ":")) if value is not None else ""

    def selected_records(self) -> list[dict]:
        return [self.visible_records[int(i)] for i in self.tree.selection()]

    def _capture_current(self):
        if not self.current_path or self.loading_editor:
            return
        text = self.raw.get("1.0", "end-1c")
        if text and text != self.source_text.get(self.current_path, ""):
            self.staged_text[self.current_path] = text

    def select_toml(self, _event=None):
        selected = self.selected_records()
        if not selected:
            return
        self._capture_current()
        row = selected[0]
        path = row["path"]
        if path in self.staged_text:
            self._show_toml(path, self.staged_text[path], row)
        elif path in self.source_text:
            self._show_toml(path, self.source_text[path], row)
        else:
            self.log(f"Reading {path}")
            self.background("toml", lambda: (path, self.ssh().run("cat -- " + shlex.quote(path)), row))

    def _show_toml(self, path, text, row):
        if path not in self.source_text:
            self.source_text[path] = text
        self.current_path = path
        self.loading_editor = True
        try:
            self.raw.delete("1.0", "end"); self.raw.insert("1.0", text)
            fields = common_fields(text)
            values = {
                "path": path, "name": fields["name"], "videos": ";".join(fields["video_paths"]),
                "intensity_min": fields["intensity_min"], "intensity_max": fields["intensity_max"],
                "area_min": fields["area_min"], "area_max": fields["area_max"],
                "start": fields["start"], "end": fields["end"], "animals": fields["animals"],
                "roi_count": fields["roi_count"], "sha256": row.get("sha256", ""),
            }
            for key, value in values.items():
                self.fields[key].set(str(value))
            self.use_bkg.set(fields["use_bkg"])
        finally:
            self.loading_editor = False

    def apply_common(self):
        if not self.current_path:
            messagebox.showinfo("Editor", "Select a TOML first")
            return
        try:
            current = self.raw.get("1.0", "end-1c")
            changed = update_common_fields(current, {
                "name": self.fields["name"].get(),
                "video_paths": [x.strip() for x in self.fields["videos"].get().split(";") if x.strip()],
                "intensity_min": self.fields["intensity_min"].get(), "intensity_max": self.fields["intensity_max"].get(),
                "area_min": self.fields["area_min"].get(), "area_max": self.fields["area_max"].get(),
                "start": self.fields["start"].get(), "end": self.fields["end"].get(),
                "animals": self.fields["animals"].get(), "use_bkg": self.use_bkg.get(),
            })
            self.raw.delete("1.0", "end"); self.raw.insert("1.0", changed)
            self.staged_text[self.current_path] = changed
            self.log("Applied common inputs and staged a validated in-memory copy. The source TOML on Firebird is unchanged.")
            self.apply_filter()
        except Exception as exc:
            messagebox.showerror("Invalid TOML inputs", str(exc))

    def validate_stage(self):
        if not self.current_path:
            messagebox.showinfo("Editor", "Select a TOML first")
            return
        try:
            text = self.raw.get("1.0", "end-1c")
            data = validate_six_beetle_toml(text)
            self.staged_text[self.current_path] = text
            self.log(f"Validated and staged {self.current_path}\nSHA-256: {sha256_text(text)}\nName: {data.get('name')}")
            self.apply_filter()
        except Exception as exc:
            messagebox.showerror("TOML validation failed", str(exc))

    def revert_current(self):
        if not self.current_path:
            return
        path = self.current_path
        self.staged_text.pop(path, None); self.source_text.pop(path, None)
        row = self.record_by_path[path]
        self.background("toml", lambda: (path, self.ssh().run("cat -- " + shlex.quote(path)), row))
        self.apply_filter()

    def _content_for(self, ssh: SSH, row: dict) -> str:
        path = row["path"]
        if path in self.staged_text:
            return self.staged_text[path]
        if path in self.source_text:
            return self.source_text[path]
        text = ssh.run("cat -- " + shlex.quote(path))
        self.source_text[path] = text
        return text

    def preview_selected(self):
        selected = self.selected_records()
        if not selected:
            messagebox.showinfo("Preview", "Select one or more TOMLs")
            return
        self._capture_current()
        lines = []
        for row in selected:
            mark = "edited" if row["path"] in self.staged_text else "unchanged"
            lines.append(f"{row['relative']}  [{mark}; animals={row.get('animals')}; ROIs={row.get('roi_count')}; video={'found' if row.get('video_exists') else 'MISSING'}]")
        messagebox.showinfo("Submission preview", "No jobs submitted.\n\n" + "\n".join(lines))

    def submit_selected(self):
        selected = self.selected_records()
        if not selected:
            messagebox.showinfo("Submit", "Select one or more TOMLs")
            return
        self._capture_current()
        for row in selected:
            if not row.get("eligible"):
                messagebox.showerror("Submit", f"Not a six-beetle/four-ROI TOML:\n{row['path']}")
                return
        names = "\n".join("• " + row["relative"] for row in selected[:12])
        if len(selected) > 12:
            names += f"\n• …and {len(selected)-12} more"
        if not messagebox.askyesno(
            "Submit IDtracker.ai jobs",
            f"Submit {len(selected)} GPU job(s)? Each source TOML will remain unchanged.\n\n{names}",
        ):
            return
        self.log(f"Preparing {len(selected)} immutable IDtracker.ai submission(s)…")
        self.background("submitted", lambda: self._submit_records(selected))

    def _submit_records(self, records: list[dict]) -> list[dict]:
        ssh = self.ssh()
        home = ssh.run('printf "%s" "$HOME"').strip()
        run_root = expand_remote(self.run_root.get(), home).rstrip("/")
        environment = expand_remote(self.environment.get(), home).rstrip("/")
        ssh.run("test -x " + shlex.quote(environment + "/bin/idtrackerai"))
        submitted = []
        for index, row in enumerate(records):
            text = self._content_for(ssh, row)
            data = validate_six_beetle_toml(text)
            missing_videos = [
                path for path in data["video_paths"]
                if ssh.run("test -f " + shlex.quote(path) + " && printf yes || true").strip() != "yes"
            ]
            if missing_videos:
                raise FileNotFoundError(
                    f"Referenced video path(s) do not exist for {row['path']}: " + ", ".join(missing_videos)
                )
            timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            label = safe_label(str(data.get("name") or Path(row["path"]).stem))
            run_dir = f"{run_root}/{timestamp}_{index:03d}_{label}"
            remote_toml = f"{run_dir}/input/submitted.toml"
            remote_runner = f"{run_dir}/firebird_idtracker_runner.py"
            remote_output = f"{run_dir}/idtracker_output"
            ssh.run("mkdir -p " + shlex.quote(run_dir + "/input"))
            with tempfile.TemporaryDirectory(prefix="idtracker-toml-") as folder:
                local = Path(folder)
                toml_path = local / "submitted.toml"; toml_path.write_text(text)
                ssh.upload(toml_path, remote_toml)
                ssh.upload(RUNNER, remote_runner)
                command = submission_command(environment, remote_runner, remote_toml, remote_output)
                source_text = self.source_text.get(row["path"], text)
                request = {
                    "schema_version": 1, "source_toml": row["path"], "source_sha256": row.get("sha256"),
                    "submitted_toml_sha256": sha256_text(text), "modified": text != source_text,
                    "submitted_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "run_dir": run_dir,
                    "idtracker_environment": environment, "command": command,
                    "slurm": {"partition":"gpu","gres":"gpu:l40s:1","cpus":16,"memory":"64G","time":"08:00:00"},
                }
                request_path = local / "submission_request.json"
                request_path.write_text(json.dumps(request, indent=2, sort_keys=True) + "\n")
                ssh.upload(request_path, f"{run_dir}/submission_request.json")
                hashes = ssh.run("sha256sum " + shlex.quote(remote_toml) + " " + shlex.quote(remote_runner))
                observed = {line.split()[1]: line.split()[0] for line in hashes.splitlines() if len(line.split()) >= 2}
                if observed.get(remote_toml) != request["submitted_toml_sha256"]:
                    raise RuntimeError(f"Uploaded TOML hash mismatch in {run_dir}")
                wrapped = (
                    "export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1; "
                    f"export MPLCONFIGDIR={shlex.quote(run_dir + '/matplotlib_cache')}; "
                    "export PYTHONUNBUFFERED=1; exec " + shlex.join(command)
                )
                submit = [
                    "sbatch", "--parsable", f"--job-name=idta_{label[:40]}", "--partition=gpu",
                    "--gres=gpu:l40s:1", "--nodes=1", "--cpus-per-task=16", "--mem=64G", "--time=08:00:00",
                    f"--chdir={run_dir}", f"--output={run_dir}/slurm-%j.log", "--wrap", wrapped,
                ]
                job_id = ssh.run(shlex.join(submit), timeout=120).strip().split(";", 1)[0]
                receipt = {**request, "job_id": job_id, "stage": "SUBMITTED"}
                receipt_path = local / "submission_receipt.json"
                receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
                ssh.upload(receipt_path, f"{run_dir}/submission_receipt.json")
            submitted.append(receipt)
        return submitted

    def load_runs(self):
        self.log("Loading managed run receipts and status files…")
        def task():
            ssh = self.ssh(); home = ssh.run('printf "%s" "$HOME"').strip()
            root = expand_remote(self.run_root.get(), home)
            env = expand_remote(self.environment.get(), home)
            command = f"{shlex.quote(env + '/bin/python')} -c {shlex.quote(REMOTE_RUN_DISCOVERY)}"
            return json.loads(ssh.run(command, json.dumps({"root": root})))
        self.background("runs", task)

    def _show_runs(self, records, prepend=False):
        if prepend:
            known = {x.get("run_dir") for x in self.jobs}
            self.jobs = [x for x in records if x.get("run_dir") not in known] + self.jobs
        else:
            self.jobs = records
        self.job_tree.delete(*self.job_tree.get_children())
        for index, row in enumerate(self.jobs):
            source = Path(row.get("source_toml", "")).name
            self.job_tree.insert("", "end", iid=str(index), values=(
                row.get("job_id", ""), row.get("stage", "SUBMITTED"), row.get("submitted_utc", ""), source, row.get("run_dir", ""),
            ))
        self.log(f"Loaded {len(self.jobs)} managed job receipt(s).")

    def refresh_jobs(self):
        choices = list(self.job_tree.selection())
        if not choices:
            choices = list(self.job_tree.get_children())
        if not choices:
            messagebox.showinfo("Jobs", "No managed jobs loaded")
            return
        indexes = [int(x) for x in choices]
        def task():
            ssh = self.ssh()
            home = ssh.run('printf "%s" "$HOME"').strip()
            root = expand_remote(self.run_root.get(), home)
            env = expand_remote(self.environment.get(), home)
            command = f"{shlex.quote(env + '/bin/python')} -c {shlex.quote(REMOTE_RUN_DISCOVERY)}"
            current = {row["run_dir"]:row for row in json.loads(ssh.run(command,json.dumps({"root":root})))}
            queue_rows = ssh.run("squeue -h -u \"$USER\" -o '%i|%T|%M|%R'").splitlines()
            queue_state = {parts[0]: " | ".join(parts[1:]) for line in queue_rows
                           if len(parts := line.split("|", 3)) == 4}
            result=[]
            for index in indexes:
                job=self.jobs[index]
                updated=current.get(job["run_dir"])
                job_id=str((updated or job).get("job_id", ""))
                stage=queue_state.get(job_id) or (updated["stage"] if updated else "RUN_NOT_FOUND")
                result.append((index,stage))
            return result
        self.background("job_status", task)

    def _update_job_status(self, updates):
        for index, stage in updates:
            self.jobs[index]["stage"] = stage
            if self.job_tree.exists(str(index)):
                values = list(self.job_tree.item(str(index), "values")); values[1] = stage
                self.job_tree.item(str(index), values=values)
            self.log(f"Job {self.jobs[index].get('job_id')}: {stage}")

    def show_job(self):
        chosen = self.job_tree.selection()
        if not chosen:
            return
        job = self.jobs[int(chosen[0])]
        messagebox.showinfo("Managed run", json.dumps(job, indent=2, sort_keys=True))

    def open_postprocessor(self):
        """Open the existing six-beetle processor after tracking completes."""
        subprocess.Popen([sys.executable, str(BASE / "six_beetle_firebird_gui.py")], cwd=BASE)
        self.log(
            "Opened the six-beetle post-processing GUI. Click 'Find six-beetle sessions'; "
            "the managed IDtracker run folder is included in its default search roots."
        )


def main():
    App().mainloop()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Local GUI for finding Firebird sessions and running shared group processing."""

from __future__ import annotations

import hashlib
import json
import math
import queue
import shlex
import subprocess
import threading
from datetime import datetime
from pathlib import Path, PurePosixPath
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


BASE = Path(__file__).resolve().parent
DEFAULT_SSH_HOST = "firebird"
DEFAULT_SSH_KEY = "~/.ssh/id_ed25519_firebird"
DEFAULT_SESSION_ROOTS = ";".join((
    "/data/labs/vformic1-swat-lab/2024_Videos/Groupagetrial_2024/managed_idtracker_runs",
    "/data/labs/vformic1-swat-lab/2024_Videos",
    "/data/labs/vformic1-swat-lab/2026_Videos/2026_Fights/2026_Fights_Recorded",
    "/data/labs/vformic1-swat-lab/idtracker_pipeline_runs",
))
DEPLOY_FILES = (
    "processor.py",
    "six_beetle_processor.py",
    "dyadic_processor.py",
    "frame_data.py",
    "group_processor.py",
    "persistent_groups.py",
    "trajectory_reconstruction.py",
    "export_blob_evidence.py",
    "build_canonical_review.py",
    "review_geometry.py",
    "interaction_review_template.html",
    "review_editor.js",
    "apply_review_decisions.py",
    "run_six_beetle_pipeline.py",
    "output_manifest.py",
    "run_group_pipeline.py",
)

REMOTE_DISCOVERY = r"""
import json,math,sys
from pathlib import Path

names=("validated.npy","without_gaps.npy","trajectories_wo_gaps.npy","trajectories_without_gaps.npy","trajectories.npy","trajectories.h5","trajectories.csv")
interval_keys={"tracking_intervals","tracking_interval","intervals_to_track","analysis_interval","analysis_intervals"}

def extract_pairs(value, trail):
    output=[]
    if isinstance(value,list):
        if len(value)>=2 and all(isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x) for x in value[:2]):
            output.append([int(value[0]),int(value[1]),trail])
        else:
            for index,child in enumerate(value):output.extend(extract_pairs(child,f"{trail}[{index}]") )
    return output

def intervals(value, trail=""):
    output=[]
    if isinstance(value,dict):
        for key,child in value.items():
            name=str(key).lower()
            if name in interval_keys:
                output.extend(extract_pairs(child,trail+"."+str(key)))
            elif isinstance(child,(dict,list)):
                output.extend(intervals(child,trail+"."+str(key)))
    elif isinstance(value,list):
        for index,child in enumerate(value):
            if isinstance(child,(dict,list)):output.extend(intervals(child,f"{trail}[{index}]") )
    return output

request=json.load(sys.stdin)
roots=request if isinstance(request,list) else request['roots']
profile='six' if isinstance(request,list) else request.get('profile','all')
records=[]
seen=set()
for root_text in roots:
    root=Path(root_text).expanduser()
    if not root.is_dir():continue
    for session_json in root.rglob("session.json"):
        session=session_json.parent
        if str(session) in seen:continue
        seen.add(str(session))
        try:data=json.loads(session_json.read_text())
        except Exception:continue
        animal_count=data.get("number_of_animals")
        rois=data.get("roi_list")
        if not isinstance(animal_count,int) or animal_count<2 or not isinstance(rois,list) or len(rois)<2:continue
        if profile=='six' and (animal_count!=6 or len(rois)!=4):continue
        if profile=='dyadic' and animal_count!=2:continue
        trajectory=""
        for name in names:
            candidates=[]
            for path in (session/name,session/"trajectories"/name):
                if path.is_file():candidates.append(path)
            if not candidates:candidates=list(session.rglob(name))
            candidates=sorted(set(candidates))
            if len(candidates)==1:
                trajectory=str(candidates[0]);break
        videos=data.get("video_paths") or data.get("videos") or []
        if isinstance(videos,str):videos=[videos]
        video=str(videos[0]) if videos else ""
        pairs=intervals(data)
        start,end=(pairs[0][:2] if pairs else (0,0))
        records.append(dict(session=str(session),trajectory=trajectory,video=video,start=start,end=end,
            animal_count=animal_count,roi_count=len(rois),
            label=session.name,blob_evidence=(session/"blob_evidence.json").is_file(),
            blob_source=(session/"preprocessing/list_of_blobs.pickle").is_file()))
records.sort(key=lambda row:row["session"],reverse=True)
json.dump(records[:1000],sys.stdout)
"""

REMOTE_ARCHIVE = r"""
import sys,zipfile
from pathlib import Path
root=Path(sys.argv[1]);destination=Path(sys.argv[2])
if not root.is_dir():raise RuntimeError(f"Missing run folder: {root}")
if destination.exists():raise FileExistsError(destination)
partial=destination.with_name(destination.name+".partial")
try:
    with zipfile.ZipFile(partial,"w",compression=zipfile.ZIP_STORED,allowZip64=True) as archive:
        for path in sorted(root.rglob("*")):
            if path.is_file():archive.write(path,path.relative_to(root.parent))
    partial.replace(destination)
except Exception:
    partial.unlink(missing_ok=True);raise
print(destination)
"""


class SSH:
    def __init__(self, host: str, key: str):
        self.host = host.strip()
        self.key = str(Path(key).expanduser()) if key.strip() else ""

    def _options(self):
        options = ["-o", "BatchMode=yes", "-o", "ConnectTimeout=20"]
        if self.key:
            options += ["-o", "IdentitiesOnly=yes", "-i", self.key]
        return options

    def run(self, command: str, input_text: str | None = None, timeout: int = 900) -> str:
        invocation = ["ssh", *self._options(), self.host, "bash", "-lc", shlex.quote(command)]
        result = subprocess.run(invocation, input=input_text, text=True, capture_output=True, timeout=timeout)
        if result.returncode:
            raise RuntimeError(connection_error(result.stderr.strip() or result.stdout.strip(), self.host))
        return result.stdout

    def upload(self, local: Path, remote: str, timeout: int = 900):
        invocation = ["scp", *self._options(), str(local), f"{self.host}:{remote}"]
        result = subprocess.run(invocation, text=True, capture_output=True, timeout=timeout)
        if result.returncode:
            raise RuntimeError(connection_error(result.stderr.strip() or result.stdout.strip(), self.host))

    def download(self, remote: str, local: Path, timeout: int = 3600):
        invocation = ["scp", *self._options(), f"{self.host}:{remote}", str(local)]
        result = subprocess.run(invocation, text=True, capture_output=True, timeout=timeout)
        if result.returncode:
            raise RuntimeError(connection_error(result.stderr.strip() or result.stdout.strip(), self.host))


def connection_error(message: str, host: str) -> str:
    """Add the actionable local prerequisite to Firebird network failures."""
    lowered = message.lower()
    network_failure = any(
        phrase in lowered
        for phrase in (
            "could not resolve hostname",
            "operation timed out",
            "connection timed out",
            "no route to host",
        )
    )
    if network_failure and host.strip() == DEFAULT_SSH_HOST:
        return (
            f"{message}\n\n"
            "The GUI is using the established SSH alias 'firebird' from "
            "~/.ssh/config. Connect Cisco Secure Client to the Swarthmore VPN "
            "and retry Test SSH."
        )
    return message


def expand_remote(path: str, home: str) -> str:
    value = path.strip()
    if value == "~":
        return home
    if value.startswith("~/"):
        return home.rstrip("/") + "/" + value[2:]
    return value


def code_digest() -> str:
    digest = hashlib.sha256()
    for name in DEPLOY_FILES:
        path = BASE / name
        digest.update(name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def validated_parameters(values: dict) -> dict:
    parsed = dict(values)
    for key in ("start", "end"):
        parsed[key] = int(values[key])
    for key, default in (("split_confirmation", 3), ("gap_frames", 30), ("distant_confirmation", 10)):
        parsed[key] = int(values.get(key, default))
    for key in ("fps", "movement", "wall", "fungus", "proximity", "jump", "reconstruction"):
        parsed[key] = float(values[key])
    for key, default in (("gap_speed", 20), ("gap_cap", 300)):
        parsed[key] = float(values.get(key, default))
    if not all(math.isfinite(parsed[key]) for key in
               ("fps", "movement", "wall", "fungus", "proximity", "jump", "reconstruction", "gap_speed", "gap_cap")):
        raise ValueError('All numeric settings must be finite')
    if parsed["start"] < 0 or parsed["end"] < parsed["start"]:
        raise ValueError("Frame range must have a nonnegative start and end at or after start")
    if parsed["fps"] <= 0 or parsed["movement"] <= 0 or parsed["proximity"] <= 0 or parsed["jump"] <= 0 or parsed["reconstruction"] <= 0:
        raise ValueError("FPS and movement, proximity, jump, and reconstruction thresholds must be positive")
    if parsed["wall"] < 0 or parsed["fungus"] < 0:
        raise ValueError("ROI buffers cannot be negative")
    if (parsed['split_confirmation'] < 1 or parsed['gap_frames'] < 1 or
            parsed['distant_confirmation'] < parsed['split_confirmation'] or
            parsed['gap_speed'] <= 0 or parsed['gap_cap'] < parsed['proximity']):
        raise ValueError('Persistent-group gap and split settings are invalid')
    for key in ("session", "video", "label"):
        if not str(parsed[key]).strip():
            raise ValueError(f"{key} cannot be blank")
    return parsed


def pipeline_command(code_dir: str, run_dir: str, post_python: str, idtracker_python: str, ffmpeg: str, ffprobe: str, parameters: dict, script_name="run_six_beetle_pipeline.py") -> list[str]:
    pdf_name = parameters["label"].replace("/", "_") + ".pdf"
    command = [
        post_python,
        f"{code_dir}/{script_name}",
        "--session", parameters["session"],
        "--source-video", parameters["video"],
        "--analysis-output", f"{run_dir}/analysis",
        "--review-output", f"{run_dir}/review",
        "--start", str(parameters["start"]),
        "--end", str(parameters["end"]),
        "--fps", str(parameters["fps"]),
        "--label", parameters["label"],
        "--pdf-name", pdf_name,
        "--movement-threshold-px", str(parameters["movement"]),
        "--wall-buffer-px", str(parameters["wall"]),
        "--fungus-buffer-px", str(parameters["fungus"]),
        "--proximity-px", str(parameters["proximity"]),
        "--jump-threshold-px", str(parameters["jump"]),
        "--reconstruction-speed-px", str(parameters["reconstruction"]),
        "--split-confirmation-frames", str(parameters.get('split_confirmation', 3)),
        "--gap-speed-px", str(parameters.get('gap_speed', 20)),
        "--gap-radius-cap-px", str(parameters.get('gap_cap', 300)),
        "--max-reacquire-gap-frames", str(parameters.get('gap_frames', 30)),
        "--distant-confirmation-frames", str(parameters.get('distant_confirmation', 10)),
        "--idtracker-python", idtracker_python,
        "--ffmpeg", ffmpeg,
        "--ffprobe", ffprobe,
    ]
    if parameters.get("trajectory"):
        command += ["--trajectory", parameters["trajectory"]]
    return command


class App(tk.Tk):
    def __init__(self, profile="six"):
        super().__init__()
        self.title("Firebird beetle group analysis")
        self.profile = tk.StringVar(value=profile)
        self.geometry("1180x820")
        self.minsize(960, 700)
        self.events = queue.Queue()
        self.records = []
        self.jobs = []
        self._build()
        self.after(100, self._poll)

    def _build(self):
        # Explicit light colors avoid an all-black Tk window on macOS builds
        # whose ttk theme does not follow the system appearance correctly.
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
        connection = ttk.LabelFrame(self, text="1. Firebird connection and search")
        connection.pack(fill="x", padx=10, pady=8)
        self.host = tk.StringVar(value=DEFAULT_SSH_HOST)
        self.key = tk.StringVar(value=DEFAULT_SSH_KEY)
        self.roots = tk.StringVar(value=DEFAULT_SESSION_ROOTS)
        default_root = "six_beetle_postprocessing" if self.profile.get() == "six" else "group_postprocessing"
        self.output_root = tk.StringVar(value=f"/data/labs/vformic1-swat-lab/{default_root}")
        self.post_python = tk.StringVar(value="/home/vformic1-swat/miniconda3/envs/idtracker_reprocess_v1/bin/python")
        self.idtracker_python = tk.StringVar(value="/home/vformic1-swat/miniconda3/envs/idtrackerai_6_0_14/bin/python")
        self.ffmpeg = tk.StringVar(value="/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffmpeg")
        self.ffprobe = tk.StringVar(value="/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffprobe")
        fields = [
            ("SSH host", self.host), ("SSH key", self.key), ("Search roots (; separated)", self.roots),
            ("Remote output root", self.output_root), ("Post-processing Python", self.post_python),
            ("IDtracker Python", self.idtracker_python), ("ffmpeg", self.ffmpeg), ("ffprobe", self.ffprobe),
        ]
        for row, (label, variable) in enumerate(fields):
            ttk.Label(connection, text=label).grid(row=row, column=0, sticky="w", padx=6, pady=2)
            ttk.Entry(connection, textvariable=variable).grid(row=row, column=1, sticky="ew", padx=6, pady=2)
        connection.columnconfigure(1, weight=1)
        ttk.Button(connection, text="Test SSH", command=self.test_ssh).grid(row=0, column=2, padx=6)
        ttk.Combobox(connection, textvariable=self.profile, values=("six", "dyadic", "all"), state="readonly", width=12).grid(row=1, column=2, padx=6)
        ttk.Button(connection, text="Find sessions", command=self.search).grid(row=2, column=2, padx=6)

        sessions = ttk.LabelFrame(self, text="2. Select an IDtracker session (profile: six, dyadic, or all)")
        sessions.pack(fill="both", expand=True, padx=10, pady=4)
        columns = ("label", "animals", "rois", "start", "end", "trajectory", "video", "blobs")
        self.tree = ttk.Treeview(sessions, columns=columns, show="tree headings", height=9)
        self.tree.heading("#0", text="Session")
        for name, width in [("label", 130), ("animals", 65), ("rois", 55), ("start", 65), ("end", 75), ("trajectory", 220), ("video", 250), ("blobs", 80)]:
            self.tree.heading(name, text=name.title())
            self.tree.column(name, width=width, stretch=name in {"trajectory", "video"})
        self.tree.column("#0", width=360)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(sessions, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<<TreeviewSelect>>", self.select_record)

        settings = ttk.LabelFrame(self, text="3. Review paths and analysis settings")
        settings.pack(fill="x", padx=10, pady=4)
        defaults = dict(session="", trajectory="", video="", label="", start="422", end="7622", fps="30",
                        movement="30", wall="30", fungus="30", proximity="60", jump="200", reconstruction="100",
                        split_confirmation="3", gap_speed="20", gap_cap="300", gap_frames="30",
                        distant_confirmation="10")
        self.variables = {key: tk.StringVar(value=value) for key, value in defaults.items()}
        labels = [
            ("session", "Remote session"), ("trajectory", "Remote trajectory (optional)"), ("video", "Remote source video"),
            ("label", "Output label"), ("start", "Start frame"), ("end", "End frame inclusive"), ("fps", "FPS"),
            ("movement", "Wake movement px"), ("wall", "Wall buffer px"), ("fungus", "Fungus buffer px"),
            ("proximity", "Proximity px"), ("jump", "Analysis jump px"), ("reconstruction", "One-frame identity speed px"),
            ("split_confirmation", "Split confirmation frames"), ("gap_speed", "Gap search growth px/frame"),
            ("gap_cap", "Gap search radius cap px"), ("gap_frames", "Maximum automatic gap frames"),
            ("distant_confirmation", "Distant ID return confirmation frames"),
        ]
        for index, (key, label) in enumerate(labels):
            row, pair = divmod(index, 2)
            column = pair * 2
            ttk.Label(settings, text=label).grid(row=row, column=column, sticky="w", padx=6, pady=2)
            ttk.Entry(settings, textvariable=self.variables[key]).grid(row=row, column=column + 1, sticky="ew", padx=6, pady=2)
        settings.columnconfigure(1, weight=1)
        settings.columnconfigure(3, weight=1)

        actions = ttk.Frame(self)
        actions.pack(fill="x", padx=10, pady=6)
        ttk.Button(actions, text="Preview exact Firebird command", command=self.preview).pack(side="left", padx=4)
        ttk.Button(actions, text="Submit complete pipeline", command=self.submit).pack(side="left", padx=4)
        ttk.Button(actions, text="Check latest job", command=self.check_job).pack(side="left", padx=4)
        ttk.Button(actions, text="Download latest bundle", command=self.download).pack(side="left", padx=4)
        ttk.Label(actions, text="Remote run folder").pack(side="left", padx=(18, 4))
        self.latest_run = tk.StringVar(value="")
        ttk.Entry(actions, textvariable=self.latest_run, width=44).pack(side="left", fill="x", expand=True, padx=4)

        self.log_box = tk.Text(
            self,
            height=10,
            wrap="word",
            background="#FFFFFF",
            foreground="#15181B",
            insertbackground="#15181B",
        )
        self.log_box.pack(fill="both", padx=10, pady=(0, 10))
        self.log("The GUI searches read-only. Jobs write only under the remote output root. All results are marked UNREVIEWED.")

    def ssh(self):
        return SSH(self.host.get(), self.key.get())

    def log(self, message):
        self.log_box.insert("end", str(message).rstrip() + "\n")
        self.log_box.see("end")

    def background(self, name, function):
        def worker():
            try:self.events.put((name, function(), None))
            except Exception as exc:self.events.put((name, None, exc))
        threading.Thread(target=worker, daemon=True).start()

    def _poll(self):
        try:
            while True:
                name, value, error = self.events.get_nowait()
                if error:
                    self.log(f"ERROR: {error}")
                    messagebox.showerror("Firebird group GUI", str(error))
                elif name == "ssh":self.log(f"Connected to {value}")
                elif name == "search":self._show_records(value)
                elif name == "submit":
                    self.jobs.append(value);self.latest_run.set(value["run_dir"]);self.log(f"Submitted Slurm job {value['job_id']}\nRun folder: {value['run_dir']}")
                elif name == "status":self.log(value)
                elif name == "download":
                    self.log(f"Downloaded and verified: {value}")
                    messagebox.showinfo("Download complete", str(value))
        except queue.Empty:pass
        self.after(100, self._poll)

    def test_ssh(self):
        self.log("Testing SSH…")
        self.background("ssh", lambda: self.ssh().run("hostname").strip())

    def search(self):
        roots = [item.strip() for item in self.roots.get().split(";") if item.strip()]
        if not roots:
            messagebox.showerror("Search", "Enter at least one Firebird search root")
            return
        self.log(f"Searching Firebird for {self.profile.get()} sessions…")
        def task():
            ssh = self.ssh()
            command = f"{shlex.quote(self.post_python.get())} -c {shlex.quote(REMOTE_DISCOVERY)}"
            return json.loads(ssh.run(command, json.dumps(dict(roots=roots,profile=self.profile.get())), timeout=900))
        self.background("search", task)

    def _show_records(self, records):
        self.records = records
        self.tree.delete(*self.tree.get_children())
        for index, row in enumerate(records):
            self.tree.insert("", "end", iid=str(index), text=row["session"], values=(row["label"], row["animal_count"], row["roi_count"], row["start"], row["end"], row["trajectory"], row["video"], "yes" if row["blob_source"] else "NO"))
        self.log(f"Found {len(records)} {self.profile.get()} sessions.")

    def select_record(self, _event=None):
        chosen = self.tree.selection()
        if not chosen:return
        row = self.records[int(chosen[0])]
        for key in ("session", "trajectory", "video", "label"):
            if row.get(key) not in (None, "", 0):self.variables[key].set(str(row[key]))
        if isinstance(row.get('start'), int) and isinstance(row.get('end'), int) and row['start']>=0 and row['end']>row['start']:
            self.variables['start'].set(str(row['start']))
            self.variables['end'].set(str(row['end']-1))  # IDtracker intervals are end-exclusive.
        self.log(
            f"Selected {row['session']}\n"
            f"{row['animal_count']} animals, {row['roi_count']-1} fungi. "
            f"Recorded tracking interval: [{row.get('start')}, {row.get('end')}). "
            f"Analysis range set to {self.variables['start'].get()}–{self.variables['end'].get()} inclusive; review before submission."
        )

    def parameters(self):
        return validated_parameters({key: variable.get() for key, variable in self.variables.items()})

    def remote_context(self, deploy=False):
        parameters = self.parameters()
        ssh = self.ssh()
        home = ssh.run('printf "%s" "$HOME"').strip()
        output_root = expand_remote(self.output_root.get(), home).rstrip("/")
        post_python = expand_remote(self.post_python.get(), home)
        idtracker_python = expand_remote(self.idtracker_python.get(), home)
        ffmpeg = expand_remote(self.ffmpeg.get(), home)
        ffprobe = expand_remote(self.ffprobe.get(), home)
        digest = code_digest()
        code_dir = f"{output_root}/_code/{digest[:16]}"
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        safe_label = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in parameters["label"])
        run_dir = f"{output_root}/runs/{stamp}_{safe_label}"
        if deploy:
            preflight = " && ".join(
                [
                    f"test -x {shlex.quote(post_python)}",
                    f"test -x {shlex.quote(idtracker_python)}",
                    f"test -x {shlex.quote(ffmpeg)}",
                    f"test -x {shlex.quote(ffprobe)}",
                    f"test -d {shlex.quote(parameters['session'])}",
                    f"test -f {shlex.quote(parameters['video'])}",
                ]
            )
            ssh.run(preflight)
            ssh.run("mkdir -p " + shlex.quote(code_dir))
            for name in DEPLOY_FILES:
                remote = f"{code_dir}/{name}"
                if ssh.run(f"test -f {shlex.quote(remote)} && printf yes || true").strip() != "yes":
                    ssh.upload(BASE / name, remote)
            remote_hashes = ssh.run(
                "cd " + shlex.quote(code_dir) + " && sha256sum " + " ".join(shlex.quote(name) for name in DEPLOY_FILES)
            )
            observed = {line.split()[1]: line.split()[0] for line in remote_hashes.splitlines() if len(line.split()) >= 2}
            expected = {name: hashlib.sha256((BASE / name).read_bytes()).hexdigest() for name in DEPLOY_FILES}
            if observed != expected:
                raise RuntimeError("Firebird code snapshot hashes do not match the local files")
            self.events.put(("status", "Deployed immutable code snapshot:\n" + remote_hashes, None))
        script = 'run_six_beetle_pipeline.py' if self.profile.get() == 'six' else 'run_group_pipeline.py'
        command = pipeline_command(code_dir, run_dir, post_python, idtracker_python, ffmpeg, ffprobe, parameters, script)
        return ssh, run_dir, command

    def preview(self):
        try:
            _, run_dir, command = self.remote_context(deploy=False)
            self.log("Preview only; nothing submitted:\n" + shlex.join(command) + f"\nRun folder: {run_dir}")
        except Exception as exc:
            messagebox.showerror("Invalid settings", str(exc))

    def submit(self):
        try:self.parameters()
        except Exception as exc:
            messagebox.showerror("Invalid settings", str(exc));return
        self.log("Deploying the exact local code snapshot and submitting the complete pipeline…")
        def task():
            ssh, run_dir, command = self.remote_context(deploy=True)
            ssh.run("mkdir -p " + shlex.quote(run_dir))
            wrapped = shlex.join(command)
            job_name = 'six_beetle_post' if self.profile.get() == 'six' else 'group_beetle_post'
            submit = ["sbatch", "--parsable", f"--job-name={job_name}", "--partition=compute", "--cpus-per-task=4", "--mem=24G", "--time=04:00:00", f"--output={run_dir}/slurm-%j.log", "--wrap", wrapped]
            job_id = ssh.run(shlex.join(submit), timeout=120).strip().split(";", 1)[0]
            return dict(job_id=job_id, run_dir=run_dir, command=command)
        self.background("submit", task)

    def check_job(self):
        if not self.jobs:
            messagebox.showinfo("Job status", "No job has been submitted in this GUI session")
            return
        job = self.jobs[-1]
        def task():
            ssh = self.ssh();job_id=job["job_id"]
            queued = ssh.run(f"squeue -h -j {shlex.quote(job_id)} -o '%T %M %R' || true").strip()
            if queued:return f"Job {job_id}: {queued}"
            accounting = ssh.run(f"sacct -n -X -j {shlex.quote(job_id)} --format=State,Elapsed,ExitCode | head -1 || true").strip()
            return f"Job {job_id}: {accounting or 'not found in queue/accounting yet'}\nRun folder: {job['run_dir']}"
        self.background("status", task)

    def download(self):
        run_dir = self.latest_run.get().strip()
        if not run_dir:
            messagebox.showinfo("Download", "Enter a remote run folder or submit a job in this GUI session")
            return
        destination = filedialog.askdirectory(title="Choose a new local parent folder")
        if not destination:return
        local = Path(destination) / (PurePosixPath(run_dir).name + ".zip")
        if local.exists():
            messagebox.showerror("Download", f"Refusing existing file: {local}");return
        self.log("Packaging and downloading the latest complete result bundle…")
        def task():
            ssh=self.ssh();archive=run_dir+".zip"
            home=ssh.run('printf "%s" "$HOME"').strip()
            post_python=expand_remote(self.post_python.get(),home)
            command=f"{shlex.quote(post_python)} -c {shlex.quote(REMOTE_ARCHIVE)} {shlex.quote(run_dir)} {shlex.quote(archive)}"
            ssh.run(command,timeout=3600)
            remote_hash=ssh.run(f"sha256sum {shlex.quote(archive)}").split()[0]
            partial=local.with_suffix(local.suffix+".partial")
            ssh.download(archive,partial,timeout=7200)
            local_hash=hashlib.sha256(partial.read_bytes()).hexdigest()
            if local_hash != remote_hash:
                partial.unlink(missing_ok=True);raise RuntimeError("Downloaded archive SHA-256 does not match Firebird")
            partial.replace(local)
            return local
        self.background("download",task)


def main():
    App().mainloop()


if __name__ == "__main__":
    main()

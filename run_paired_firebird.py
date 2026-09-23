#!/usr/bin/env python3
"""Submit immutable human-setting/background-on and shared-setting Firebird pairs."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shlex
from pathlib import Path

from idtracker_toml_manager import DEFAULT_GROUPTRIAL_ROOT, DEFAULT_IDTRACKER_ENV, DEFAULT_RUN_ROOT
from six_beetle_firebird_gui import DEFAULT_SSH_HOST, DEFAULT_SSH_KEY, SSH


# These are the five unique sources with no trajectory in the 22 Sep 2026 batch.
# Hashes pin the exact segmentation-app originals; a changed source aborts.
SOURCES = {
    "groupagetrial01_062024_Box02_MIX.toml": "01551fca302ae0b9093bc1387d218bef925da3e90688e8dd9ed7023f5514f314",
    "groupagetrial02_062024_Box01_YOUNG.toml": "fcce6916fadbbbde3e25b0b76d947a3ac49897fcced2b5872e622ed7b4fce426",
    "groupagetrial02_062024_Box03_OLD.toml": "ce90c7155af60336fba46c479bd163842e20e9dc1de3a9f526cf16eb7f480b3f",
    "groupagetrial03_062124_Box03_OLD.toml": "2e308353805d219e1a3783b2bab1a95790290ec6e012db2968f0e7bdf74bab0c",
    "groupagetrial04_062124_Box01_MIX.toml": "a44bad3346a154f489378b22e809f658d7df7add5ed35339a7fa6ac10f0357d6",
}

REMOTE_SUBMIT = r'''
import datetime as dt, hashlib, json, os, re, shlex, shutil, subprocess, sys, tomllib
from pathlib import Path

request=json.load(sys.stdin)
root=Path(request["batch_root"])
source_root=Path(request["source_root"])
environment=Path(request["environment"])
runner=Path(request["runner"])
assert runner.is_file() and (environment/"bin/idtrackerai").is_file()

def replace_value(text,key,value):
    pattern=re.compile(r"(?m)^("+re.escape(key)+r"\s*=\s*)([^\n]*)$")
    changed,count=pattern.subn(lambda match:match.group(1)+value,text,count=1)
    if count != 1:raise ValueError("Expected one "+key)
    return changed

def variant(text,mode):
    if mode == "human_bkg_on":
        return replace_value(text,"use_bkg","true")
    if mode == "shared_50_400_bkg_on":
        text=replace_value(text,"use_bkg","true")
        text=replace_value(text,"intensity_ths","[50, 255]")
        return replace_value(text,"area_ths","[400.0, inf]")
    raise ValueError(mode)

# Check every input and both generated configurations before submitting any job.
planned=[]
for filename,expected_hash in request["sources"].items():
    source=source_root/filename
    raw=source.read_bytes()
    actual=hashlib.sha256(raw).hexdigest()
    if actual != expected_hash:raise ValueError(f"Source changed: {source}: {actual}")
    base=tomllib.loads(raw.decode())
    assert base["number_of_animals"] == 6 and len(base["roi_list"]) == 4
    assert len(base["tracking_intervals"]) == 1
    assert all(Path(p).is_file() for p in base["video_paths"])
    for mode in ("human_bkg_on","shared_50_400_bkg_on"):
        text=variant(raw.decode(),mode)
        data=tomllib.loads(text)
        assert data["use_bkg"] is True
        assert data["tracking_intervals"] == base["tracking_intervals"]
        assert data["roi_list"] == base["roi_list"]
        assert all(type(x) is float for x in data["area_ths"])
        planned.append((filename,mode,text,actual,base,data))

root.mkdir(parents=True,exist_ok=False)
receipts=[]
for filename,mode,text,source_hash,base,data in planned:
    label=Path(filename).stem
    run=root/(label+"__"+mode)
    (run/"input").mkdir(parents=True)
    toml_path=run/"input/submitted.toml"
    toml_path.write_text(text)
    runner_path=run/"firebird_idtracker_runner.py"
    shutil.copy2(runner,runner_path)
    output=run/"idtracker_output"
    command=[str(environment/"bin/python"),str(runner_path),"--toml",str(toml_path),"--output",str(output),"--workers","10","--device","cuda","--data-policy","all"]
    metadata={
        "schema_version":1,"source_toml":str(source_root/filename),"source_sha256":source_hash,
        "submitted_toml_sha256":hashlib.sha256(text.encode()).hexdigest(),
        "variant":mode,"use_bkg":True,"intensity_ths":data["intensity_ths"],
        "area_ths":["inf" if x==float("inf") else x for x in data["area_ths"]],
        "tracking_intervals":data["tracking_intervals"],"roi_count":len(data["roi_list"]),
        "batch_root":str(root),"run_dir":str(run),"command":command,
        "submitted_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "slurm":{"partition":"gpu","nodelist":"gpu02","gres":"gpu:quadro_8000:1","cpus":10,"memory":"48G","time":"08:00:00"},
    }
    (run/"submission_request.json").write_text(json.dumps(metadata,indent=2,sort_keys=True)+"\n")
    wrapped="export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1; export MPLCONFIGDIR="+shlex.quote(str(run/"matplotlib_cache"))+"; export PYTHONUNBUFFERED=1; exec "+shlex.join(command)
    submit=["sbatch","--parsable","--job-name=idta_"+label[:25]+("_H" if mode=="human_bkg_on" else "_C"),
            "--partition=gpu","--nodelist=gpu02","--gres=gpu:quadro_8000:1","--nodes=1",
            "--cpus-per-task=10","--mem=48G","--time=08:00:00",
            "--chdir="+str(run),"--output="+str(run/"slurm-%j.log"),"--wrap",wrapped]
    result=subprocess.run(submit,text=True,capture_output=True)
    if result.returncode:
        (root/"partial_receipts.json").write_text(json.dumps(receipts,indent=2)+"\n")
        raise RuntimeError(f"sbatch failed for {filename} {mode}: {result.stderr}")
    metadata.update(job_id=result.stdout.strip().split(";",1)[0],stage="SUBMITTED")
    (run/"submission_receipt.json").write_text(json.dumps(metadata,indent=2,sort_keys=True)+"\n")
    receipts.append(metadata)
(root/"batch_receipts.json").write_text(json.dumps(receipts,indent=2,sort_keys=True)+"\n")
json.dump(receipts,sys.stdout)
'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--submit", action="store_true", help="Create and submit ten immutable Slurm jobs")
    parser.add_argument("--host", default=DEFAULT_SSH_HOST)
    parser.add_argument("--key", default=DEFAULT_SSH_KEY)
    args = parser.parse_args()
    if not args.submit:
        for filename in SOURCES:
            print(filename, "human_bkg_on + shared_50_400_bkg_on")
        return
    label = dt.datetime.now(dt.timezone.utc).strftime("paired_20260922_%H%M%S_utc")
    batch_root = DEFAULT_RUN_ROOT + "/" + label
    ssh = SSH(args.host, args.key)
    ssh.run("mkdir -p " + shlex.quote(DEFAULT_RUN_ROOT))
    ssh.upload(Path(__file__).with_name("firebird_idtracker_runner.py"), DEFAULT_RUN_ROOT + "/paired_runner_20260922.py")
    payload = {"batch_root": batch_root, "source_root": DEFAULT_GROUPTRIAL_ROOT,
               "environment": DEFAULT_IDTRACKER_ENV,
               "runner": DEFAULT_RUN_ROOT + "/paired_runner_20260922.py", "sources": SOURCES}
    command = shlex.quote(DEFAULT_IDTRACKER_ENV + "/bin/python") + " -c " + shlex.quote(REMOTE_SUBMIT)
    receipts = json.loads(ssh.run(command, json.dumps(payload), timeout=1800))
    local = Path(__file__).parent / "results" / label
    local.mkdir(parents=True, exist_ok=False)
    (local / "submissions.json").write_text(json.dumps(receipts, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"batch_root":batch_root,"jobs":[{k:r[k] for k in ("job_id","variant","source_toml","run_dir")} for r in receipts]},indent=2))


if __name__ == "__main__":
    main()

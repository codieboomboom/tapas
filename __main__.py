#!/usr/bin/env python3
# tap_trainer/__main__.py
import argparse, sys, json, os, platform, time
from pathlib import Path

APP_NAME = "tapas"
HOME = Path.home() / ".tapas"
PRESETS_DIR = HOME / "presets"
ATTEMPTS_DIR = HOME / "attempts"
CONFIG_PATH = HOME / "config.json"
CALIB_PATH = HOME / "calibration.json"

def ensure_dirs():
    """Ensuring the required directory are present"""
    PRESETS_DIR.mkdir(parents=True, exist_ok=True)
    ATTEMPTS_DIR.mkdir(parents=True, exist_ok=True)
    HOME.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(json.dumps({"version":"1"}, indent=2))
    if not CALIB_PATH.exists():
        CALIB_PATH.write_text(json.dumps({"devices":{}}, indent=2))

# --------- Helpers (stubs to implement in modules later) ---------
def run_metronome(bpm, meter, subdiv, swing, count_in, bars, minutes, beep, accent):
    # TODO: call metronome.scheduler(...)
    print(f"[metronome] {bpm=} {meter=} {subdiv=} {swing=} {count_in=} {bars=} {minutes=} {beep=} {accent=}")

def preset_new(name, time_sig, bars, subdivision, interactive):
    ensure_dirs()
    path = PRESETS_DIR / f"{name}.json"
    if path.exists():
        print(f"Preset exists: {path}")
        return 1
    preset = {
        "name": name,
        "tempo": 100,
        "time_sig": time_sig,
        "bars": bars,
        "subdivision": subdivision,
        "notes": []
    }
    if interactive:
        print("Interactive mode not implemented yet. Creating empty preset.")
    path.write_text(json.dumps(preset, indent=2))
    print(f"Created {path}")
    return 0

def preset_list():
    ensure_dirs()
    items = sorted(p.name for p in PRESETS_DIR.glob("*.json"))
    for it in items:
        print(it)

def preset_show(name):
    ensure_dirs()
    path = PRESETS_DIR / f"{name}.json"
    if not path.exists():
        print(f"Not found: {path}", file=sys.stderr)
        return 1
    print(path.read_text())
    return 0

def preset_validate(name):
    # TODO: load and verify time_sig, bars, subdivision, idx ranges
    return preset_show(name)

def practice_run(preset_name, bpm, bars, minutes, export, device):
    # TODO: orchestrate: click -> record (or prompt) -> analyze -> report
    print(f"[practice] preset={preset_name} bpm={bpm} bars={bars} minutes={minutes} export={export} device={device}")

def analyze_file(audio_path, preset_name, bpm, report):
    # TODO: read WAV -> onset detect -> DTW -> score -> dump artifacts
    print(f"[analyze] audio={audio_path} preset={preset_name} bpm={bpm} report={report}")

def calibrate(device):
    # TODO: play 8 clicks -> user claps -> detect vs scheduled -> store median latency
    print(f"[calibrate] device={device}")

def tap_tempo():
    """Get tempo from tapping of user (interactive)"""
    print("Tap ENTER ~4–8 times. Empty line to finish.")
    timestamp = []
    while True:
        line = sys.stdin.readline()
        now = time.perf_counter()
        if not line.strip():
            break
        timestamp.append(now)
    if len(timestamp) < 2:
        print("Not enough taps.")
        return
    intervals = [end_timestamp - start_timestamp for start_timestamp, end_timestamp in zip(timestamp, timestamp[1:])]
    intervals.sort()
    med = intervals[len(intervals)//2]
    bpm = round(60.0 / med, 1)
    print(f"BPM ≈ {bpm}")

def report_history(preset, last, metric):
    # TODO: scan ATTEMPTS_DIR and aggregate
    print(f"[report] preset={preset} last={last} metric={metric}")

# ---------------------- Argument parsing ------------------------
def build_parser():
    parser = argparse.ArgumentParser(prog=APP_NAME, description="Tap Trainer (CLI, stdlib-only)")
    subparser = parser.add_subparsers(dest="cmd", required=True)

    # metronome mode
    metronome_parser = subparser.add_parser("metronome", help="Run a metronome")
    metronome_parser.add_argument("--bpm", type=float, required=True, help="Tempo in BPM")
    metronome_parser.add_argument("--meter", default="4/4", help="Time signature, e.g. 4/4, 7/8, 6/8")
    metronome_parser.add_argument("--subdiv", type=int, default=1, help="Subdivisions per beat (1,2,3,4,6)")
    metronome_parser.add_argument("--swing", type=float, default=0.0, help="Swing ratio for subdiv=2 (e.g., 0.66)")
    metronome_parser.add_argument("--count-in", type=int, default=0, help="Count-in bars before start")
    duration = metronome_parser.add_mutually_exclusive_group()
    duration.add_argument("--bars", type=int, help="Run for N bars")
    duration.add_argument("--minutes", type=float, help="Run for N minutes")
    metronome_parser.add_argument("--beep", action="store_true", help="Play OS beeps if available")
    metronome_parser.add_argument("--accent", default=None, help="Accent pattern, e.g., 1,0,0,0")
    metronome_parser.set_defaults(func=lambda a: run_metronome(
        a.bpm, a.meter, a.subdiv, a.swing, a.count_in, a.bars, a.minutes, a.beep, a.accent
    ))

    # preset (group with subcommands)
    preset_parser = subparser.add_parser("preset", help="Manage rudiment presets")
    preset_subparser = preset_parser.add_subparsers(dest="preset_cmd", required=True)

    new_preset_parser = preset_subparser.add_parser("new", help="Create a new preset JSON")
    new_preset_parser.add_argument("--name", required=True)
    new_preset_parser.add_argument("--meter", default="4/4", dest="time_sig")
    new_preset_parser.add_argument("--bars", type=int, default=4)
    new_preset_parser.add_argument("--subdivision", type=int, default=4)
    new_preset_parser.add_argument("--interactive", action="store_true")
    new_preset_parser.set_defaults(func=lambda a: preset_new(a.name, a.time_sig, a.bars, a.subdivision, a.interactive))

    list_preset_parser = preset_subparser.add_parser("list", help="List presets")
    list_preset_parser.set_defaults(func=lambda a: preset_list())

    show_preset_parser = preset_subparser.add_parser("show", help="Show preset JSON")
    show_preset_parser.add_argument("name")
    show_preset_parser.set_defaults(func=lambda a: preset_show(a.name))

    validate_preset_parser = preset_subparser.add_parser("validate", help="Validate preset schema")
    validate_preset_parser.add_argument("name")
    validate_preset_parser.set_defaults(func=lambda a: preset_validate(a.name))

    # practice mode
    practice_parser = subparser.add_parser("practice", help="Practice a preset (record/analyze)")
    practice_parser.add_argument("preset", help="Preset name (without .json)")
    practice_parser.add_argument("--bpm", type=float, help="Override preset tempo")
    practice_parser.add_argument("--bars", type=int, help="Limit run to N bars")
    practice_parser.add_argument("--minutes", type=float, help="Limit run to N minutes")
    practice_parser.add_argument("--export", default="json,csv", help="Comma list: wav,json,csv")
    practice_parser.add_argument("--device", default=None, help="Audio input device (if recording)")
    practice_parser.set_defaults(func=lambda a: practice_run(a.preset, a.bpm, a.bars, a.minutes, a.export, a.device))

    # analyze mode
    analyze_parser = subparser.add_parser("analyze", help="Analyze a WAV against a preset")
    analyze_parser.add_argument("--audio", required=True, help="Path to WAV file")
    analyze_parser.add_argument("--preset", required=True, help="Preset name (without .json)")
    analyze_parser.add_argument("--bpm", type=float, help="Override preset tempo")
    analyze_parser.add_argument("--report", choices=["summary","detailed"], default="summary")
    analyze_parser.set_defaults(func=lambda a: analyze_file(a.audio, a.preset, a.bpm, a.report))

    # calibrate mode
    calibrate_parser = subparser.add_parser("calibrate", help="Estimate device latency and store it")
    calibrate_parser.add_argument("--device", default=None, help="Input device name/id (if applicable)")
    calibrate_parser.set_defaults(func=lambda a: calibrate(a.device))

    # tap-tempo mode
    tap_tempo_parser = subparser.add_parser("tap-tempo", help="Tap ENTER to estimate BPM")
    tap_tempo_parser.set_defaults(func=lambda a: tap_tempo())

    # report mode
    report_parser = subparser.add_parser("report", help="Show progress reports from attempts")
    report_parser.add_argument("--preset", default=None, help="Filter by preset")
    report_parser.add_argument("--last", type=int, default=30, help="Number of recent attempts")
    report_parser.add_argument("--metric", choices=["score","mean_err","variance"], default="score")
    report_parser.set_defaults(func=lambda a: report_history(a.preset, a.last, a.metric))

    return parser

def main(argv=None):
    ensure_dirs()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        rc = args.func(args)
        if isinstance(rc, int):
            sys.exit(rc)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)

if __name__ == "__main__":
    main()
# Check fictional Python syntax without running it

Save three source files in a NEW empty lesson folder.

    python make_sample.py
    python pycheck.py sample/colon.py
    python -m unittest -v

Two Windows and two Ubuntu full replays run exact visible source versions. Final 38 small fixture tests pass (Unix pipe skips on Windows); symlink creation can skip where unavailable. Displayed stdout is first Windows output, not normalized or mixed. Pair differences are unittest time.
Only link/error changes: final reader refuses input/ancestor symbolic links/reparse points, hardlinks, special files and traversal before reading. Metadata/open errors remain exit 2. Setup refuses linked parents/traversal and existing sample paths, without reset or deletion. Naive first version remains fictional-sample-only and must be replaced.
Original AST parsing, syntax messages, source encoding handling, import listing and function/class/line counts remain unchanged. Exits remain 0 no syntax error found, 1 parser-reported error, 2 usage/read errors. Checked scripts are not run and imports are not loaded or checked. A pass is not execution, dependency, type, security or program-correctness proof. Python version affects accepted syntax and messages.
The checker has no write/move/delete/network code but reads the whole source and builds an AST in memory. No size/time/resource limit, atomic snapshot or hostile-race defense. Stop editors/sync. Paths and error excerpts can be private. Small fictional fixtures are not proof on every filesystem. No desktop Windows/macOS recording. Recorder removes only its own temporary fixture folder. Decisions and feedback are teaching text, not recorded output.

MIT code. Python separately licensed/not included.

Reference: https://docs.python.org/3/library/os.html

Windows pair: https://github.com/faiz12321/lesson-lab/actions/runs/38973800907
Ubuntu pair: https://github.com/faiz12321/lesson-lab/actions/runs/38973865534

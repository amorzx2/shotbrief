# ShotBrief

A small, offline Python tool that validates JSON shot lists and exports Markdown prompt cards for AI video planning.

**Status:** initial version, 0.1.0. This is a new project, not an established or widely adopted tool. AI-assisted implementation. No claimed usage statistics or model integrations. It does not generate videos, call models, or automatically improve prompts.

## Run

Requires Python 3.9+; standard library only, no install or API key needed. Run commands in the repository folder.

```sh
python shotbrief.py examples/shotlist.json --check
python shotbrief.py examples/shotlist.json -o prompts.md
python shotbrief.py examples/shotlist.json
python -m unittest discover -s tests -v
```

On some systems use `python3` instead of `python`. On Windows, `py -3` also works. If redirecting Unicode output in an older terminal, use `-o` for a UTF-8 file instead.

Existing output files are protected. Add `--force` only when you intend to replace them. Input and output cannot be the same path. `--check` validates without creating output. Files are handled locally; no telemetry or network requests.

## Input

```json
{
  "title": "Morning",
  "shots": [
    {
      "duration": 6,
      "scene": "A sunlit room",
      "camera": "A slow forward movement",
      "action": "A curtain lifts in the breeze",
      "ending": "The white curtain fills the frame"
    }
  ]
}
```

All fields are required. `duration` is a finite number of seconds greater than zero and at most 86400 (one day). Text fields must contain non-whitespace text; Unicode text is supported. Unknown fields and duplicate JSON keys are rejected to catch typos. Shot numbers in errors are one-based. Duration is descriptive metadata, not a guarantee that a video model supports it.

## Output and limits

Each shot becomes a numbered card with duration, scene, camera, action, ending, and a single combined prompt. The tool preserves your intent instead of inventing content. Markdown/HTML characters in your text are escaped for display. Read and adapt the result before using it with a video model; this tool cannot verify artistic quality, factual accuracy, continuity, licensing, or provider compatibility.

## Contributing

Bug reports should include a minimal, non-sensitive JSON example, the command, Python version, and expected result. Please do not upload private client briefs, personal information, credentials, or copyrighted source assets. Keep additions small and include tests.

MIT licensed. See [LICENSE](LICENSE).

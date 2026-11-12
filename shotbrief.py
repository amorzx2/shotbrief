#!/usr/bin/env python3
"""Validate a shot list and turn it into Markdown prompt cards. No network use."""
import argparse
import json
import os
from pathlib import Path
import sys

__version__ = "0.1.0"
TEXT_FIELDS = ("scene", "camera", "action", "ending")


class ValidationError(ValueError):
    """An input document does not follow the ShotBrief schema."""


def _text(value, path):
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{path}: expected a non-empty string")
    return value.strip()


def validate(data):
    """Return a normalized copy, or raise ValidationError. Input is not modified."""
    if not isinstance(data, dict):
        raise ValidationError("root: expected an object")
    unknown = set(data) - {"title", "shots"}
    if unknown:
        raise ValidationError(f"root: unknown fields: {', '.join(sorted(unknown))}")
    title = _text(data.get("title"), "title")
    shots = data.get("shots")
    if not isinstance(shots, list) or not shots:
        raise ValidationError("shots: expected a non-empty array")
    result = []
    for i, shot in enumerate(shots, 1):
        prefix = f"shots[{i}]"
        if not isinstance(shot, dict):
            raise ValidationError(f"{prefix}: expected an object")
        unknown = set(shot) - set(TEXT_FIELDS) - {"duration"}
        if unknown:
            raise ValidationError(f"{prefix}: unknown fields: {', '.join(sorted(unknown))}")
        duration = shot.get("duration")
        if (isinstance(duration, bool) or not isinstance(duration, (int, float))
                or not 0 < duration <= 86400):
            raise ValidationError(f"{prefix}.duration: expected seconds greater than 0 and at most 86400")
        clean = {key: _text(shot.get(key), f"{prefix}.{key}") for key in TEXT_FIELDS}
        clean["duration"] = duration
        result.append(clean)
    return {"title": title, "shots": result}


def _escape(text):
    """Keep user text literal rather than interpreting Markdown/HTML markup."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    for char in "\\`*_{}[]()#!|":
        text = text.replace(char, "\\" + char)
    return text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")


def render(data):
    """Validate data and return UTF-8-friendly Markdown, without model calls."""
    data = validate(data)
    total = sum(shot["duration"] for shot in data["shots"])
    lines = [f"# {_escape(data['title'])}", "", f"{len(data['shots'])} shots | {total:g} seconds", ""]
    labels = {"scene": "Scene", "camera": "Camera", "action": "Action", "ending": "Ending"}
    for i, shot in enumerate(data["shots"], 1):
        lines += [f"## Shot {i:02d} | {shot['duration']:g}s", ""]
        for field in TEXT_FIELDS:
            lines.append(f"- **{labels[field]}:** {_escape(shot[field])}")
        lines += ["", "**Prompt card**", "", _escape(
            f"Duration: {shot['duration']:g} seconds. Scene: {shot['scene']} "
            f"Camera: {shot['camera']} Action: {shot['action']} Ending: {shot['ending']}"), ""]
    return "\n".join(lines)


def _pairs(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValidationError(f"Duplicate JSON key: {key}")
        obj[key] = value
    return obj


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON shot list (UTF-8)")
    parser.add_argument("-o", "--output", type=Path, help="Markdown output; defaults to stdout")
    parser.add_argument("--check", action="store_true", help="Validate only; do not write Markdown")
    parser.add_argument("--force", action="store_true", help="Replace an existing output file")
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args(argv)
    if args.check and args.output:
        parser.error("--check cannot be combined with --output")
    try:
        if args.output and (args.input.resolve() == args.output.resolve()
                            or (args.output.exists() and os.path.samefile(args.input, args.output))):
            raise ValidationError("Input and output must be different files")
        data = json.loads(args.input.read_text(encoding="utf-8-sig"), object_pairs_hook=_pairs)
        markdown = render(data)
        if args.check:
            print("Valid shot list.")
        elif args.output:
            # Exclusive creation protects existing work unless replacement is explicit.
            with args.output.open("w" if args.force else "x", encoding="utf-8", newline="\n") as output:
                output.write(markdown)
        else:
            sys.stdout.write(markdown)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"shotbrief: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

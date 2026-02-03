"""
All the drafts are built by the build-specs workflow itself.
This handles the rest of the work:

* creates an index page listing all specs
* creates symlinks for unlevelled urls, linking to the appropriate levelled folder
* builds timestamps.json, which provides metadata about the specs
"""

import json
import os
import os.path
import re
import subprocess
from collections import defaultdict
from datetime import datetime, timezone

import bikeshed
from html.parser import HTMLParser


def title_from_html(file):
    class HTMLTitleParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.in_title = False
            self.title = ""
            self.done = False

        def handle_starttag(self, tag, attrs):
            if tag == "title":
                self.in_title = True

        def handle_data(self, data):
            if self.in_title:
                self.title += data

        def handle_endtag(self, tag):
            if tag == "title" and self.in_title:
                self.in_title = False
                self.done = True
                self.reset()

    parser = HTMLTitleParser()
    with open(file, encoding="UTF-8") as f:
        for line in f:
            parser.feed(line)
            if parser.done:
                break
    if not parser.done:
        parser.close()

    return parser.title if parser.done else None


def get_date_authored_timestamp_from_git(path):
    source = os.path.realpath(path)
    proc = subprocess.run(["git", "log", "-1", "--format=%at", source],
                          capture_output=True, encoding="utf_8")
    return int(proc.stdout.splitlines()[-1])


def get_bs_spec_metadata(folder_name, path):
    spec = bikeshed.Spec(path)
    spec.assembleDocument()

    level = int(spec.md.level) if spec.md.level else 0
    shortname = spec.md.shortname

    return {
        "timestamp": get_date_authored_timestamp_from_git(path),
        "shortname": shortname,
        "level": level,
        "title": spec.md.title,
        "workStatus": spec.md.workStatus
    }


def get_html_spec_metadata(folder_name, path):
    match = re.match("^([a-z0-9-]+)-([0-9]+)$", folder_name)
    shortname = match.group(1) if match else folder_name
    title = title_from_html(path)

    return {
        "shortname": shortname,
        "level": int(match.group(2)) if match else 0,
        "title": title,
        "workStatus": "completed"  # It's a good heuristic
    }


def create_symlink(shortname, spec_folder):
    """Creates a <shortname> symlink pointing to the given <spec_folder>."""

    if spec_folder in timestamps:
        timestamps[shortname] = timestamps[spec_folder]

    try:
        os.symlink(spec_folder, shortname)
    except OSError:
        pass


def format_timestamp(ts):
    """Format a Unix timestamp as a human-readable date string."""
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d")


def escape_html(text):
    """Escape HTML special characters."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


CURRENT_WORK_EXCEPTIONS = {}

# ------------------------------------------------------------------------------


bikeshed.messages.state.dieOn = "nothing"

specgroups = defaultdict(list)
timestamps = defaultdict(list)

for entry in os.scandir("."):
    if entry.is_dir(follow_symlinks=False):
        bs_file = os.path.join(entry.path, "Overview.bs")
        html_file = os.path.join(entry.path, "Overview.html")
        if os.path.exists(bs_file):
            metadata = get_bs_spec_metadata(entry.name, bs_file)
            timestamps[entry.name] = metadata["timestamp"]
        elif os.path.exists(html_file):
            metadata = get_html_spec_metadata(entry.name, html_file)
        else:
            # Not a spec
            continue

        metadata["dir"] = entry.name
        metadata["currentWork"] = False
        specgroups[metadata["shortname"]].append(metadata)

# Reorder the specs with common shortname based on their level,
# and determine which spec is the current work.
for shortname, specgroup in specgroups.items():
    if len(specgroup) == 1:
        if shortname != specgroup[0]["dir"]:
            create_symlink(shortname, specgroup[0]["dir"])
    else:
        specgroup.sort(key=lambda spec: spec["level"])

        for spec in specgroup:
            if shortname in CURRENT_WORK_EXCEPTIONS:
                if CURRENT_WORK_EXCEPTIONS[shortname] == spec["level"]:
                    spec["currentWork"] = True
                    currentWorkDir = spec["dir"]
                    break
            elif spec["workStatus"] != "completed":
                spec["currentWork"] = True
                currentWorkDir = spec["dir"]
                break
        else:
            specgroup[-1]["currentWork"] = True
            currentWorkDir = specgroup[-1]["dir"]

        if shortname != currentWorkDir:
            create_symlink(shortname, currentWorkDir)

with open('./timestamps.json', 'w') as f:
    json.dump(timestamps, f, indent=2, sort_keys=True)

# Build the index page
rows = []
for shortname in sorted(specgroups.keys()):
    specgroup = specgroups[shortname]
    for spec in specgroup:
        title = escape_html(spec["title"] or spec["dir"])
        level_suffix = f" Level {spec['level']}" if spec["level"] else ""
        current_label = ' <span class="current-work">(Current Work)</span>' if spec["currentWork"] else ""
        dir_name = spec["dir"]

        ts = timestamps.get(dir_name)
        date_str = format_timestamp(ts) if ts else ""

        rows.append(
            f'      <tr>\n'
            f'        <td><a href="./{dir_name}/">{title}</a>{current_label}</td>\n'
            f'        <td>{date_str}</td>\n'
            f'      </tr>'
        )

rows_html = "\n".join(rows)

with open("./index.html", mode='w', encoding="UTF-8") as f:
    f.write(f"""\
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>CSS Houdini Task Force Editor Drafts</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      max-width: 900px;
      margin: 2em auto;
      padding: 0 1em;
      color: #333;
    }}
    h1 {{
      border-bottom: 1px solid #ccc;
      padding-bottom: 0.3em;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 1em;
    }}
    th, td {{
      text-align: left;
      padding: 0.5em 0.75em;
      border-bottom: 1px solid #eee;
    }}
    th {{
      border-bottom: 2px solid #ccc;
      font-weight: 600;
    }}
    td:last-child {{
      white-space: nowrap;
      color: #666;
    }}
    a {{
      color: #0366d6;
      text-decoration: none;
    }}
    a:hover {{
      text-decoration: underline;
    }}
    .current-work {{
      color: #080;
      font-size: 0.9em;
    }}
  </style>
</head>
<body>
  <h1>CSS Houdini Task Force Editor Drafts</h1>
  <table>
    <thead>
      <tr>
        <th>Specification</th>
        <th>Last Update</th>
      </tr>
    </thead>
    <tbody>
{rows_html}
    </tbody>
  </table>
</body>
</html>
""")

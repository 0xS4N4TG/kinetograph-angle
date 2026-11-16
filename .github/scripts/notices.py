"""Write THIRD-PARTY-NOTICES.txt: every third-party component the shipped libraries are built from, with its licence text.

The components are the directories (the targets' own and those of their source files, from gn's project description) that the shipped targets
depend on; each is resolved to the nearest directory (walking up) that carries a README.chromium or a
licence file. Usage: notices.py <angle checkout> <gn out dir> <output file> <gn target>..."""
import json, os, re, subprocess, sys

src, outdir, outfile, *targets = sys.argv[1:]
B = ".bat" if sys.platform == "win32" else ""
LICENSE_NAME = re.compile(r"^(licen[cs]e|copying|notice|unlicense)", re.I)
SKIP = ("out", "build", "build/config", "testing", "tools", "third_party/googletest", "buildtools/third_party/eu-strip")

r = subprocess.run(["gn" + B, "gen", outdir, "--ide=json"], cwd=src, capture_output=True, text=True)
if r.returncode:
    sys.exit(f"gn gen --ide=json failed:\n{r.stdout}{r.stderr}")
graph = json.load(open(os.path.join(src, outdir, "project.json"), encoding="utf8"))["targets"]
strip = lambda label: re.sub(r"\(.*\)$", "", label)
by_label = {}
for label, t in graph.items():
    by_label.setdefault(strip(label), label)
# Walk the dependencies of the shipped targets, not through programs run at build time (executables); a target contributes its
# own directory and the directories of its source files.
dirs, seen, todo = set(), set(), [by_label[t] for t in targets]
while todo:
    label = todo.pop()
    if label in seen or label not in graph:
        continue
    seen.add(label)
    t = graph[label]
    if t["type"] == "executable":
        continue
    dirs.add(re.match(r"//([^:]*)", label).group(1))
    for f in t.get("sources", []):
        dirs.add(os.path.dirname(f[2:]))
    todo.extend(t.get("deps", []))
print(len(seen), "targets,", len(dirs), "directories")

def readme(path):
    fields = {}
    f = os.path.join(path, "README.chromium")
    if os.path.exists(f):
        for line in open(f, encoding="utf8", errors="replace"):
            k, sep, v = line.partition(":")
            if sep and k.strip() in ("Name", "URL", "Version", "License", "License File", "Revision"):
                fields.setdefault(k.strip(), v.strip())
    return fields

def has_info(rel):
    p = os.path.join(src, rel)
    return os.path.exists(os.path.join(p, "README.chromium")) or any(LICENSE_NAME.match(n) for n in os.listdir(p) if os.path.isfile(os.path.join(p, n)))

components = {}
for d in sorted(dirs):
    if any(d == s or d.startswith(s + "/") for s in SKIP) or not d or not os.path.isdir(os.path.join(src, d)):
        continue
    rel = d
    while rel and not has_info(rel):
        rel = os.path.dirname(rel)
    components[rel] = True  # "" is ANGLE's own tree
print(f"{len(dirs)} gn directories -> {len(components)} components")

def license_files(rel):
    p = os.path.join(src, rel)
    names = {n for n in os.listdir(p) if os.path.isfile(os.path.join(p, n)) and LICENSE_NAME.match(n)}
    lf = readme(p).get("License File", "")
    if lf and lf.upper() != "NONE":
        for n in re.split(r"[,\s]+", lf):
            if n and os.path.isfile(os.path.join(p, n)):
                names.add(n)
    return sorted(names)

sha = subprocess.check_output(["git", "-C", src, "rev-parse", "HEAD"], text=True).strip()
out = [f"Third-party components in these libraries (ANGLE {sha}).\n",
       "ANGLE (BSD-3-Clause, the file LICENSE in this archive) is built with the components below. The list is the set of\n"
       "directories of the ANGLE source tree that the shipped targets depend on, as reported by gn; each entry gives the\n"
       "component's name, version and licence from its README.chromium and the full text of its licence files.\n"]
missing = []
for rel in sorted(components, key=lambda r: (r == "", r)):
    info = readme(os.path.join(src, rel))
    files = license_files(rel)
    name = info.get("Name") or os.path.basename(rel) or "ANGLE"
    out.append("=" * 78)
    out.append(f"{name}\n  path:     {rel or '(ANGLE root)'}")
    for k in ("URL", "Version", "Revision", "License"):
        if k in info:
            out.append(f"  {k.lower() + ':':<9} {info[k]}")
    out.append("=" * 78)
    if not files:
        missing.append(rel)
        out.append("(no licence file in the source tree)")
    for n in files:
        out.append(f"--- {rel + '/' if rel else ''}{n}\n")
        out.append(open(os.path.join(src, rel, n), encoding="utf8", errors="replace").read().strip() + "\n")
open(outfile, "w", encoding="utf8", newline="\n").write("\n".join(out) + "\n")
print("components:", ", ".join(r or "(ANGLE)" for r in sorted(components)))
print("without licence file:", missing)

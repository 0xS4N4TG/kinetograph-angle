"""Write THIRD-PARTY-NOTICES.txt: every third-party component the shipped libraries are built from, with its licence text.

The components are the directories gn reports as dependencies of the shipped targets (gn desc <target> deps --all) that sit
outside ANGLE's own code; each is resolved to the nearest directory (walking up) that carries a README.chromium or a
licence file. Usage: notices.py <angle checkout> <gn out dir> <output file> <gn target>..."""
import os, re, subprocess, sys

src, outdir, outfile, *targets = sys.argv[1:]
B = ".bat" if sys.platform == "win32" else ""
LICENSE_NAME = re.compile(r"^(licen[cs]e|copying|notice|unlicense)", re.I)
SKIP = ("build", "build/config", "testing", "tools", "third_party/googletest", "buildtools/third_party/eu-strip")

dirs = set()
for t in targets:
    r = subprocess.run(["gn" + B, "desc", outdir, t, "deps", "--all"], cwd=src, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"gn desc {t} failed:\n{r.stdout}{r.stderr}")
    for line in r.stdout.splitlines():
        m = re.match(r"\s*//([^:()\s]*)", line)
        if m:
            dirs.add(m.group(1))
    dirs.add(re.match(r"//([^:]*)", t).group(1))

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

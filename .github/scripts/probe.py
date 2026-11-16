"""Print what an ANGLE checkout says about SwiftShader, the Vulkan loader and licences (diagnostic, changes nothing)."""
import os, re, subprocess, sys

src, outdir = sys.argv[1:3]
B = ".bat" if sys.platform == "win32" else ""
ext = {"win32": "dll", "darwin": "dylib"}.get(sys.platform, "so")

def sh(cmd, tail=4000):
    print("$", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=src, capture_output=True, text=True)
    out = "\n".join(l for l in (r.stdout + r.stderr).splitlines() if "d3d9" not in l)
    print(out[-tail:], flush=True)
    return out

for root, dirs, files in os.walk(src):
    dirs[:] = [d for d in dirs if d not in (".git", "out", "third_party", "build", "buildtools", "tools")]
    for f in files:
        if f.endswith((".gn", ".gni")):
            p = os.path.join(root, f)
            for i, line in enumerate(open(p, encoding="utf8", errors="replace"), 1):
                if re.search(r"swiftshader|libvulkan|vulkan_loader|icd", line, re.I):
                    print(f"{os.path.relpath(p, src)}:{i}: {line.rstrip()}")
sh(["gn" + B, "ls", outdir, "//third_party/SwiftShader/src/Vulkan:*"])
sh(["gn" + B, "ls", outdir, "//third_party/SwiftShader/*"], 3000)
for t in ("//third_party/vulkan-loader/src:libvulkan",):
    sh(["gn" + B, "desc", outdir, t, "outputs"])
out = sh(["ninja", "-C", outdir, "-t", "targets", "all"], 100)
print([l for l in out.splitlines() if re.search(r"swiftshader|icd|libvulkan|vulkan-1", l, re.I) and not l.startswith("obj/")][:40])
cmds = subprocess.run(["ninja", "-C", outdir, "-t", "commands", "-x", f"libEGL.{ext}"], cwd=src, capture_output=True, text=True).stdout.splitlines()
link = [c for c in cmds if re.search(r"-shared|-dynamiclib|link\.exe|lld-link", c)]
print("commands:", len(cmds), "link commands:", len(link))
objs = sorted({os.path.dirname(m) for c in link for m in re.findall(r"obj/[^\s\"']+", c)})
print("object dirs of libEGL:\n" + "\n".join(objs))

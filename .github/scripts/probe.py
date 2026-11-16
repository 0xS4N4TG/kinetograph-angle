"""Print what an ANGLE checkout says about SwiftShader, the Vulkan loader and licences (diagnostic, changes nothing)."""
import glob, os, subprocess, sys

src, outdir = sys.argv[1:3]
B = ".bat" if sys.platform == "win32" else ""

def sh(cmd):
    print("$", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=src, capture_output=True, text=True)
    print((r.stdout + r.stderr)[-6000:], flush=True)

for f in ("gni/angle.gni", "BUILD.gn"):
    for i, line in enumerate(open(os.path.join(src, f), encoding="utf8"), 1):
        if any(k in line.lower() for k in ("swiftshader", "custom_libvulkan", "vulkan_loader", "libvulkan")):
            print(f"{f}:{i}: {line.rstrip()}")
sh(["gn" + B, "args", outdir, "--list", "--short"])
for lab in ("//third_party/swiftshader/src/Vulkan:*", "//third_party/vulkan-loader/src:*", "//:*"):
    sh(["gn" + B, "ls", outdir, lab])
for t in ("//third_party/swiftshader/src/Vulkan:swiftshader_libvulkan", "//third_party/vulkan-loader/src:libvulkan"):
    sh(["gn" + B, "desc", outdir, t, "type", "outputs", "deps"])
lic = os.path.join(src, "tools/licenses")
print("tools/licenses:", os.listdir(lic) if os.path.isdir(lic) else None)
print("third_party:", sorted(os.listdir(os.path.join(src, "third_party"))))
print("READMEs:", sorted(os.path.relpath(p, src) for p in glob.glob(os.path.join(src, "third_party", "*", "README.chromium"))))

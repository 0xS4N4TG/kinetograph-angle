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

sh(["gn" + B, "ls", outdir, "//third_party/SwiftShader/src/Vulkan:*"])
sh(["gn" + B, "desc", outdir, "//third_party/SwiftShader/src/Vulkan:swiftshader_libvulkan", "outputs"])
sh(["gn" + B, "desc", outdir, "//third_party/SwiftShader/src/Vulkan:icd_file", "outputs"])
sh(["gn" + B, "desc", outdir, "//third_party/vulkan-loader/src:libvulkan", "outputs"])

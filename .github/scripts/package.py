"""Package the ANGLE libraries and SwiftShader: archive + SHA256SUMS-<platform>, and print what they link against."""
import hashlib, os, subprocess, sys, tarfile, zipfile, shutil, glob

src, gn_args_file, dist = sys.argv[1:4]
name, ext = os.environ["OS_NAME"], os.environ["EXT"]
sha = subprocess.check_output(["git", "-C", src, "rev-parse", "HEAD"], text=True).strip()
out = os.path.join(src, "out", "Release")
libs = {"darwin": ("libEGL.dylib", "libGLESv2.dylib"),
        "linux": ("libEGL.so", "libGLESv2.so"),
        "win32": ("libEGL.dll", "libGLESv2.dll")}[name.split("-")[0]]
# SwiftShader (ANGLE's Vulkan backend on a software driver) and what ANGLE needs to reach it. On macOS ANGLE links the
# Vulkan loader statically (angle_shared_libvulkan is false there), so no libvulkan is shipped.
extra = {"darwin": ("libvk_swiftshader.dylib", "vk_swiftshader_icd.json"),
         "linux": ("libvk_swiftshader.so", "vk_swiftshader_icd.json", "libvulkan.so.1"),
         "win32": ("vk_swiftshader.dll", "vk_swiftshader_icd.json", "vulkan-1.dll")}[name.split("-")[0]]

def sha256(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

def run(cmd):
    print("$", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout + r.stderr, flush=True)

for lib in libs:
    p = os.path.join(out, lib)
    print(f"{lib}: {os.path.getsize(p)} bytes")
    if name.startswith("darwin"):
        run(["otool", "-L", p])
    elif name.startswith("linux"):
        run(["ldd", p])
    else:
        dumpbin = glob.glob("C:/Program Files/Microsoft Visual Studio/2022/*/VC/Tools/MSVC/*/bin/Hostx64/x64/dumpbin.exe")
        run([dumpbin[0], "/dependents", p])
print("files in out/Release:", sorted(f for f in os.listdir(out) if f.endswith((".dll", ".so", ".dylib", ".json"))))
if name.startswith("win32"):
    print("d3dcompiler_47.dll produced:", os.path.exists(os.path.join(out, "d3dcompiler_47.dll")))

short = sha[:10]
for f in extra:
    assert os.path.exists(os.path.join(out, f)), f"{f} was not built"
    print(f"{f}: {os.path.getsize(os.path.join(out, f))} bytes")
notices = os.path.join(out, "THIRD-PARTY-NOTICES.txt")
targets = ["//:libEGL", "//:libGLESv2", "//third_party/SwiftShader/src/Vulkan:swiftshader_libvulkan"]
if not name.startswith("darwin"):
    targets.append("//third_party/vulkan-loader/src:libvulkan")
subprocess.check_call([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "notices.py"), src, "out/Release", notices, *targets])
stage = os.path.join("stage", f"angle-{short}-{name}")
os.makedirs(stage, exist_ok=True)
for lib in (*libs, *extra, "THIRD-PARTY-NOTICES.txt"):
    shutil.copy(os.path.join(out, lib), stage)
shutil.copy(os.path.join(src, "LICENSE"), os.path.join(stage, "LICENSE"))
with open(os.path.join(stage, "SOURCE.txt"), "w") as f:
    f.write(f"ANGLE commit: {sha}\nasked for: {os.environ['ANGLE_REF']}\nrunner image: {os.environ['IMAGE']}\n"
            f"gn args: {open(gn_args_file).read().strip()}\nsource: https://chromium.googlesource.com/angle/angle\n")

os.makedirs(dist, exist_ok=True)
archive = os.path.join(dist, f"angle-{short}-{name}.{ext}")
files = [*libs, *extra, "THIRD-PARTY-NOTICES.txt", "LICENSE", "SOURCE.txt"]
if ext == "zip":
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(os.path.join(stage, f), f)
else:
    with tarfile.open(archive, "w:gz") as t:
        for f in files:
            t.add(os.path.join(stage, f), f)
lines = [f"{sha256(archive)}  {os.path.basename(archive)}"]
lines += [f"{sha256(os.path.join(stage, l))}  {name}/{l}" for l in (*libs, *extra, "THIRD-PARTY-NOTICES.txt")]
open(os.path.join(dist, f"SHA256SUMS-{name}"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))

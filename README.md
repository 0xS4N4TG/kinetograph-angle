# kinetograph-angle

Builds of [ANGLE](https://chromium.googlesource.com/angle/angle) (`libEGL` and `libGLESv2`) for the
[Kinetograph](https://github.com/0xS4N4TG/kinetograph) video engine. Google ships no prebuilt ANGLE.

- `main` is Google's ANGLE source, untouched.
- This branch (`ci`, the default) holds only the workflows, a packaging script and the licence.

## Run a build

Actions, then "build", then "Run workflow". Or:

```sh
gh workflow run build.yml -f angle_ref=chromium/8103 -f release=false
```

`angle_ref` is a commit SHA or a branch of the upstream repository. It is resolved to a SHA once, and all three
platforms build that SHA: macOS arm64, Linux x64 and Windows x64. Each job uploads an archive as a workflow
artifact. With `release=true` a draft release `angle-<shortsha>` is created with the archives and `SHA256SUMS`;
publishing it is a manual step.

## Keeping up

`update.yml` runs weekly (and on demand). It fast-forwards `main` from `google/angle`, and if Chrome Stable's ANGLE
branch has no release yet, starts a build with `release=true` (a draft; publishing stays manual). GitHub switches off
scheduled workflows in a repository with no activity for 60 days; re-enable it in the Actions tab if that happens.

## Releases

See the [Releases](../../releases) page. Each archive holds the two libraries, ANGLE's `LICENSE` and a `SOURCE.txt`
(commit, gn args, runner image).

## Licence

The libraries are ANGLE, under its BSD 3-clause licence (`LICENSE`).

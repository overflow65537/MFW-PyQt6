# MFW Android deployment PoC

This directory is an isolated **Phase-0 Android deployment skeleton** for a
minimal PySide6 Qt Widgets application built with `pyside6-android-deploy`.
It does not import the repository's desktop `main.py` or existing desktop
`MainWindow`, so desktop startup and packaging behavior remain unchanged.

> Status: skeleton only. No APK/AAB has been produced in this workspace, and
> the MaaFramework native runtime is **not integrated**.

## Contents

- `main.py` - Android-only minimal Qt Widgets entry point.
- `android.pyproject` - explicit deployment file list.
- `requirements-android.txt` - intentionally minimal Android dependency list.
- `pysidedeploy.spec` - arm64 configuration seed with unfilled wheel paths.

## Scope of the first APK

The window reports Android/runtime detection, `sys.platform`, CPU architecture,
Python/PySide6/Qt versions and the Qt installation prefix. Its button runs a
basic Python/Qt smoke test. MaaFw is reported as skipped.

## Supported build host

Use **Linux**. On Windows, use WSL2 Ubuntu or a Linux CI runner. Building from a
Linux-native path is preferable to `/mnt/d/...` for performance and fewer
permission/path surprises in Gradle and Android tools.

Required tools:

1. A Python 3.11 virtual environment, aligned with the official PySide6 Android wheels.
2. JDK 21 with `JAVA_HOME` configured for the pinned Qt 6.11 toolchain.
3. Android SDK and an NDK version compatible with the selected Qt/PySide6 release.
4. Buildozer/python-for-android prerequisites.
5. `pyside6-android-deploy` from a desktop PySide6 installation.
6. Matching **Android aarch64** PySide6 and shiboken6 wheels.

Do not use desktop PyPI PySide6 wheels as Android target wheels. Download the
matching Android wheel pair from the official Qt for Python `pyside6` and
`shiboken6` release directories. For example, the pinned 6.11.1 CI uses:

```text
pyside6-6.11.1-6.11.1-cp311-cp311-android_aarch64.whl
shiboken6-6.11.1-6.11.1-cp311-cp311-android_aarch64.whl
```

The CI downloads these files directly because the open-source PySide6 wheel
installs `pyside6-android-deploy` but does not provide a `qtpip` executable.
Do not commit developer-specific absolute wheel, SDK or NDK paths.

## Initialize the deployment configuration

The checked-in `pysidedeploy.spec` follows the current Qt for Python section
layout, but intentionally contains wheel placeholders. The installed tool's
`--help` and generated configuration are authoritative for that PySide6
release.

To let the tool create a fresh configuration, temporarily move the checked-in
seed and run `--init`. Android wheels are still required during initialization:

```bash
cd android_app
mv pysidedeploy.spec pysidedeploy.spec.seed
pyside6-android-deploy --init \
  --name "mfwandroidpoc" \
  --wheel-pyside /absolute/path/to/PySide6-android-aarch64.whl \
  --wheel-shiboken /absolute/path/to/shiboken6-android-aarch64.whl \
  --ndk-path /absolute/path/to/android-ndk \
  --sdk-path /absolute/path/to/android-sdk
```

The SDK/NDK flags may be omitted when the installed tool detects its supported
cache. Compare the generated spec with `pysidedeploy.spec.seed` and retain:

- `project_dir = .` and `input_file = main.py`;
- `project_file = android.pyproject`;
- `modules = Core,Widgets`;
- `mode = debug`;
- `arch = aarch64` (Android/NDK name: `arm64-v8a`).

Restore the committed filename after merging the generated fields.

`pyside6-android-deploy` currently reuses `[app] title` as both Buildozer's
human-readable title and Android package identifier. Keep the committed value
lowercase ASCII alphanumeric without spaces (`mfwandroidpoc`); the Qt window
itself still displays the human-readable `MFW Android PoC` title.

## Inspect and build

With real wheel paths filled in locally, inspect the generated commands first:

```bash
cd android_app
pyside6-android-deploy --dry-run --config-file pysidedeploy.spec
```

Then build a debug APK:

```bash
pyside6-android-deploy --config-file pysidedeploy.spec
```

Use `--keep-deployment-files` when debugging generated Buildozer, Gradle or
python-for-android files. Generated outputs are ignored by repository-level
Android-specific `.gitignore` rules.


## GitHub Actions build

The independent `.github/workflows/android.yml` workflow validates and builds
this PoC without changing the existing desktop packaging workflow. It runs when
Android files or the workflow itself change on `main` pushes and pull requests,
and it can also be started manually with `workflow_dispatch`.

The CI toolchain is deliberately pinned as one compatible set:

- CPython 3.11.15 for both the Android target runtime and python-for-android hostpython;
- PySide6/shiboken6 Android aarch64 6.11.1 wheels;
- JDK 21;
- Android platform 36, minimum API 28 and Build Tools 36.0.0;
- Android NDK 27.2.12479018 (r27c);
- python-for-android develop commit `7af1d1325ef460def993cc7871c43d04bc877a94`.

The workflow installs and pins its deployment tools first, patches the Buildozer
template, and disables dependency reinstallation in the generated CI spec.
PySide6 6.11.1 generates an unversioned `python3` Buildozer requirement, while
the pinned python-for-android revision defaults to a newer CPython runtime. CI
therefore pins both `python3` and `hostpython3` to 3.11.15 so they match the
official `cp311` PySide6/shiboken6 Android wheels. It then downloads those
pinned official Android wheels directly from Qt,
creates an untracked `pysidedeploy.ci.spec` containing runner-specific
absolute paths, and also passes the SDK/NDK paths explicitly on the command
line. The explicit flags are required because PySide6 6.11.1 does not read
the NDK value from an already-existing config file on this code path. The
CLI help still mentions r26b, but Qt 6.11 officially requires r27c. Because
Buildozer 1.5.0 otherwise defaults to target API 31 and minimum API 21, CI
patches its generated-config template to target API 36 with minimum API 28.
PySide6 forces python-for-android's moving `develop` branch, so CI also pins
the selected commit through Buildozer's `p4a.commit` setting.
The CI then runs a deployment dry-run, builds the arm64 debug APK, and verifies
that the package contains `lib/arm64-v8a/libpython3.11.so` together with the
PySide6 and shiboken6 native libraries, with no conflicting versioned
`libpython` library. Only a package that passes this check is uploaded as the
`MFW-Android-PoC-arm64-debug` artifact. Deployment logs and the generated CI
spec are uploaded separately for diagnosis, including when the build fails.

The workflow currently builds only the minimal Qt shell. A green APK build does
not mean MaaFramework is available; MaaFramework native integration remains the
next Go/No-Go phase.

## Device smoke test

Install the first debug APK on an arm64 device and verify:

1. The window opens without importing desktop-only modules.
2. Platform information is visible.
3. The smoke-test button reports Python and Qt checks as PASS.
4. Logcat has no Qt plugin, missing shared-library or Python import errors.

## MaaFramework Go/No-Go phase

**This skeleton has not integrated MaaFw or its native runtime.** Do not add
`MaaFw` to `requirements-android.txt`: a desktop/manylinux wheel is not an
Android wheel.

After the Qt shell passes, deliberately package:

- the MaaFramework Python binding;
- `libMaaFramework.so` for `arm64-v8a`;
- `libMaaAndroidNativeControlUnit.so` for `arm64-v8a`;
- every matching transitive native dependency;
- a custom python-for-android recipe and/or `buildozer.local_libs` mapping.

Go/No-Go test order on a real device:

1. `import maa` succeeds.
2. The native loader reports the MaaFramework version.
3. `AndroidNativeController` can be created.
4. Screenshot succeeds.
5. Tap and swipe succeed.
6. A minimal Resource/Tasker pipeline executes.

Do not port the full desktop UI until this chain works. Expected blockers include
Android linker paths, ABI mismatches, transitive OpenCV/Boost/Maa libraries,
Android control permissions and device-specific behavior.

## Intentional exclusions

The Android dependency set excludes `keyboard`, `wmi`, `psutil` and
`MaaFw`. This phase also excludes qasync, Fluent Widgets, the desktop
single-instance guard, tray integration, updater, scheduler, ADB emulator scan,
external agent processes and desktop configuration/resource path handling. Add
each feature separately only after its Android behavior is validated.

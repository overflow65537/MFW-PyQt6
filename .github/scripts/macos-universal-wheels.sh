#!/usr/bin/env bash
set -euo pipefail

PACKAGES=("$@")
if [ ${#PACKAGES[@]} -eq 0 ]; then
  PACKAGES=(cffi numpy)
fi

ARCHS=(arm64 x86_64)
WORK_ROOT=".github/workflows/.universal-build"
BUILD_ROOT="$WORK_ROOT/build"
WHEEL_DIR="$WORK_ROOT/wheels"

rm -rf "$WORK_ROOT"
mkdir -p "$BUILD_ROOT" "$WHEEL_DIR"

for pkg in "${PACKAGES[@]}"; do
  echo "Building universal wheel for $pkg"
  declare -A wheel_paths
  declare -A unzip_dirs
  for arch in "${ARCHS[@]}"; do
    export ARCHFLAGS="-arch $arch"
    arch_build_dir="$BUILD_ROOT/${pkg}-${arch}"
    rm -rf "$arch_build_dir"
    mkdir -p "$arch_build_dir"
    python -m pip wheel --no-binary :all: "$pkg" -w "$arch_build_dir"
    wheel_paths["$arch"]="$(ls "$arch_build_dir"/*.whl | head -n 1)"
    if [ -z "${wheel_paths[$arch]:-}" ]; then
      echo "Failed to find wheel for $pkg ($arch)" >&2
      exit 1
    fi
    unzip_dir="$arch_build_dir/unzip"
    rm -rf "$unzip_dir"
    mkdir -p "$unzip_dir"
    unzip -q "${wheel_paths[$arch]}" -d "$unzip_dir"
    unzip_dirs["$arch"]="$unzip_dir"
  done

  universal_dir="$BUILD_ROOT/${pkg}-universal"
  rm -rf "$universal_dir"
  mkdir -p "$universal_dir"
  cp -R "${unzip_dirs[arm64]}/." "$universal_dir"

  declare -A rel_paths
  for arch in "${ARCHS[@]}"; do
    while IFS= read -r file; do
      rel="${file#"${unzip_dirs[$arch]}/"}"
      rel_paths["$rel"]=1
    done < <(find "${unzip_dirs[$arch]}" -type f)
  done

  for rel in "${!rel_paths[@]}"; do
    dest="$universal_dir/$rel"
    mkdir -p "$(dirname "$dest")"
    srcs=()
    for arch in "${ARCHS[@]}"; do
      candidate="${unzip_dirs[$arch]}/$rel"
      if [ -f "$candidate" ]; then
        srcs+=("$candidate")
      fi
    done
    if [ "${#srcs[@]}" -gt 1 ] && ([[ "$rel" == *.so ]] || [[ "$rel" == *.dylib ]]); then
      lipo -create "${srcs[@]}" -output "$dest"
    elif [ "${#srcs[@]}" -gt 0 ]; then
      cp -f "${srcs[0]}" "$dest"
    fi
  done

  base_name="$(basename "${wheel_paths[arm64]}")"
  universal_name="${base_name/_arm64.whl/_universal2.whl}"
  universal_name="${universal_name/_x86_64.whl/_universal2.whl}"
  pushd "$universal_dir" >/dev/null
  zip -qr "$WHEEL_DIR/$universal_name" .
  popd >/dev/null

  echo "Installing universal wheel $universal_name"
  python -m pip install "$WHEEL_DIR/$universal_name"
done


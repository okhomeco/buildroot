./flutter/tools/gn --ios --unoptimized --no-goma
./flutter/tools/gn --unoptimized --no-goma
./flutter/tools/gn --ios --unoptimized --no-goma --simulator --simulator-cpu=arm64
./flutter/tools/gn --ios --unoptimized --no-goma --runtime-mode=profile
./flutter/tools/gn --ios --unoptimized --no-goma --runtime-mode=release
./flutter/tools/gn --unoptimized --no-goma --runtime-mode=profile
./flutter/tools/gn --unoptimized --no-goma --runtime-mode=release

ninja -C out/ios_debug_unopt && ninja -C out/host_debug_unopt && ninja -C out/ios_debug_sim_unopt_arm64 && ninja -C out/ios_profile_unopt && ninja -C
out/host_profile_unopt && ninja -C out/ios_release_unopt && ninja -C out/host_release_unopt

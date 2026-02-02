set dotenv-load := true

default:
    @just --list

android-run: (android-cmd "deploy run logcat")

android-logcat: (android-cmd "logcat")

android-build: (android-cmd "debug")

android-emu:
    ~/Android/Sdk/emulator/emulator -avd Medium_Phone_2

android-cmd cmd:
    #!/usr/bin/env bash
    set -euxo pipefail
    docker run --privileged --interactive --tty --rm  --volume "$PWD":/home/user/hostcwd --volume "$HOME/.buildozer":/home/user/.buildozer --volume "$HOME/.gradle":/home/ubuntu/.gradle -e VIRTUAL_ENV=1 -v /dev/bus/usb:/dev/bus/usb  kivy/buildozer android {{cmd}}

pytest:
    #!/usr/bin/env bash
    set -euxo pipefail
    uv run -q pytest -q

adb-install:
    adb install bin/crazybot-0.2-arm64-v8a_armeabi-v7a-debug.apk

adb-logcat:
    adb logcat

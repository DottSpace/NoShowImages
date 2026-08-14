[app]
title = Snake 3310
package.name = snake3310
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav,ogg,ttf
version = 0.1
requirements = python3,pygame
orientation = portrait
fullscreen = 1

# Configurazioni Android stabili
android.accept_sdk_license = True
android.api = 33
android.minapi = 21
android.ndk = 25b

[buildozer]
log_level = 2
warn_on_root = 1

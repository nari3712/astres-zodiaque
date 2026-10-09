[app]
title = Astres Zodiaque
package.name = astreszodiaque
package.domain = org.astres
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,bsp
source.include_patterns = donnees_skyfield/*
version = 1.0
requirements = python3,kivy,numpy,skyfield,jplephem,sgp4,certifi
orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.api = 34
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1

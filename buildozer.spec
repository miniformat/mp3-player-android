[app]

title = 音乐播放器
package.name = mp3player
package.domain = org.music
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav,mp3,ogg
version = 1.0.0
requirements = python3,kivy,android,pyjnius,sdl2,ffpyplayer
orientation = portrait
fullscreen = 0
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,WAKE_LOCK
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.accept_sdk_license = True
android.gradle_dependencies = 
p4a.branch = master
icon.filename = icon.png
presplash.filename = presplash.png
presplash.color = #1a1a2e
whitelist = /sdcard/*

[buildozer]
log_level = 2
warn_on_root = 1

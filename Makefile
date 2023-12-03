all: test android-debug

.PHONY: all \
	debug test clean update_commit_sha \
	buildozer-docker-image \
	android-remove-apk android-run android-uninstall \
	android-debug android-release

CURRENT_COMMIT := $(shell git rev-parse HEAD | head -c6)
BUILD_TIME := $(shell date -u '+%Y-%m-%d %T')

update_build_info:
	sed -i "s/^__commit_sha__.*/__commit_sha__ = \"$(CURRENT_COMMIT)\"/" wkwallet/version.py
	sed -i "s/^__build_time__.*/__build_time__ = \"$(BUILD_TIME)\"/" wkwallet/version.py

use_debug_build:
	sed -i "s/^__build_type__.*/__build_type__ = \"debug\"/" wkwallet/version.py

use_release_build:
	sed -i "s/^__build_type__.*/__build_type__ = \"release\"/" wkwallet/version.py

#######################################################################################
# Development
#######################################################################################
debug:
	. venv/bin/activate && python wkwallet/main.py

test:
	. venv/bin/activate && pytest ./tests

clean:
	rm -rf .buildozer/android/platform/build-armeabi-v7a/dists/

#######################################################################################
# Buildozer
#######################################################################################
define run_buildozer
    $(eval $@_ENTRYPOINT = $(1))
    $(eval $@_BUILD_ARGS = $(2))

	docker run \
		-v "$(HOME)/.buildozer":/home/user/.buildozer \
		-v "$(HOME)/.gradle":/home/user/.gradle \
		-v "$(CURDIR)":/home/user/hostcwd \
		-v "$(CURDIR)/keystores":/home/user/hostcwd/keystores \
		-e P4A_DEBUG_KEYSTORE='/home/user/hostcwd/keystores/wkwallet_debug.keystore' \
		-e P4A_DEBUG_KEYSTORE_PASSWD='wkwallet_debug' \
		-e P4A_DEBUG_KEYALIAS_PASSWD='wkwallet_debug' \
		-e P4A_DEBUG_KEYALIAS='wkwallet_debug' \
		-it --rm \
		--entrypoint ${$@_ENTRYPOINT} \
		buildozer ${$@_BUILD_ARGS}
endef

buildozer-docker-image:
	if ! docker image ls |grep buildozer; then \
		docker build --tag=buildozer ./buildozer; \
	fi

buildozer-docker-bash:
	$(call run_buildozer, /bin/bash)

#######################################################################################
# Android
#######################################################################################
ANDROID_APK := $(wildcard bin/*.apk)

android-remove-apk:
ifneq (,$(ANDROID_APK))
	rm $(ANDROID_APK)
endif

android-debug: buildozer-docker-image android-remove-apk update_build_info use_debug_build
	@$(call run_buildozer, buildozer, -v android debug)
	git checkout HEAD wkwallet/version.py

android-release: buildozer-docker-image android-remove-apk update_build_info use_release_build
	@$(call run_buildozer, buildozer, -v android release)
	git checkout HEAD wkwallet/version.py

android-run: android-debug
	adb install $(ANDROID_APK)
	adb shell monkey -p com.bitcoinwukong.wkwallet -c android.intent.category.LAUNCHER 1
	adb logcat -s python

android-uninstall:
	adb uninstall "com.bitcoinwukong.wkwallet"

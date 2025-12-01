Finder Badge Overlay — Verification & QA

Pre-req:
- Replace placeholders in install/uninstall scripts with your extension bundle id.
- Build artifact expected under: build/Build/Products/Debug/*.appex

Build:
xcodebuild -workspace <YourWorkspace>.xcworkspace -scheme <YourScheme> -configuration Debug -derivedDataPath build clean build

Install:
./scripts/install_finder_extension.sh
killall Finder

Verify:
- List finder extensions: pluginkit -m -p com.apple.finder.sync
- Check extension: pluginkit -p <EXT_ID>
- Functional tests:
  1) mkdir ~/fs-overlay-test
  2) touch ~/fs-overlay-test/file{1..20}.txt
  3) Confirm badge appears for predicate-matched items.
  4) Modify a file: echo "x" >> ~/fs-overlay-test/file1.txt -> badge updates.
  5) Move file in/out -> badge toggles.

Stress test:
for i in {1..200}; do echo "u$i" >> ~/fs-overlay-test/file$(( (i % 20) + 1 )).txt; sleep 0.03; done

Logging:
- Console.app: filter by your extension bundle id for runtime logs.
- Save output of: pluginkit -m -p com.apple.finder.sync
- Capture Activity Monitor snapshot during stress test.

Acceptance criteria:
- Installer idempotent.
- Badge displays and updates reliably.
- No visual flicker under rapid events.
- CPU/memory acceptable under stress test.

Rollback:
./scripts/uninstall_finder_extension.sh
killall Finder

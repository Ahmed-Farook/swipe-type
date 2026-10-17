#!/usr/bin/env python3
"""
macOS Menu Bar Application for Laptop Swipe
Allows toggling Swipe Typing ON and OFF directly from the macOS status bar.
Supports automatic continuous swipe decoding, spacebar trigger, and Right Shift modifier.
"""

import sys
import time
import threading
import subprocess
import os
import traceback

import AppKit
import Quartz
from Foundation import NSObject
from pynput import keyboard

from decoder import decode_swipe, client

# Controller fallback
controller = keyboard.Controller()

# Configuration for Automatic Continuous Swipe Detection
SWIPE_PAUSE_TIMEOUT = 0.35   # 350ms pause after sliding finger triggers auto-decode
SWIPE_MIN_LENGTH = 3        # minimum letters to constitute a swipe
LOG_FILE = "/tmp/laptop_swipe.log"

# State
is_swipe_enabled = True
swipe_buffer = []          # [(char, timestamp), ...]
buffer_lock = threading.Lock()
pause_timer = None
suppressing_injection = False
last_key_time = 0.0
is_swiping_explicit = False
last_decoded_text = ""
app_delegate = None
listener = None


def log(msg: str):
    """Logs timestamped messages to /tmp/laptop_swipe.log and stdout."""
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass
    print(line)


def check_accessibility():
    """Checks if macOS Accessibility permission is granted, prompting the user if not."""
    try:
        import ApplicationServices
        trusted = ApplicationServices.AXIsProcessTrusted()
        if not trusted:
            log("⚠️  macOS Accessibility permission missing! Triggering prompt...")
            ApplicationServices.AXIsProcessTrustedWithOptions({
                ApplicationServices.kAXTrustedCheckOptionPrompt: True
            })
            
            # Show a native alert guiding the user to System Settings
            def _show_alert():
                try:
                    alert = AppKit.NSAlert.alloc().init()
                    alert.setMessageText_("Accessibility Permission Required")
                    alert.setInformativeText_(
                        "Laptop Swipe needs Accessibility and Input Monitoring permissions to detect swipe gestures and replace them with decoded words.\n\n"
                        "Please enable Laptop Swipe in:\n"
                        "System Settings -> Privacy & Security -> Accessibility\n"
                        "and Input Monitoring."
                    )
                    alert.addButtonWithTitle_("Open Accessibility Settings")
                    alert.addButtonWithTitle_("Later")
                    res = alert.runModal()
                    if res == AppKit.NSAlertFirstButtonReturn:
                        subprocess.run(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"])
                except Exception as ex:
                    log(f"Alert display error: {ex}")

            AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(_show_alert)
            return False
        return True
    except Exception as e:
        log(f"check_accessibility exception: {e}")
        return True


def process_and_replace(raw_stream: str, count_to_erase: int, add_space: bool = True):
    """Deletes noisy slide characters and inserts the clean decoded word."""
    global suppressing_injection
    if len(raw_stream) < SWIPE_MIN_LENGTH:
        return

    decoded = decode_swipe(raw_stream)
    if not decoded:
        log(f"No match found for stream: '{raw_stream}'")
        return

    # If the user typed the exact word, no need to replace
    if decoded.lower() == raw_stream.lower():
        log(f"Stream '{raw_stream}' exactly matches word '{decoded}'. No replace needed.")
        return

    log(f"✨ Decoded swipe: '{raw_stream}' -> '{decoded}' (erasing {count_to_erase} chars)")

    if app_delegate:
        app_delegate.notifyDecodedWord(decoded)

    suppressing_injection = True
    try:
        # Release shift states to prevent unintended uppercase injection or modifier interference
        controller.release(keyboard.Key.shift_r)
        controller.release(keyboard.Key.shift)
        time.sleep(0.02)

        # 1. Backspace exactly the noisy characters
        for _ in range(count_to_erase):
            controller.tap(keyboard.Key.backspace)
            time.sleep(0.01)

        time.sleep(0.03)

        # 2. Type clean decoded word + optional trailing space
        text_to_type = decoded + (" " if add_space else "")
        controller.type(text_to_type)
        time.sleep(0.06)
    except Exception as e:
        log(f"Error in process_and_replace: {e}\n{traceback.format_exc()}")
    finally:
        suppressing_injection = False


def on_pause_timeout():
    """Triggered when the user pauses after sliding across keys."""
    global swipe_buffer, pause_timer
    with buffer_lock:
        pause_timer = None
        if len(swipe_buffer) >= SWIPE_MIN_LENGTH:
            raw = "".join(c for c, _ in swipe_buffer)
            swipe_buffer = []
            log(f"Pause timer triggered on stream: '{raw}'")
            threading.Thread(target=process_and_replace, args=(raw, len(raw), True), daemon=True).start()
        else:
            swipe_buffer = []


def on_press(key):
    global is_swiping_explicit, swipe_buffer, pause_timer, last_key_time
    if not is_swipe_enabled or suppressing_injection:
        return

    now = time.time()

    # Right Shift modifier
    if key == keyboard.Key.shift_r:
        is_swiping_explicit = True
        return

    # Spacebar triggers immediate decoding of swiped burst
    if key == keyboard.Key.space:
        with buffer_lock:
            if pause_timer:
                pause_timer.cancel()
                pause_timer = None
            if len(swipe_buffer) >= SWIPE_MIN_LENGTH:
                raw = "".join(c for c, _ in swipe_buffer)
                swipe_buffer = []
                log(f"Spacebar triggered on stream: '{raw}'")
                threading.Thread(target=process_and_replace, args=(raw, len(raw) + 1, True), daemon=True).start()
            else:
                swipe_buffer = []
        return

    # Word boundaries and resets
    if key in (keyboard.Key.backspace, keyboard.Key.enter, keyboard.Key.esc, keyboard.Key.tab):
        with buffer_lock:
            if pause_timer:
                pause_timer.cancel()
                pause_timer = None
            swipe_buffer = []
        return

    # Check for letter characters
    try:
        char = key.char
        if char and char.isalpha():
            char = char.lower()
            with buffer_lock:
                # If a long pause occurred (> 0.45s) since last key, flush previous buffer
                if swipe_buffer and (now - last_key_time > 0.45):
                    if pause_timer:
                        pause_timer.cancel()
                        pause_timer = None
                    if len(swipe_buffer) >= SWIPE_MIN_LENGTH:
                        prev_raw = "".join(c for c, _ in swipe_buffer)
                        threading.Thread(target=process_and_replace, args=(prev_raw, len(prev_raw), True), daemon=True).start()
                    swipe_buffer = []

                swipe_buffer.append((char, now))
                last_key_time = now

                # Reset pause timer
                if pause_timer:
                    pause_timer.cancel()
                pause_timer = threading.Timer(SWIPE_PAUSE_TIMEOUT, on_pause_timeout)
                pause_timer.start()
    except AttributeError:
        pass


def on_release(key):
    global is_swiping_explicit, swipe_buffer, pause_timer
    if not is_swipe_enabled or suppressing_injection:
        return

    # If Right Shift was explicitly released
    if key == keyboard.Key.shift_r and is_swiping_explicit:
        is_swiping_explicit = False
        with buffer_lock:
            if pause_timer:
                pause_timer.cancel()
                pause_timer = None
            if len(swipe_buffer) >= SWIPE_MIN_LENGTH:
                raw = "".join(c for c, _ in swipe_buffer)
                swipe_buffer = []
                log(f"Right Shift release triggered on stream: '{raw}'")
                threading.Thread(target=process_and_replace, args=(raw, len(raw), True), daemon=True).start()
            else:
                swipe_buffer = []

    if key == keyboard.Key.esc and not app_delegate:
        log("Exiting...")
        return False


import objc

class MenuBarDelegate(NSObject):
    def toggleSwipe_(self, sender):
        global is_swipe_enabled
        is_swipe_enabled = not is_swipe_enabled
        self.updateUI()
        log(f"Menu Bar: Swipe Typing toggled -> {'ON' if is_swipe_enabled else 'OFF'}")

    def validateMenuItem_(self, item):
        return True

    @objc.python_method
    def updateUI(self):
        if is_swipe_enabled:
            self.status_item.button().setTitle_("⌨️ ON")
            self.status_header.setTitle_("🟢 Swipe Typing: Active")
            self.toggle_item.setTitle_("Turn OFF")
            self.toggle_item.setState_(AppKit.NSControlStateValueOn)
        else:
            self.status_item.button().setTitle_("⌨️ OFF")
            self.status_header.setTitle_("⚪ Swipe Typing: Disabled")
            self.toggle_item.setTitle_("Turn ON")
            self.toggle_item.setState_(AppKit.NSControlStateValueOff)
        self.toggle_item.setEnabled_(True)

    @objc.python_method
    def notifyDecodedWord(self, word):
        def _update():
            if self.last_word_item:
                self.last_word_item.setTitle_(f'Last Swiped: "{word}"')

        AppKit.NSOperationQueue.mainQueue().addOperationWithBlock_(_update)

    def openAccessibilitySettings_(self, sender):
        subprocess.run(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"])

    def toggleLaunchAtLogin_(self, sender):
        plist_path = os.path.expanduser("~/Library/LaunchAgents/com.laptopswipe.mac.plist")
        if os.path.exists(plist_path):
            try:
                os.remove(plist_path)
            except Exception:
                pass
            self.login_item.setState_(AppKit.NSControlStateValueOff)
            log("Launch at Login disabled")
        else:
            bundle_path = "/Applications/Laptop Swipe.app"
            if not os.path.exists(bundle_path):
                workspace_app = os.path.abspath("dist/Laptop Swipe.app")
                if os.path.exists(workspace_app):
                    bundle_path = workspace_app

            plist_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.laptopswipe.mac</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/open</string>
        <string>{bundle_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
"""
            try:
                os.makedirs(os.path.dirname(plist_path), exist_ok=True)
                with open(plist_path, "w") as f:
                    f.write(plist_xml)
                self.login_item.setState_(AppKit.NSControlStateValueOn)
                log(f"Launch at Login enabled for: {bundle_path}")
            except Exception as e:
                log(f"Error setting Launch at Login: {e}")

    def quitApp_(self, sender):
        global listener
        log("Quitting Laptop Swipe Menu Bar App...")
        if listener:
            listener.stop()
        AppKit.NSApplication.sharedApplication().terminate_(self)


def start_menubar_app():
    global app_delegate, listener

    log("=== Starting MacBook Swipe Menu Bar App ===")
    trusted = check_accessibility()
    if not trusted:
        log("⚠️  macOS Accessibility permission needed. Opening System Settings...")

    # Initialize NSApplication as an accessory (menu bar only, no dock icon)
    app = AppKit.NSApplication.sharedApplication()
    app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)

    # Setup Status Bar Item
    status_bar = AppKit.NSStatusBar.systemStatusBar()
    status_item = status_bar.statusItemWithLength_(AppKit.NSVariableStatusItemLength)
    status_item.button().setTitle_("⌨️ ON")

    # Build Menu
    menu = AppKit.NSMenu.alloc().init()
    menu.setAutoenablesItems_(False)

    delegate = MenuBarDelegate.alloc().init()
    delegate.status_item = status_item
    app_delegate = delegate

    # 1. Header showing current state
    header_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("🟢 Swipe Typing: Active", None, "")
    header_item.setEnabled_(False)
    delegate.status_header = header_item
    menu.addItem_(header_item)

    # 2. Main Toggle Button (with shortcut Cmd+Option+S)
    toggle_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Turn OFF", "toggleSwipe:", "s")
    toggle_item.setKeyEquivalentModifierMask_(AppKit.NSEventModifierFlagCommand | AppKit.NSEventModifierFlagOption)
    toggle_item.setTarget_(delegate)
    toggle_item.setEnabled_(True)
    toggle_item.setState_(AppKit.NSControlStateValueOn)
    delegate.toggle_item = toggle_item
    menu.addItem_(toggle_item)

    menu.addItem_(AppKit.NSMenuItem.separatorItem())

    # 3. Dynamic Last Swiped Word
    last_word_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Last Swiped: (none yet)", None, "")
    last_word_item.setEnabled_(False)
    delegate.last_word_item = last_word_item
    menu.addItem_(last_word_item)

    # 4. Mode Indicator (Offline or Gemini AI)
    mode_text = "Mode: AI Enabled (Gemini 2.5)" if client else "Mode: Offline (9,250+ common words)"
    mode_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(mode_text, None, "")
    mode_item.setEnabled_(False)
    delegate.mode_item = mode_item
    menu.addItem_(mode_item)

    menu.addItem_(AppKit.NSMenuItem.separatorItem())

    # 5. Instructions & Accessibility Shortcut
    instructions_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        "Usage: Slide across keys & pause (or hit Space)", None, ""
    )
    instructions_item.setEnabled_(False)
    menu.addItem_(instructions_item)

    acc_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        "Accessibility Settings...", "openAccessibilitySettings:", ""
    )
    acc_item.setTarget_(delegate)
    acc_item.setEnabled_(True)
    menu.addItem_(acc_item)

    # 6. Launch at Login
    login_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        "Launch at Login", "toggleLaunchAtLogin:", ""
    )
    login_item.setTarget_(delegate)
    login_item.setEnabled_(True)
    login_agent_path = os.path.expanduser("~/Library/LaunchAgents/com.laptopswipe.mac.plist")
    login_item.setState_(AppKit.NSControlStateValueOn if os.path.exists(login_agent_path) else AppKit.NSControlStateValueOff)
    delegate.login_item = login_item
    menu.addItem_(login_item)

    menu.addItem_(AppKit.NSMenuItem.separatorItem())

    # 7. Quit App
    quit_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Quit Laptop Swipe", "quitApp:", "q")
    quit_item.setTarget_(delegate)
    quit_item.setEnabled_(True)
    menu.addItem_(quit_item)

    status_item.setMenu_(menu)

    # Start pynput keyboard listener in background daemon thread
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.daemon = True
    listener.start()

    log("Menu Bar item installed. Look for '⌨️ ON' in your top menu bar!")
    log("Continuous swipe typing active. Slide across keys and pause or press Spacebar.")

    # Start Cocoa Run Loop
    app.run()


if __name__ == "__main__":
    if "--test-perm" in sys.argv:
        trusted = check_accessibility()
        print(f"AXIsProcessTrusted: {trusted}")
        sys.exit(0)
    start_menubar_app()

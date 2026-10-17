import time
from pynput import keyboard
from decoder import decode_swipe

controller = keyboard.Controller()

is_swiping = False
swipe_buffer = []
suppressing_injection = False

def replace_noisy_text(raw_count: int, clean_text: str):
    """Deletes the noisy characters on screen and types the decoded output (macOS optimized)."""
    global suppressing_injection
    suppressing_injection = True

    # Ensure Right Shift state is released so injected text isn't uppercase
    controller.release(keyboard.Key.shift_r)
    time.sleep(0.04)

    # 1. Remove the raw characters that appeared while sliding your finger
    for _ in range(raw_count):
        controller.tap(keyboard.Key.backspace)
        time.sleep(0.01)  # Tuned for macOS Quartz event queue

    time.sleep(0.02)
    # 2. Type the clean decoded word/phrase + trailing space
    controller.type(clean_text + " ")
    time.sleep(0.05)
    suppressing_injection = False

def on_press(key):
    global is_swiping, swipe_buffer
    if suppressing_injection:
        return

    # Start listening for a swipe when RIGHT SHIFT is held down on MacBook
    if key == keyboard.Key.shift_r:
        if not is_swiping:
            is_swiping = True
            swipe_buffer = []
        return

    # Record characters while Right Shift is held
    if is_swiping:
        try:
            if key.char and key.char.isalpha():
                swipe_buffer.append(key.char.lower())
        except AttributeError:
            pass

def on_release(key):
    global is_swiping, swipe_buffer
    if suppressing_injection:
        return

    # Stop swiping when Right Shift is released -> Decode & Replace!
    if key == keyboard.Key.shift_r and is_swiping:
        is_swiping = False
        raw_swipe = "".join(swipe_buffer)
        
        # Only decode if 3+ keys were slid across (so normal Shift + 1 letter capitals still work!)
        if len(raw_swipe) >= 3:
            print(f"\nRaw stream captured: {raw_swipe}")
            decoded = decode_swipe(raw_swipe)
            print(f"Decoded output:      {decoded}")
            replace_noisy_text(len(raw_swipe), decoded)

    # Press ESC to quit the app
    if key == keyboard.Key.esc:
        print("Exiting MacBook Swipe App...")
        return False

def check_accessibility():
    """Checks if macOS Accessibility permission is granted, prompting the user if not."""
    try:
        import ApplicationServices
        if not ApplicationServices.AXIsProcessTrusted():
            print("\n⚠️  [ACTION REQUIRED] macOS Accessibility Permission Missing!")
            print("macOS requires Accessibility permission to backspace noisy keys and type decoded words.")
            print("Opening macOS permission prompt now...")
            ApplicationServices.AXIsProcessTrustedWithOptions({
                ApplicationServices.kAXTrustedCheckOptionPrompt: True
            })
            print("👉 Please enable 'Antigravity IDE' (or your Terminal app) in:")
            print("   System Settings -> Privacy & Security -> Accessibility\n")
            return False
        return True
    except Exception:
        return True

def run_cli():
    print("=== MacBook AI Swipe Keyboard (CLI Mode) ===")
    check_accessibility()
    print("Instructions:")
    print("1. Ensure Accessibility & Input Monitoring permissions are enabled for your IDE/Terminal.")
    print("2. Hold RIGHT SHIFT, slide your finger across 3+ keys, then release RIGHT SHIFT.")
    print("   (Pressing Right Shift + 1 letter still types a normal capital letter!)")
    print("3. Press ESC at any time to quit.\n")
    
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

if __name__ == "__main__":
    import sys
    if "--cli" in sys.argv:
        run_cli()
    else:
        from menubar_app import start_menubar_app
        start_menubar_app()

from spatial_engine import deduplicate_stream, extract_anchor_keys
from decoder import decode_swipe

def run_tests():
    samples = [
        "hgrertyhjklo",        # hello
        "thgrere",             # there
        "pytrhjon",            # python
        "swqipre",             # swipe
        "mkoiuytre",           # more (was previously 'moe')
        "crazxdfty",           # crazy (was previously 'crafty')
        "lonbfderhjklkuy",     # lonely (was previously 'looney')
        "dsaxcvbnmn",          # damn
        "ghoiugfasdtyred",     # good
    ]
    print("=== Running Offline/AI Decoder Verification (macOS Build) ===")
    for s in samples:
        dedup = deduplicate_stream(s)
        anchors = extract_anchor_keys(s)
        decoded = decode_swipe(s)
        print(f"Raw: {s:<22} | Dedup: {dedup:<16} | Anchors: {anchors:<10} | Decoded: {decoded}")

if __name__ == "__main__":
    run_tests()

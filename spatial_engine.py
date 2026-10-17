import math

# Physical (X, Y) coordinates of a standard staggered QWERTY layout
QWERTY_MAP = {
    'q': (0.0, 0), 'w': (1.0, 0), 'e': (2.0, 0), 'r': (3.0, 0), 't': (4.0, 0),
    'y': (5.0, 0), 'u': (6.0, 0), 'i': (7.0, 0), 'o': (8.0, 0), 'p': (9.0, 0),
    'a': (0.25, 1), 's': (1.25, 1), 'd': (2.25, 1), 'f': (3.25, 1), 'g': (4.25, 1),
    'h': (5.25, 1), 'j': (6.25, 1), 'k': (7.25, 1), 'l': (8.25, 1),
    'z': (0.75, 2), 'x': (1.75, 2), 'c': (2.75, 2), 'v': (3.75, 2), 'b': (4.75, 2),
    'n': (5.75, 2), 'm': (6.75, 2)
}

def deduplicate_stream(raw_swipe: str) -> str:
    """Removes immediate duplicate triggers if a key bounced."""
    cleaned = []
    for char in raw_swipe.lower():
        if char in QWERTY_MAP and (not cleaned or cleaned[-1] != char):
            cleaned.append(char)
    return "".join(cleaned)

def extract_anchor_keys(swipe_str: str) -> str:
    """
    Finds the start key, end key, and any key where the finger 
    made a sharp turn (inflection point) on the physical keyboard.
    """
    s = deduplicate_stream(swipe_str)
    if len(s) <= 2:
        return s

    anchors = [s[0]]
    for i in range(1, len(s) - 1):
        p_prev = QWERTY_MAP[s[i - 1]]
        p_curr = QWERTY_MAP[s[i]]
        p_next = QWERTY_MAP[s[i + 1]]

        # Vectors between consecutive keys
        v1 = (p_curr[0] - p_prev[0], p_curr[1] - p_prev[1])
        v2 = (p_next[0] - p_curr[0], p_next[1] - p_curr[1])

        mag1 = math.hypot(*v1)
        mag2 = math.hypot(*v2)

        if mag1 > 0 and mag2 > 0:
            cos_angle = (v1[0]*v2[0] + v1[1]*v2[1]) / (mag1 * mag2)
            cos_angle = max(-1.0, min(1.0, cos_angle))
            angle_deg = math.degrees(math.acos(cos_angle))

            # If the finger turns by more than 45 degrees, it's likely an intentional target letter
            if angle_deg > 45:
                anchors.append(s[i])

    anchors.append(s[-1])
    return "".join(anchors)

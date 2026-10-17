import os
from spatial_engine import deduplicate_stream, extract_anchor_keys

# Load frequency-ranked common words
try:
    from common_words import COMMON_WORDS, WORD_RANKS
except ImportError:
    COMMON_WORDS = ["hello", "there", "world", "python", "keyboard", "swipe", "typing"]
    WORD_RANKS = {w: i for i, w in enumerate(COMMON_WORDS)}

# Optional: Load Gemini client if GEMINI_API_KEY is set in environment
try:
    from google import genai
    client = genai.Client() if os.environ.get("GEMINI_API_KEY") else None
except ImportError:
    client = None

def load_system_dictionary():
    """Loads system dictionary words if available on macOS/Linux as a Tier 3 fallback."""
    dict_paths = ["/usr/share/dict/words", "/usr/dict/words"]
    words = set()
    for path in dict_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        w = line.strip().lower()
                        if w.isalpha() and 2 <= len(w) <= 15:
                            words.add(w)
                break
            except Exception:
                pass
    return list(words)

VOCABULARY = load_system_dictionary()
TOTAL_COMMON = len(COMMON_WORDS)

def is_exact_subsequence(collapsed_word: str, stream: str) -> bool:
    """Checks if collapsed_word characters appear in order inside stream."""
    it = iter(stream)
    return all(c in it for c in collapsed_word)

def lcs_length(s1: str, s2: str) -> int:
    """Longest Common Subsequence length for fuzzy matching."""
    m, n = len(s1), len(s2)
    dp = [0] * (n + 1)
    for i in range(1, m + 1):
        prev = 0
        for j in range(1, n + 1):
            temp = dp[j]
            if s1[i - 1] == s2[j - 1]:
                dp[j] = prev + 1
            else:
                dp[j] = max(dp[j], dp[j - 1])
            prev = temp
    return dp[n]

def score_word_match(word: str, stream: str, anchors: str, is_common: bool = True) -> float:
    """Computes a multi-factor match score for a candidate word against the swiped stream."""
    # Collapse consecutive identical letters (e.g. 'hello' -> 'helo')
    collapsed = []
    for ch in word:
        if not collapsed or collapsed[-1] != ch:
            collapsed.append(ch)
    collapsed_str = "".join(collapsed)

    is_sub = is_exact_subsequence(collapsed_str, stream)
    missing = 0
    if not is_sub:
        # If the word is at least 6 letters, tolerate 1 skipped key
        if len(collapsed_str) >= 6:
            lcs = lcs_length(collapsed_str, stream)
            if len(collapsed_str) - lcs <= 1:
                missing = 1
            else:
                return -999.0
        else:
            return -999.0

    score = 0.0

    # 1. Start key alignment (exact start gets high confidence)
    if word[0] == stream[0]:
        score += 45.0
    elif len(stream) > 1 and word[0] == stream[1]:
        score += 8.0
    else:
        return -999.0

    # 2. End key alignment (exact end gets high confidence)
    if word[-1] == stream[-1]:
        score += 45.0
    elif len(stream) > 1 and word[-1] == stream[-2]:
        score += 8.0
    else:
        return -999.0

    # 3. Anchor inflection point matching
    for a in anchors:
        if a in word:
            score += 15.0
        else:
            score -= 12.0  # Penalize missing an intentional geometric turn

    # Disallow tiny 2-letter words on long swipe gestures
    if len(word) <= 2 and len(stream) >= 5:
        return -999.0

    # 4. Stream coverage bonus (prefer words that account for more swiped letters)
    coverage = len(word) / max(1, len(stream))
    score += coverage * 60.0

    # 5. Length difference penalty relative to anchors
    score -= abs(len(word) - len(anchors)) * 2.0

    # 6. Fuzzy penalty if 1 char missed
    if missing > 0:
        score -= 35.0

    # 7. Continuous inverse-rank frequency priority (highest priority to top everyday words)
    rank = WORD_RANKS.get(word)
    if is_common and rank is not None:
        # Smooth non-linear priority curve:
        # Top 100 words: ~100-140 pts
        # Top 500 words: ~65-95 pts
        # Top 1500 words: ~35-65 pts
        # Rare words: < 15 pts
        freq_bonus = 140.0 / (1.0 + (rank / 250.0))
        score += freq_bonus
    else:
        # System dictionary rare word penalty
        score -= 60.0

    # 8. Exact match boost (if the swiped stream exactly matches the candidate, high confidence)
    if stream.lower() == word.lower():
        score += 100.0

    return score

def decode_swipe(raw_swipe: str) -> str:
    stream = deduplicate_stream(raw_swipe)
    if not stream:
        return ""

    anchors = extract_anchor_keys(stream)

    # Tier 1: If Gemini API key is configured, use AI for multi-word & noisy sentence decoding
    if client:
        prompt = (
            "You are a physical QWERTY keyboard swipe-to-text decoder. "
            "The user slid their finger across the laptop keys, generating a noisy stream of letters.\n"
            f"Raw key stream: '{stream}'\n"
            f"Detected finger inflection points (high-probability letters): '{anchors}'\n"
            "Task: Remove the intermediate brushed keys, restore any double letters (like 'll' in 'hello'), "
            "and split into spaces if multiple words were swiped together.\n"
            "Return ONLY the final decoded lowercase text with no quotes or explanation."
        )
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            print(f"[AI Fallback triggered]: {e}")

    # Tier 2: Frequency-Ranked Common Vocabulary Matching (Single Intended Word)
    candidates = []
    stream_starts = {stream[0]}
    if len(stream) > 1:
        stream_starts.add(stream[1])
    stream_ends = {stream[-1]}
    if len(stream) > 1:
        stream_ends.add(stream[-2])

    for word in COMMON_WORDS:
        if word[0] in stream_starts and word[-1] in stream_ends:
            score = score_word_match(word, stream, anchors, is_common=True)
            if score > 0:
                candidates.append((score, word))

    # If high-confidence common word found, return top choice immediately
    if candidates:
        candidates.sort(reverse=True)
        if candidates[0][0] >= 50.0:
            return candidates[0][1]

    # Tier 3: Rare System Dictionary Fallback (only if no common word matched)
    for word in VOCABULARY:
        if word[0] in stream_starts and word[-1] in stream_ends:
            score = score_word_match(word, stream, anchors, is_common=False)
            if score > 0:
                candidates.append((score, word))

    if candidates:
        candidates.sort(reverse=True)
        return candidates[0][1]

    # If nothing matched, return the geometric anchor keys
    return anchors

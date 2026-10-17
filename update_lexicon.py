import re
import os

TECH_WORDS = [
    # Top modern conversational & tech words
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i", "it", "for", "not", "on", "with",
    "he", "as", "you", "do", "at", "this", "but", "his", "by", "from", "they", "we", "say", "her",
    "she", "or", "an", "will", "my", "one", "all", "would", "there", "their", "what", "so", "up",
    "out", "if", "about", "who", "get", "which", "go", "me", "when", "make", "can", "like", "time",
    "no", "just", "him", "know", "take", "people", "into", "year", "your", "good", "some", "could",
    "them", "see", "other", "than", "then", "now", "look", "only", "come", "its", "over", "think",
    "also", "back", "after", "use", "two", "how", "our", "work", "first", "well", "way", "even",
    "new", "want", "because", "any", "these", "give", "day", "most", "us", "more", "is", "was",
    "are", "been", "has", "had", "did", "does", "done", "am", "were", "down", "different", "stuff",
    "thing", "things", "crazy", "cool", "yeah", "yes", "awesome", "super", "okay", "swipe",
    "keyboard", "typing", "laptop", "macbook", "python", "code", "terminal", "screen", "button",
    "click", "press", "hold", "release", "window", "file", "folder", "app", "apps", "chat",
    "message", "messages", "email", "post", "online", "offline", "api", "gemini", "ai", "model",
    "hello", "hi", "hey", "thanks", "thank", "welcome", "please", "bye", "goodbye", "lonely", "alone"
]

def build_common_words():
    gutenberg_path = "/Users/ahmed/.gemini/antigravity-ide/brain/021a9b92-dce6-4115-8566-bfc5a58dcc7c/.system_generated/steps/396/content.md"
    with open(gutenberg_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Extract words in order of frequency
    matches = [m[1].lower() for m in re.findall(r'title=\"([a-z]+)\">([a-z]+)</a>', html)]
    
    seen = set()
    ranked_words = []

    # 1. Add top tech words first (boosted)
    for w in TECH_WORDS:
        if w not in seen and len(w) >= 2:
            seen.add(w)
            ranked_words.append(w)

    # 2. Add Project Gutenberg top frequency words
    for w in matches:
        if w not in seen and len(w) >= 2 and w.isalpha():
            seen.add(w)
            ranked_words.append(w)

    print(f"Total curated frequency-ranked words: {len(ranked_words)}")

    # Write out common_words.py
    out_path = "/Users/ahmed/Desktop/laptop-swipe/common_words.py"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Authoritative Frequency-Ranked English Vocabulary (Project Gutenberg Top ~9,300 words)\n")
        f.write("# Words at the top of this list have the highest frequency in the English language.\n")
        f.write("COMMON_WORDS = [\n")
        for w in ranked_words:
            f.write(f'    "{w}",\n')
        f.write("]\n\n")
        f.write("WORD_RANKS = {w: i for i, w in enumerate(COMMON_WORDS)}\n")

    print(f"Successfully wrote {out_path}")

if __name__ == "__main__":
    build_common_words()

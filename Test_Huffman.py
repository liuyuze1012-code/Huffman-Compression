"""
Tests for Huffman_Compression.py

Compresses each sample to a file, decompresses it back, and checks the result
is identical to what went in. Also checks the code table is prefix-free, which
is what makes the bit stream decodable without separators.

Run:  python3 Test_Huffman.py
"""

import os
import shutil
import tempfile

import Huffman_Compression as huff


CASES = {
    "abracadabra":      "abracadabra",
    "with newline":     "abracadabra\n",
    "two characters":   "abababab",
    "english sentence": "the quick brown fox jumps over the lazy dog",
    "repeated text":    "hello world! " * 50,
    "punctuation":      "a,b.c!d?e;f:g",
    "unicode":          "café naïve résumé",
    "all identical":    "aaaaaaaa",
    "single character": "x",
    "empty file":       "",
}


def roundtrip(content, workdir):
    """Write, compress, decompress. Returns (restored text, before, after)."""
    src = os.path.join(workdir, "in.txt")
    enc = os.path.join(workdir, "in.huff")
    dst = os.path.join(workdir, "out.txt")

    open(src, "w").write(content)
    huff.compress(src, enc)
    huff.decompress(enc, dst)

    return open(dst).read(), os.path.getsize(src), os.path.getsize(enc)


def prefix_free(codes):
    """No code may be the start of another, or decoding is ambiguous."""
    values = list(codes.values())
    return all(
        not a.startswith(b)
        for a in values
        for b in values
        if a is not b
    )


def check(content, workdir):
    try:
        restored, before, after = roundtrip(content, workdir)
    except Exception as e:
        return None, None, f"{type(e).__name__}: {e}"

    if restored != content:
        return before, after, f"round trip failed: got {restored[:30]!r}"

    if content:
        codes = huff.build_codes(huff.build_tree(content))
        if not prefix_free(codes):
            return before, after, "codes are not prefix-free"
        if sorted(codes) != sorted(set(content)):
            return before, after, "code table does not cover every character"

    return before, after, "ok"


def main():
    workdir = tempfile.mkdtemp()
    try:
        print(f"{'case':20} {'before':>8} {'after':>8} {'ratio':>7}  result")
        print("-" * 68)

        passed = failed = 0
        for name, content in CASES.items():
            before, after, note = check(content, workdir)

            if note == "ok":
                passed += 1
                ratio = f"{after * 100 // before}%" if before else "-"
                print(f"{name:20} {before:>7}B {after:>7}B {ratio:>7}  ok")
            else:
                failed += 1
                print(f"{name:20} {'':>8} {'':>8} {'':>7}  FAIL  {note}")

        print()
        print(f"{passed} passed, {failed} failed")
        return failed
    finally:
        shutil.rmtree(workdir)


if __name__ == "__main__":
    raise SystemExit(1 if main() else 0)
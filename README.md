# Huffman File Compressor

A file compressor built from scratch in Python, implementing **Huffman coding** —
the entropy-encoding stage used inside DEFLATE (ZIP, PNG), JPEG and MP3.

No external dependencies. Works on any file, text or binary.

## Usage

```bash
python3 huffman.py -c input.txt  input.huff     # compress
python3 huffman.py -d input.huff restored.txt   # decompress
```

```bash
$ python3 huffman.py -c book.txt book.huff
book.txt: 18000 -> 10086 bytes (44% smaller)
```

## How it works

Fixed-width encoding wastes space: ASCII spends 8 bits on `e` (very common) and
8 bits on `z` (rare). Huffman gives frequent bytes short codes and rare bytes
long ones.

**1. Count** how often each byte appears.

**2. Build a tree** by repeatedly merging the two rarest nodes into a parent
whose count is their sum. Rare bytes get merged early and sink deep; common
bytes get merged last and stay near the root.

**3. Read the codes off the tree.** Going left appends `0`, going right appends
`1`. The path from root to a leaf *is* that byte's code.

For `"abracadabra"`:

```
              [11]
            0/     \1
         [a:5]      [6]
                  0/    \1
               [2]       [4]
              0/ \1     0/ \1
            [c] [d]   [b] [r]

   a -> 0      (1 bit,  appears 5x)
   c -> 100    (3 bits, appears 1x)
   d -> 101
   b -> 110
   r -> 111

   88 bits -> 23 bits
```

**4. Decode** by walking the tree with the bits as directions. Because every
byte sits at a *leaf*, no code is a prefix of another — so the bit stream is
unambiguous without any separators.

## File format

```
   [padding]  [serialized tree]  [encoded data]  [padding zeros]
    1 byte        variable          variable
```

Two details that make it work on disk:

**Padding.** Bit counts rarely divide evenly by 8. The stream is padded to a
byte boundary and the number of fake bits is stored in byte 0, so decompression
can strip them off. Without it, decoding emits a phantom byte at the end.

**The tree goes in the file.** The decompressor needs the same tree, so it is
serialized pre-order into the header: `1` plus 8 bits for a leaf, `0` plus both
subtrees for a branch. `deserialize` returns both the rebuilt node and the index
it stopped at, so the caller knows where the next subtree begins.

## Results

```
case                     before    after   ratio   round trip
------------------------------------------------------------
empty file                    0        0       -      ok
one byte                      1        4    400%      ok
all identical                50       10     20%      ok
abracadabra                  11       10     90%      ok
two distinct bytes          200       29     14%      ok
english text              18000    10086     56%      ok
all 256 byte values        5120     5441    106%      ok
random bytes               4000     4312    107%      ok
```

Two cases get **larger**, and that is expected rather than a bug:

- **Tiny files** — the tree header and padding byte cost more than the savings.
- **Random data** — every byte is equally likely, so there are no frequent
  bytes to give short codes to. Huffman cannot beat incompressible input, and
  pays the header cost on top. Real compressors store such files uncompressed.

## Comparison with gzip

On the English text sample: this tool produces 10,086 bytes; `gzip` produces 135.

The gap is not an implementation flaw. `gzip` uses **DEFLATE**, which runs LZ77
first to replace repeated substrings with back-references, *then* applies
Huffman. The sample is one sentence repeated 400 times, so LZ77 removes almost
all of it before Huffman ever sees it. This project implements the Huffman stage
only.

## Complexity

```
   counting          O(n)
   building the tree O(k log k)      k = distinct byte values, at most 256
   generating codes  O(k)
   encoding          O(n)
   decoding          O(bits)
```

Linear in file size; the tree work is bounded by the 256 possible byte values.

## Edge cases handled

- empty file
- a file with exactly one distinct byte (its tree has no depth, so the root is
  given two identical children to produce a valid 1-bit code)
- bit streams that are not a multiple of 8
- binary files — the compressor reads bytes, not text, so line endings and
  non-UTF-8 content survive the round trip

## Tests

```bash
python3 test_huffman.py
```

## Files

```
   huffman.py        the compressor and CLI
   test_huffman.py   round-trip tests
```
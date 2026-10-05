from collections import defaultdict
import heapq
import os

class TreeNode:
    def __init__(self, char=None, count=0, left=None, right=None):
        self.char = char
        self.count = count
        self.left = left
        self.right = right

    def __lt__(self, other):
        return self.count < other.count


def build_tree(text):
    freq = defaultdict(int)
    for ch in text:
        freq[ch] += 1

    heap = []
    for ch, count in freq.items():
        heapq.heappush(heap, (count, TreeNode(char=ch, count=count)))

    # only one distinct character — give it both children so walk() works
    if len(heap) == 1:
        count, only = heapq.heappop(heap)
        return TreeNode(count=count, left=only, right=only)

    while len(heap) > 1:
        c1, n1 = heapq.heappop(heap)
        c2, n2 = heapq.heappop(heap)
        heapq.heappush(heap, (c1 + c2, TreeNode(count=c1 + c2, left=n1, right=n2)))

    return heap[0][1]


def build_codes(root):
    codes = {}
    def walk(node, path):
        if node.char is not None:
            codes[node.char] = path
            return
        walk(node.left,  path + "0")
        walk(node.right, path + "1")
    walk(root, "")
    return codes


def serialize(node, out):
    """Tree -> bits.  leaf = '1' + 8 bits of the char.  branch = '0' + left + right."""
    if node.char is not None:
        out.append("1")
        out.append(format(ord(node.char), "08b"))
    else:
        out.append("0")
        serialize(node.left, out)
        serialize(node.right, out)


def deserialize(bits, i):
    """Bits -> tree.  Returns (node, index where it stopped reading)."""
    if bits[i] == "1":
        return TreeNode(char=chr(int(bits[i+1:i+9], 2))), i + 9
    left,  i = deserialize(bits, i + 1)
    right, i = deserialize(bits, i)
    return TreeNode(left=left, right=right), i


def compress(infile, outfile):
    text = open(infile).read()
    if not text:
        open(outfile, "wb").write(b"")
        return

    root  = build_tree(text)
    codes = build_codes(root)

    parts = []
    serialize(root, parts)
    bits = "".join(parts) + "".join(codes[ch] for ch in text)

    padding = (8 - len(bits) % 8) % 8
    bits += "0" * padding

    data = [padding]
    for i in range(0, len(bits), 8):
        data.append(int(bits[i:i+8], 2))

    open(outfile, "wb").write(bytes(data))


def decompress(infile, outfile):
    data = open(infile, "rb").read()
    if not data:
        open(outfile, "w").write("")
        return

    padding = data[0]
    bits = "".join(format(b, "08b") for b in data[1:])
    if padding:
        bits = bits[:-padding]

    root, i = deserialize(bits, 0)

    out  = []
    node = root
    for bit in bits[i:]:
        node = node.left if bit == "0" else node.right
        if node.char is not None:
            out.append(node.char)
            node = root

    open(outfile, "w").write("".join(out))


if __name__ == "__main__":
    compress("Test1.txt", "Test1.huff")
    decompress("Test1.huff", "Test1_out.txt")

    before = os.path.getsize("Test1.txt")
    after  = os.path.getsize("Test1.huff")
    print(f"{before} bytes -> {after} bytes")
    print("round trip:", open("Test1.txt").read() == open("Test1_out.txt").read())
import argparse
import base64
import json
import random
import secrets
from sympy import nextprime, isprime

# === 工具函数 ===
def generate_large_prime(bits=256) -> int:
    return nextprime(secrets.randbits(bits))

def generate_n_random_primes(n: int, upper_bound: int) -> list:
    primes = set()
    while len(primes) < n:
        candidate = random.randint(3, upper_bound - 1)
        if isprime(candidate):
            primes.add(candidate)
    return list(primes)

def encode_data(label, data):
    encoded = base64.b64encode(json.dumps(data).encode()).decode()
    return f"{label}:{encoded}"

def decode_data(encoded, expected_label):
    label, b64_data = encoded.split(":", 1)
    assert label == expected_label, f"收到错误标签 {label}，期望 {expected_label}"
    data = json.loads(base64.b64decode(b64_data).decode())
    return data

def input_time_slots(prompt):
    slots = input(prompt).strip().split(",")
    return sorted([int(s.strip()) for s in slots if s.strip().isdigit()])

# === Alice 部分 ===
def alice():
    print("\n=== Alice 阶段 ===")
    N = int(input("请输入时间槽总数 N: "))
    p = generate_large_prime()
    P = generate_n_random_primes(N, p)

    time_slots = input_time_slots("请输入 Alice 的有空时间槽（用逗号分隔）: ")
    alpha = random.randint(3, p - 3)
    print(f"Alice 随机选取的指数 alpha={alpha}")

    A2 = [P[i - 1] for i in time_slots]
    while len(A2) < N:
        dummy = nextprime(random.randint(2, p - 1))
        if dummy not in P:
            A2.append(dummy)

    M_a_unsorted = [pow(x, alpha, p) for x in A2]
    P1 = sorted(range(len(M_a_unsorted)), key=lambda k: M_a_unsorted[k])
    M_a_sorted = sorted(M_a_unsorted)

    output = {"N": N, "p": p, "P": P, "M_a": M_a_sorted}
    encoded = encode_data("A1", output)
    print("\n请将以下编码发送给 Bob：\n")
    print(encoded)

    print("\n=== Alice 收到 M_b 阶段 ===")
    encoded_from_bob = input("请输入 Bob 发送的编码（B2）: ").strip()
    data = decode_data(encoded_from_bob, "B2")
    M_b = data["M_b"]

    M_ba = [pow(m, alpha, p) for m in M_b]
    M_ba_sorted = sorted(M_ba)

    encoded_ba = encode_data("A2", {"M_ba": M_ba_sorted})
    print("\n请将以下编码发送给 ZY（A2）：\n")
    print(encoded_ba)

    print("\n=== Alice 收到索引 j 阶段 ===")
    j = int(input("请输入 Bob 告诉你的索引 j: "))
    p_k = A2[P1[j]]
    k = P.index(p_k)
    print(f"\n双方共有的有空时间槽索引 k={k + 1}")

# === Bob 部分 ===
def bob():
    print("\n=== Bob 阶段 ===")
    encoded_from_alice = input("请输入 Alice 发送的编码(A1): ").strip()
    data = decode_data(encoded_from_alice, "A1")
    N, p, P, M_a = data["N"], data["p"], data["P"], data["M_a"]

    beta = random.randint(3, p - 3)
    print(f"Bob 随机选取的指数 beta={beta}")

    M_ab_unsorted = [pow(m, beta, p) for m in M_a]
    P2 = sorted(range(len(M_ab_unsorted)), key=lambda k: M_ab_unsorted[k])
    M_ab_sorted = sorted(M_ab_unsorted)

    encoded_ab = encode_data("B1", {"M_ab": M_ab_sorted})
    print("\n请将以下编码发送给 ZY（B1）：\n")
    print(encoded_ab)

    time_slots = input_time_slots("请输入 Bob 的有空时间槽（用逗号分隔）: ")
    B2 = [P[i - 1] for i in time_slots]
    while len(B2) < N:
        dummy = nextprime(random.randint(2, p - 1))
        if dummy not in P:
            B2.append(dummy)

    M_b = [pow(x, beta, p) for x in B2]
    M_b_sorted = sorted(M_b)
    encoded_b = encode_data("B2", {"M_b": M_b_sorted})
    print("\n请将以下编码发送给 Alice（B2）：\n")
    print(encoded_b)

    print("\n=== Bob 收到索引 i 阶段 ===")
    i = int(input("请输入 ZY 告诉你的索引 i: "))
    j = P2[i]
    print(f"\n对应的索引 j={j}，请将 j 告诉 Alice。")

# === ZY 部分 ===
def zy():
    print("\n=== ZY 阶段 ===")
    encoded_ab = input("请输入 Bob 发送的编码（B1）: ").strip()
    encoded_ba = input("请输入 Alice 发送的编码（A2）: ").strip()

    M_ab_data = decode_data(encoded_ab, "B1")
    M_ba_data = decode_data(encoded_ba, "A2")
    M_ab = M_ab_data["M_ab"]
    M_ba = M_ba_data["M_ba"]

    intersection = list(set(M_ab) & set(M_ba))
    if not intersection:
        print("交集为空，没有共同有空时间。")
        return

    z = random.choice(intersection)
    i = M_ab.index(z)
    print(f"\n随机选择的交集元素在 M_ab 中的索引 i={i}")
    print("请将索引 i 告诉 Bob。 (标签: Z1)")

# === CLI 主入口 ===
def main():
    parser = argparse.ArgumentParser(description="基于多方安全计算的组会时间选定算法")
    subparsers = parser.add_subparsers(title="子命令", description="选择角色", dest="role")

    subparsers.add_parser("alice", help="Alice")
    subparsers.add_parser("bob", help="Bob")
    subparsers.add_parser("zy", help="ZY")

    args = parser.parse_args()

    if args.role == "alice":
        alice()
    elif args.role == "bob":
        bob()
    elif args.role == "zy":
        zy()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

"""Prepare seed SQL from an OWNER-APPROVED UTF-8 word list; never connect to DB."""
import argparse
import hashlib
from pathlib import Path

ALPHABET = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZñÑ")


def build_seed(raw: bytes) -> str:
    words = set()
    for number, line in enumerate(raw.decode("utf-8-sig").splitlines(), 1):
        word = line.strip()
        if not word:
            continue
        # Validate BEFORE upper() to reject Unicode expansions such as sharp s.
        if len(word) != 5 or any(letter not in ALPHABET for letter in word):
            raise ValueError(f"Invalid dictionary entry at line {number}; expected five A-Z/Ñ letters")
        words.add(word.upper())
    if not words:
        raise ValueError("The approved dictionary must contain at least one word")
    checksum = hashlib.sha256(raw).hexdigest()
    values = ",\n".join(f"    ('{word}')" for word in sorted(words))
    # Whitelisting above excludes SQL delimiters; source contents are not comments.
    return (
        "-- Generated from an owner-approved dictionary; no production extraction.\n"
        f"-- Source SHA256: {checksum}\n"
        f"-- Distinct normalized words: {len(words)}\n"
        "-- Apply only to the authorized disposable local target.\n"
        "BEGIN;\nINSERT INTO public.palabras (palabra) VALUES\n"
        + values + "\nON CONFLICT (palabra) DO NOTHING;\nCOMMIT;\n"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--owner-approved", required=True, action="store_true",
                        help="Confirm source permission/licence; do not use a production export")
    args = parser.parse_args()
    sql = build_seed(args.input.read_bytes())
    # Never overwrite an existing artifact. No DB/client/network dependency.
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(sql)
    print("Prepared dictionary SQL; no database operations performed.")


if __name__ == "__main__":
    main()

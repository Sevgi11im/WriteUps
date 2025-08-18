#!/usr/bin/env python3
# Brute force OpenSSL enc decryption options and only report candidates
# that contain PNG/IHDR/IDAT/IEND/RIFF in their output.

import subprocess, re, os, sys

PASSWORD = "Aw4ken_7he_Cut3s7_An9e1_iN_7he_w0rld"
INFILE = "flag.enc"
OUTDIR = "decrypt_candidates"
os.makedirs(OUTDIR, exist_ok=True)

def run_cmd(cmd):
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=20)
        return proc.returncode, proc.stdout
    except Exception:
        return 999, b""

def get_ciphers():
    rc, out = run_cmd(["openssl", "enc", "-ciphers"])
    if rc != 0:
        print("Failed to list openssl ciphers")
        sys.exit(1)
    text = out.decode(errors="ignore")
    parts = text.split(":", 1)[1] if ":" in text else text
    return [t for t in re.split(r"\s+", parts.strip())
            if re.match(r"^[a-z0-9\-]+$", t)]

ciphers = get_ciphers()
print(f"Found {len(ciphers)} ciphers. Trying all combinations...")

# Try every combination and save output
for cipher in ciphers:
    for pbkdf2 in (False, True):
        for md in ("md5", "sha256"):
            for base64 in (False, True):
                outname = f"{cipher}{'_pbkdf2' if pbkdf2 else ''}_md-{md}{'_a' if base64 else ''}.bin"
                path = os.path.join(OUTDIR, outname)
                cmd = ["openssl", "enc", "-d", "-" + cipher,
                       "-in", INFILE, "-pass", "pass:" + PASSWORD,
                       "-md", md]
                if pbkdf2: cmd.append("-pbkdf2")
                if base64: cmd.append("-a")
                rc, out = run_cmd(cmd)
                with open(path, "wb") as f:
                    f.write(out)

# Now scan all candidates for useful signatures
patterns = (b"IHDR", b"IHDR", b"IDAT", b"IEND", b"RIFF",)
hits = {}

for fname in os.listdir(OUTDIR):
    fpath = os.path.join(OUTDIR, fname)
    try:
        with open(fpath, "rb") as f:
            data = f.read()
            found = [p.decode("latin1") for p in patterns if p in data]
            if found:
                hits[fname] = found
    except Exception:
        pass

if hits:
    print(f"Possible valid decryptions, found {patterns} in:")
    for h, found in hits.items():
        print(f"- {h} # found {', '.join(found)}")
else:
    print("No hits found. Check decrypt_candidates/ manually.")


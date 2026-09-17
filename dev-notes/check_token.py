import os
from dotenv import dotenv_values

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

# Ask dotenv's own parser what it extracts — bypasses any guessing
parsed = dotenv_values(env_path)
print("Keys dotenv actually parsed:", list(parsed.keys()))

# Show the raw file content in escaped form so hidden characters become visible
with open(env_path, "rb") as f:
    raw = f.read()

text = raw.decode("utf-8", errors="replace")
if "=" in text:
    key_part, value_part = text.split("=", 1)
    value_part = value_part.strip()
    masked = value_part[:6] + "..." + value_part[-4:] if len(value_part) > 10 else value_part
    print("Full file repr:", repr(text[:len(key_part)+1] + masked))
else:
    print("Full file repr:", repr(text))
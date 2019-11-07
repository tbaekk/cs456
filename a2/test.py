buffer = []
with open("tiny.txt", "rb") as f:
  byte = f.read(500)
  while byte:
    buffer.append(byte)
    byte = f.read(500)

for x in buffer:
  print(x)

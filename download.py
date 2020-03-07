import sys
import requests

if len(sys.argv) != 3 and len(sys.argv) != 4:
    print("Usage: python download.py xlogin00 COUNT")
    exit(1)

login = sys.argv[1]
target_count = int(sys.argv[2])
current_count = 0
target_file = sys.argv[3] if len(sys.argv) == 4 else "messages.txt"

if target_count <= 0:
    print("Target message count invalid!")
    exit(1)


def download():
    try:
        req = requests.get(f"http://pcocenas.fit.vutbr.cz/?login={login}&cnt=50")
        content = req.content.decode("utf-8")
        if content.startswith("Error"):
            print("There has been an error on remote server: " + content.replace("<br>", "\n"))
            exit(2)

        return content.split("\n")

    except ConnectionError as err:
        print("\nAn exception occured while processing the request...")
        print(err)
        exit(1)


print("\rOpening target file, starting download...", end="", flush=True)
with open(target_file, "w") as f:
    while current_count < target_count:
        print(f"\rDownloading messages... ({current_count}/{target_count})", end="", flush=True)
        messages = download()
        current_count += len(messages)
        f.writelines("\n".join(messages) + "\n")

print(f"\rDownloading finished!")

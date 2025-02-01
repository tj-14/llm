import datetime
import os
import readline  # not used, but needed for input() to work properly
import subprocess
from pathlib import Path

from openai import OpenAI
from trafilatura import extract, fetch_url

N_RG_CHOICES = 3
VAULTDIR = "/Users/tj/Dropbox/tj-vault-dropbox/"


class LOGGER:
    def __init__(self):
        base_dir = Path("/Users/tj/.llm/logs")
        base_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = base_dir / (
            datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + ".txt"
        )

    def log(self, *args, **kwargs):
        file_only = False
        if "file_only" in kwargs:
            file_only = kwargs.pop("file_only")
        if not file_only:
            print(*args, **kwargs)
        with open(self.log_file, "a") as f:
            print(*args, **kwargs, file=f)


logger = LOGGER()
P = logger.log


def IN(*args, **kwargs):
    if len(args) > 0:
        P(args[0], file_only=True)
    i = input(*args, **kwargs)
    P(i, file_only=True)
    return i


class LLM:
    def __init__(self):
        self.api_key = os.environ.get("OPENTYPHOON_API_KEY")
        self.base_url = "https://api.opentyphoon.ai/v1"
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )
        self.model = "typhoon-v2-70b-instruct"
        self.messages = []

    def add_message(self, role, content):
        self.messages.append(
            {
                "role": role,
                "content": content,
            }
        )

    def chat_once(self):
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            max_tokens=4096,
            temperature=0.6,
            top_p=0.95,
            stream=True,
        )

        msg = ""
        response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                msg = chunk.choices[0].delta.content
                P(msg, end="", flush=True)

                response += msg

        P()
        P()
        self.add_message("assistant", response)

    def rag_prompt(self, context, source):
        P()
        P(source, file_only=True)
        context = f"<context>\n{context}\n</context>"
        P(context)
        P()

        p = IN()
        return context + "\n\n\n" + p

    def chat(self):
        while True:
            P("# P: ")
            try:
                p = IN()

                if p.lower() in {"'", "m"}:
                    multi_p = []
                    while True:
                        p = IN()
                        if p.lower() in {"'", "m"}:
                            break
                        multi_p.append(p)
                    p = "\n".join(multi_p)
                elif p.lower() in {"h", "u", "r"}:
                    url = IN("Enter URL: ")
                    html = fetch_url(url)
                    text = extract(html)

                    p = self.rag_prompt(text, url)
                elif p.lower() in {"rg"}:
                    g = IN()
                    rg = subprocess.run(
                        ["rg", "-i", g, VAULTDIR, "-l"], capture_output=True
                    )
                    choices = rg.stdout.decode().split("\n")
                    choices = choices[:N_RG_CHOICES]
                    for i, choice in enumerate(choices):
                        P(f"{i}: {Path(choice).relative_to(VAULTDIR)}")
                    try:
                        choice = int(IN())
                        with open(choices[choice]) as f:
                            text = f.read()

                        p = self.rag_prompt(text, choices[choice])
                    except Exception as e:
                        P(e)
                        P("Invalid choice")
                        continue

                P()
                self.add_message("user", p)

                P("# M: ")
                self.chat_once()
            except KeyboardInterrupt:
                break


def main():
    llm = LLM()
    llm.chat()


if __name__ == "__main__":
    main()

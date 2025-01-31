import datetime
import os
from pathlib import Path

from openai import OpenAI
from trafilatura import extract, fetch_url


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

    def chat(self):
        while True:
            P("# P: ")
            try:
                p = input()

                if p.lower() in {"'", "m"}:
                    multi_p = []
                    while True:
                        p = input()
                        if p.lower() in {"'", "m"}:
                            break
                        multi_p.append(p)
                    p = "\n".join(multi_p)

                if p.lower() in {"h", "u", "r"}:
                    url = input("Enter URL: ")
                    html = fetch_url(url)
                    text = extract(html)
                    P(url, file_only=True)
                    P()
                    P(text)
                    P()
                    p = text + "\n\n\n" + input()

                P(p, file_only=True)
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

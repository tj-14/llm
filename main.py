import datetime
import os
from pathlib import Path

from openai import OpenAI

original_print = print


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
            original_print(*args, **kwargs)
        with open(self.log_file, "a") as f:
            original_print(*args, **kwargs, file=f)


logger = LOGGER()
print = logger.log


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
                print(msg, end="", flush=True)

                response += msg

        print()
        print()
        self.add_message("assistant", response)

    def chat(self):
        while True:
            print("# P: \n")
            try:
                p = input().strip()
                if p.lower() in {"exit", "quit"}:
                    print("Exiting chat.")
                    break

                print(p, file_only=True)
                print()
                self.add_message("user", p)

                print("# M: \n")
                self.chat_once()
            except KeyboardInterrupt:
                print("\nExiting chat.")
                break


def main():
    llm = LLM()
    llm.chat()


if __name__ == "__main__":
    main()

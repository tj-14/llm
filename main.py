import argparse
import datetime
import json
import os
import readline  # needed for input() to behave
import sqlite3
import subprocess
from pathlib import Path

import pyperclip
from mistralai import Mistral
from openai import OpenAI
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from together import Together
from trafilatura import extract, fetch_url

from constants import BASEPATH, DATABASE, N_CONVERSATIONS, N_RG_CHOICES, VAULTDIR


class LOGGER:
    def __init__(self):
        base_dir = BASEPATH / "logs"
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
    def __init__(self, model):
        if model == "typhoon":
            self.api_key = os.environ.get("OPENTYPHOON_API_KEY")
            self.base_url = "https://api.opentyphoon.ai/v1"
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
            self.model = "typhoon-v2-70b-instruct"
        elif model == "mistral":
            self.api_key = os.environ.get("MISTRAL_API_KEY")
            self.model = "mistral-small-latest"
            self.client = Mistral(api_key=self.api_key)
        elif model == "llama":
            self.api_key = os.environ.get("TOGETHER_API_KEY")
            self.client = Together(api_key=self.api_key)
            self.model = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
        elif model == "deepseek":
            self.api_key = os.environ.get("TOGETHER_API_KEY")
            self.client = Together(api_key=self.api_key)
            self.model = "deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free"

        self.messages = []
        self.conn = sqlite3.connect(DATABASE)
        self.cursor = self.conn.cursor()

    def add_message(self, role, content):
        self.messages.append(
            {
                "role": role,
                "content": content,
            }
        )

    def undo_message(self):
        if len(self.messages) > 1:
            self.messages = self.messages[:-2]

    def get_one_line_summary(self):
        self.add_message(
            "user", "summarize this conversation as a one-line heading only"
        )
        return self.chat_once()

    def save_conversation(self):
        conversation_content = json.dumps(self.messages)
        summary = self.get_one_line_summary()
        summary = summary.strip()
        summary = summary.split("\n")[-1]

        self.cursor.execute(
            "INSERT INTO conversations (content, summary, model) VALUES (?, ?, ?)",
            (conversation_content, summary, self.model),
        )
        conversation_id = self.cursor.lastrowid
        self.conn.commit()
        return conversation_id

    def load_conversation(self, conversation_id):
        print(conversation_id)
        self.cursor.execute(
            "SELECT content FROM conversations WHERE id = ?", (conversation_id,)
        )
        result = self.cursor.fetchone()
        if result:
            self.messages = json.loads(result[0])
        else:
            self.messages = []
        return self.messages

    def load_all_conversations(self):
        self.cursor.execute("SELECT summary, id FROM conversations")
        results = self.cursor.fetchall()
        return list(results)

    def chat_once(self):
        if isinstance(self.client, OpenAI) or isinstance(self.client, Together):
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                max_tokens=4096,
                temperature=0.6,
                top_p=0.95,
                stream=True,
            )
        elif isinstance(self.client, Mistral):
            stream = self.client.chat.stream(
                model=self.model,
                messages=self.messages,
            )

        response = ""

        with Live() as live:
            for chunk in stream:
                if isinstance(self.client, OpenAI) or isinstance(self.client, Together):
                    msg = chunk.choices[0].delta.content
                elif isinstance(self.client, Mistral):
                    msg = chunk.data.choices[0].delta.content

                if msg:
                    P(msg, end="", flush=True, file_only=True)
                    response += msg
                    live.update(Markdown(response))

        P()
        P()
        self.add_message("assistant", response)
        return response

    def rag_prompt(self, context, source):
        P()
        P(source, file_only=True)
        context = f"<context>\n{context}\n</context>"
        P(context)
        P()

        p = IN()
        return context + "\n\n\n" + p

    def chat(self):
        console = Console()
        console.print(Markdown(f"# {self.model} | ', url, rg | undo, save, load"))
        while True:
            try:
                P("# P: ")
                p = IN()

                if p.lower() in {"'"}:
                    P("Ctrl-D to end input")
                    p = []
                    while True:
                        try:
                            line = IN()
                        except EOFError:
                            break
                        if line == "paste":
                            line = pyperclip.paste()
                            P(line)
                        p.append(line)
                    p = "\n".join(p)
                elif p.lower() in {"url"}:
                    url = IN("Enter URL: ")
                    html = fetch_url(url)
                    text = extract(html)

                    p = self.rag_prompt(text, url)
                elif p.lower() in {"rg"}:
                    g = IN()
                    rg = subprocess.run(
                        ["rg", "-i", g, str(VAULTDIR), "-l"], capture_output=True
                    )
                    choices = rg.stdout.decode().split("\n")
                    choices = choices[:N_RG_CHOICES]
                    for i, choice in enumerate(choices):
                        P(f"{i}: {Path(choice).relative_to(VAULTDIR)}")
                    choice = int(IN())
                    with open(choices[choice]) as f:
                        text = f.read()

                    p = self.rag_prompt(text, choices[choice])
                elif p.lower() in {"undo"}:
                    self.undo_message()
                    continue
                elif p.lower() in {"save"}:
                    conversation_id = self.save_conversation()
                    P(f"Conversation saved with id {conversation_id}")
                    continue
                elif p.lower() in {"load"}:
                    all_conversations = self.load_all_conversations()[-N_CONVERSATIONS:]
                    all_conversations = list(reversed(all_conversations))
                    for i, (summary, _) in enumerate(all_conversations):
                        P(f"{i}: {summary}")
                    load_choice = IN("Load: ")
                    messages = self.load_conversation(
                        all_conversations[int(load_choice)][1]
                    )
                    P(messages)
                    continue
                elif p.lower() in {"copy"}:
                    pyperclip.copy(self.messages[-1]["content"])
                    P("Copied to clipboard")
                    continue

                P()
                self.add_message("user", p)

                P("# M: ")
                self.chat_once()
            except KeyboardInterrupt:
                if len(self.messages) > 0:
                    P()
                    conversation_id = self.save_conversation()
                    P(f"Conversation saved with id {conversation_id}")
                break


def main(args):
    llm = LLM(model=args.model)
    llm.chat()


def parse_args():
    parser = argparse.ArgumentParser(description="LLM")
    parser.add_argument(
        "--model",
        type=str,
        default="llama",
        help="Model to use (`mistral`, `typhoon`, `llama`, `deepseek`)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(args)

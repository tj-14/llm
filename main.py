import datetime
import json
import os
import readline  # not used, but needed for input() to work properly
import sqlite3
import subprocess
from pathlib import Path

from openai import OpenAI
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
    def __init__(self):
        self.api_key = os.environ.get("OPENTYPHOON_API_KEY")
        self.base_url = "https://api.opentyphoon.ai/v1"
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )
        self.model = "typhoon-v2-70b-instruct"
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
            "assistant", "summarize this conversation as a one-line heading only"
        )
        return self.chat_once()

    def save_conversation(self):
        # "summarize this conversation as a one-line heading only"
        conversation_content = json.dumps(self.messages)
        summary = self.get_one_line_summary()

        self.cursor.execute(
            "INSERT INTO conversations (content, summary) VALUES (?, ?)",
            (conversation_content, summary),
        )
        conversation_id = self.cursor.lastrowid
        self.conn.commit()
        return conversation_id

    def load_conversation(self, conversation_id):
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
        self.cursor.execute("SELECT summary, content FROM conversations")
        results = self.cursor.fetchall()
        return [(result[0], json.loads(result[1])) for result in results]

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
                    all_conversations = self.load_all_conversations()
                    for i, (summary, _) in enumerate(
                        all_conversations[:N_CONVERSATIONS]
                    ):
                        P(f"{i}: {summary}")
                    conversation_id = IN("Enter conversation id: ")
                    messages = self.load_conversation(conversation_id)
                    P(messages)
                    continue

                P()
                self.add_message("user", p)

                P("# M: ")
                self.chat_once()
            except KeyboardInterrupt:
                P()
                conversation_id = self.save_conversation()
                P(f"Conversation saved with id {conversation_id}")
                break


def main():
    llm = LLM()
    llm.chat()


if __name__ == "__main__":
    main()

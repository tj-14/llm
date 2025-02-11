from pathlib import Path

N_RG_CHOICES = 3
N_CONVERSATIONS = 3

HOMEPATH = Path.home().absolute()

VAULTDIR = HOMEPATH / "Dropbox/tj-vault-dropbox/"
BASEPATH = HOMEPATH / ".llm"
DATABASE = BASEPATH / "conversations.db"

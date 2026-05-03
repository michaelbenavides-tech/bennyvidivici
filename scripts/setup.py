import pathlib
import shutil

root = pathlib.Path(__file__).resolve().parents[1]
env = root / ".env"
example = root / ".env.example"
if not env.exists():
    shutil.copyfile(example, env)
    print("Created .env from .env.example")
else:
    print(".env already exists")

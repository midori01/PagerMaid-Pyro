from sys import executable
from pagermaid.utils import execute

async def update(force: bool = False):
    await execute("git fetch --all")
    if force:
        await execute("git reset --hard origin/master")
    else:
        await execute("git diff --quiet || git stash")
    await execute("git pull --all")
    await execute(f"{executable} -m pip install --upgrade -r requirements.txt --break-system-packages")
    await execute("git stash pop || true")

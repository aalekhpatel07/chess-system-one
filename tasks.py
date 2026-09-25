from invoke import task
import subprocess

@task
def build_static(c):
    with c.cd("chess-system-one"):
        c.run("pnpm run build", pty=True)

@task 
def build_server(c):
    build_static(c)
    c.run("docker build -f server.Dockerfile .", pty=True)


@task
def prepare_pages(c):
    build_static(c)
    c.run("git checkout gh-pages", pty=True)
    c.run("rm -rf ./docs", pty=True)
    c.run("cp -r chess-system-one/dist docs", pty=True)

from invoke import task

@task
def build_static(c):
    with c.cd("chess-system-one"):
        c.run("pnpm run build", pty=True)

@task 
def build_server(c):
    build_static(c)
    c.run("docker build -f server.Dockerfile .", pty=True)


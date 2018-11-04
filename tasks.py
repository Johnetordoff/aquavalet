import os

from invoke import task

@task
def install(ctx, develop=False, pty=True):
    ctx.run('python setup.py develop')
    req_file = 'dev-requirements.txt' if develop else 'requirements.txt'
    cmd = 'pip install --upgrade -r {}'.format(req_file)

    ctx.run(cmd, pty=pty)


@task
def flake(ctx):
    """
    Run style and syntax checker. Follows options defined in setup.cfg
    """
    ctx.run('flake8 .', pty=True)


@task
def mypy(ctx):
    """
    Check python types using mypy (additional level of linting). Follows options defined in setup.cfg
    """
    ctx.run('mypy aquavalet/', pty=True)


@task
def test(ctx):
    cmd = 'python -m pytest --cov-report=html --cov=aquavalet/providers/filesystem/'
    ctx.run(cmd, pty=True)

@task
def rabbitmq(ctx):
    ctx.run('rabbitmq-server', pty=True)


@task
def server(ctx):

    if os.environ.get('REMOTE_DEBUG', None):
        import pydevd
        # e.g. '127.0.0.1:5678'
        remote_parts = os.environ.get('REMOTE_DEBUG').split(':')
        pydevd.settrace(remote_parts[0], port=int(remote_parts[1]), suspend=False, stdoutToServer=True, stderrToServer=True)

    from aquavalet.app import serve
    serve()

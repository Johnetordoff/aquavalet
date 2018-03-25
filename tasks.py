import os

from invoke import task

WHEELHOUSE_PATH = os.environ.get('WHEELHOUSE')


@task
def wheelhouse(ctx, develop=False, pty=True):
    req_file = 'dev-requirements.txt' if develop else 'requirements.txt'
    cmd = 'pip wheel --find-links={} -r {} --wheel-dir={}'.format(WHEELHOUSE_PATH, req_file, WHEELHOUSE_PATH)
    ctx.run(cmd, pty=pty)


@task
def install(ctx, develop=False, pty=True):
    ctx.run('python setup.py develop')
    req_file = 'dev-requirements.txt' if develop else 'requirements.txt'
    cmd = 'pip install --upgrade -r {}'.format(req_file)

    if WHEELHOUSE_PATH:
        cmd += ' --no-index --find-links={}'.format(WHEELHOUSE_PATH)
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
def test(ctx, verbose=False, types=False):
    flake(ctx)
    if types:
        mypy(ctx)

    cmd = 'py.test --cov-report term-missing --cov aquavalet tests'
    if verbose:
        cmd += ' -v'
    ctx.run(cmd, pty=True)


@task
def celery(ctx, loglevel='INFO', hostname='%h'):

    from aquavalet.tasks.app import app
    command = ['worker']
    if loglevel:
        command.extend(['--loglevel', loglevel])
    if hostname:
        command.extend(['--hostname', hostname])
    app.worker_main(command)


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

    from aquavalet.server.app import serve
    serve()


@task
def clean(ctx, verbose=False):
    cmd = 'find . -name "*.pyc" -delete'
    if verbose:
        print(cmd)
    ctx.run(cmd, pty=True)

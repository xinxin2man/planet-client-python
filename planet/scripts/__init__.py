import click
import json
from planet import api

client = api.Client()

pretty = click.option('-pp', '--pretty', default=False, is_flag=True)
scene_type = click.option('-s', '--scene-type', default='ortho')


def call_and_wrap(func, *args, **kw):
    '''call the provided function and wrap any API exception with a click
    exception. this means no stack trace is visible to the user but instead
    a (hopefully) nice message is provided.
    note: could be a decorator but didn't play well with click
    '''
    try:
        return func(*args, **kw)
    except api.APIException, ex:
        if type(ex) is api.APIException:
            raise click.ClickException('Unexpected response: %s' % ex.message)
        msg = "%s: %s" % (type(ex).__name__, ex.message)
        raise click.ClickException(msg)


@click.group()
@click.option('-k', '--api-key',
              help='Valid API key - or via env variable %s' % api.ENV_KEY)
@click.option('-u', '--base-url', help='Optional for testing')
def cli(api_key, base_url):
    '''Planet API Client'''
    if api_key:
        client.api_key = api_key
    if base_url:
        client.base_url = base_url


@cli.command()
def list_all_scene_types():
    '''List all scene types.'''
    click.echo(call_and_wrap(client.list_all_scene_types))


@scene_type
@click.argument('scene_ids', nargs=-1)
@click.option('--product', type=click.Choice([ "band_%d" % i for i in range(1, 12) ] + ['visual', 'analytic', 'qa']), default='visual')
@cli.command('download')
@click.pass_context
def fetch_scene_geotiff(ctx, scene_ids, scene_type, product):
    '''Fetch full scene image(s)'''
    
    if len(scene_ids) == 0:
        src = click.open_file('-')
        if not src.isatty():
            scene_ids = map(lambda s: s.strip(), src.readlines())
        else:
            click.echo(ctx.get_usage())
    
    call_and_wrap(client.fetch_scene_geotiffs, scene_ids, scene_type, product)


@scene_type
@click.argument("scene-ids", nargs=-1)
@click.option('--size', type=click.Choice(['sm', 'md', 'lg']), default='md')
@click.option('--format', 'fmt', type=click.Choice(['png', 'jpg', 'jpeg']), default='png')
@cli.command('thumbnails')
def fetch_scene_thumbnails(scene_ids, scene_type, size, fmt):
    '''Fetch scene thumbnail(s)'''
    
    if len(scene_ids) == 0:
        src = click.open_file('-')
        if not src.isatty():
            scene_ids = map(lambda s: s.strip(), src.readlines())
    
    call_and_wrap(client.fetch_scene_thumbnails, scene_ids, scene_type, size, fmt)


@pretty
@scene_type
@click.argument('id', nargs=1)
@cli.command('metadata')
def fetch_scene_info(id, scene_type, pretty):
    '''Fetch scene metadata'''
    res = call_and_wrap(client.fetch_scene_info, id, scene_type)
    if pretty:
        res = json.dumps(json.loads(res), indent=2)
    click.echo(res)


@pretty
@scene_type
@cli.command('get-scenes-list')
@click.argument("aoi", default="-", required=False)
def get_scenes_list(scene_type, pretty, aoi):
    '''Get a list of scenes'''
    
    if aoi == "-":
        src = click.open_file('-')
        if not src.isatty():
            lines = src.readlines()
            aoi = ''.join([ line.strip() for line in lines ])
        else:
            aoi = None

    res = call_and_wrap(client.get_scenes_list, scene_type=scene_type, intersects=aoi)
    if pretty:
        res = json.dumps(json.loads(res), indent=2)
    click.echo(res)

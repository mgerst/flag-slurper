import logging
import os
from functools import partial
from multiprocessing import Pool

import click
from peewee import fn

from flag_slurper.autolib.models import SUDO_FLAG
from . import utils, autolib
from .autolib import models
from .config import Config
from .project import Project

pass_config = click.make_pass_decorator(Config)

FILTERED_SERVICE_STATUS = ['score', 'service_order', 'in_progress', 'service_details', 'service_status',
                           'public_visibility', 'blue_visibility', 'green_visibility', 'red_visibility',
                           'event_time']

logger = logging.getLogger(__name__)


@click.group()
@click.pass_context
def autopwn(ctx):
    p = Project.get_instance()
    if not p.enabled:
        utils.report_error("AutoPWN commands require an active project")
        exit(4)
    p.connect_database()
    ctx.obj = p


def _pwn_service(limit_creds, service):
    p = Project.get_instance()
    config = p.post(service)
    team = service.team
    utils.report_status("Checking {team}/{url}:{port}/{proto}".format(team=team.number, url=service.service_url,
                                                                      port=service.service_port,
                                                                      proto=service.service_name))
    flags = p.flag(team)
    flag = list(filter(lambda x: x['service'] == service.service_name, flags))
    logger.debug("pwning %d", team.number)
    result = autolib.pwn_service(service, flag, limit_creds, config)
    logger.debug("pwned %d", team.number)
    return result


def _print_result(result, verbose):
    if result.success:
        utils.report_success(result)
    elif result.skipped:
        if verbose:
            utils.report_warning(result)
    else:
        utils.report_error(result)


@autopwn.command()
@pass_config
@click.option('-v', '--verbose', is_flag=True)
@click.option('-P', '--parallel', is_flag=True, help="Async AutoPWN attack")
@click.option('-N', '--processes', type=click.INT, default=None, help="How manny process to use for async AutoPWN")
@click.option('-c', '--limit-creds', type=click.STRING, multiple=True, help="Limit the attack to the given creds")
@click.option('-t', '--team', type=click.INT, default=None, help="Limit the attack to the given team")
@click.option('-s', '--service', type=click.STRING, default=None, help="Limit the attack to the given service name")
@click.option('-r', '--randomize', is_flag=True, help="Randomize autopwn order")
def pwn(config, verbose, parallel, processes, limit_creds, team, service, randomize):
    utils.report_status("Starting AutoPWN")
    p = Project.get_instance()

    if not processes:
        processes = os.cpu_count() + 1

    p.connect_database()
    utils.report_status("Loaded project from {}".format(p.base))

    services = models.Service.select()

    if team:
        utils.report_status('Limited to team {}'.format(team))
        services = services.join(models.Team).where(models.Team.number == team)

    if service:
        utils.report_status('Limited to service {}'.format(service))
        services = services.where(models.Service.service_name == service)

    if randomize or config.getboolean('autopwn', 'random'):
        utils.report_status('Shuffling services')
        services = services.order_by(fn.Random())

    if parallel:
        print("Using pool size: {}".format(processes))
        with Pool(processes=processes) as pool:
            pwn_service = partial(_pwn_service, limit_creds)
            results = pool.map(pwn_service, services)

        for result in results:
            _print_result(result, verbose)
    else:
        for service in services:
            result = _pwn_service(limit_creds, service)
            _print_result(result, verbose)

    bags = models.CredentialBag.select()
    if limit_creds:
        bags = bags.where(models.CredentialBag.username.in_(limit_creds))

    for cred in bags:
        working = cred.credentials.where(models.Credential.state == models.Credential.WORKS).execute()
        if len(working):
            def display_service(cred: models.Credential):
                return "{}/{}".format(cred.service.team.number, cred.service.service_name)

            utils.report_success("Credential {} works on the following teams: \n\t- {}".format(cred, "\n\t- ".join(
                map(display_service, working))))
        else:
            utils.report_warning("Credential {} works on no teams".format(cred))


@autopwn.command()
@click.option('-r', '--reconcile', is_flag=True, help='Remove teams that do not exist in IScorE')
def generate(reconcile):
    p = Project.get_instance()
    p.connect_database()
    teams = utils.get_teams()

    if reconcile:
        ids = [t['id'] for t in teams]
        old_teams = models.Team.select().where(~models.Team.id << ids)
        if old_teams.count() > 0:
            utils.report_status("Reconciling {} team(s)".format(old_teams.count()))
            map(lambda x: x.delete_instance(), old_teams)

    with models.database_proxy.obj:
        for team in teams:
            t, _ = models.Team.get_or_create(id=team['id'], name=team['name'], number=team['number'],
                                             domain=team['team_url'])
        models.database_proxy.commit()

    # TODO: When /services.json gets fixed, use get_services()
    service_status = utils.get_service_status()
    for status in service_status:
        service = utils.get_service(status['service_name'])
        service_url = service['url'].format(num=status['team_number'])
        st, _ = models.Service.get_or_create(remote_id=status['id'], service_id=status['service_id'],
                                             service_name=status['service_name'], service_port=service['port'],
                                             service_url=service_url, team_id=status['team_id'])


@autopwn.command()
def results():
    p = Project.get_instance()
    p.connect_database()

    utils.report_status("Found the following flags")
    utils.report_status("Key: {} Used Sudo".format(SUDO_FLAG))
    flags = models.Flag.select()
    if len(flags) == 0:
        utils.report_warning('No Flags Found')

    for flag in flags:
        notes = flag.notes.select().execute()
        if len(notes) == 1:
            note = notes[0]
            utils.report_success(
                "{}/{}: {} -> {}".format(flag.team.number, note.service.service_name, note.location, note.data))
        elif len(notes) > 1:
            data = "\n\t".join(map(str, notes))
            utils.report_success("{}/{}:\n\t{}".format(flag.team.number, notes[0].service.service_name, data))
        else:
            continue

    click.echo()
    utils.report_status("Found the following credentials")
    utils.report_status("Key: {} Sudo".format(SUDO_FLAG))

    services = models.Service.select()
    for service in services:
        creds = service.credentials.where(models.Credential.state == models.Credential.WORKS)
        if len(creds) == 0:
            continue

        utils.report_success("{}/{}:{}/{} Succeeded!  Found credentials: {}".format(
            service.team.number, service.service_url, service.service_port, service.service_name,
            ",".join(map(str, creds))
        ))

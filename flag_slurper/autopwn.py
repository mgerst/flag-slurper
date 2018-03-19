import pathlib
from collections import defaultdict

import click
import yaml

from . import utils, autolib
from .autolib import models
from .config import Config
from .project import Project

pass_config = click.make_pass_decorator(Config)

FILTERED_SERVICE_STATUS = ['score', 'service_order', 'in_progress', 'service_details', 'service_status',
                           'public_visibility', 'blue_visibility', 'green_visibility', 'red_visibility',
                           'event_time']


@click.group()
def autopwn():
    pass


@autopwn.command()
@click.option('-r', '--results', type=click.Path(), default=Project.default('results', 'results.yml'))
@click.option('-v', '--verbose', type=click.BOOL, default=False)
def pwn(results, verbose):
    utils.report_status("Starting AutoPWN")
    p = Project.get_instance()

    if not p.enabled:
        utils.report_error("AutoPwn requires a project be active")
        return 1

    p.connect_database()
    utils.report_status("Loaded project from {}".format(p.base))
    results = p.base / results

    services = models.Service.select()

    pwn_results = {'scan_results': []}
    for service in services:
        team = service.team
        utils.report_status("Checking team: {} ({})".format(team.number, team.name))
        flags = p.flag(team)
        flag = list(filter(lambda x: x['service'] == service.service_name, flags))
        flag = flag[0] if len(flag) == 1 else []
        result = autolib.pwn_service(service, flag)
        pwn_results['scan_results'].append(result)
        if result.success:
            utils.report_success(result)
        elif result.skipped:
            if verbose:
                utils.report_warning(result)
        else:
            utils.report_error(result)

    pwn_results['creds'] = []
    for cred in models.CredentialBag.select():
        pwn_results['creds'].append(cred)
        working = cred.credentials.where(models.Credential.state == models.Credential.WORKS).execute()
        if len(working):
            def display_service(cred: models.Credential):
                return "{}/{}".format(cred.service.team.number, cred.service.service_name)

            utils.report_success("Credential {} works on the following teams: \n\t- {}".format(cred, "\n\t- ".join(
                map(display_service, working))))
        else:
            utils.report_warning("Credential {} works on no teams".format(cred))

    with open(str(results), 'w') as results:
        pwn_results['flags'] = autolib.flag_bag.flags
        yaml.dump(pwn_results, results, default_flow_style=False)


@autopwn.command()
def generate():
    p = Project.get_instance()
    p.connect_database()
    if not p.enabled:
        utils.report_error("Generate requires a project be active")
        return 1

    teams = utils.get_teams()

    team_map = {}
    with models.database_proxy.obj:
        for team in teams:
            t, _ = models.Team.get_or_create(id=team['id'], name=team['name'], number=team['number'])
            team_map[team['id']] = t
        models.database_proxy.commit()

    # TODO: When /services.json gets fixed, use get_services()
    service_status = utils.get_service_status()
    for status in service_status:
        t = team_map[status['team_id']]
        st, _ = models.Service.get_or_create(remote_id=status['id'], service_id=status['service_id'],
                                             service_name=status['service_name'], service_port=status['service_port'],
                                             service_url=status['service_url'], admin_status=status['admin_status'],
                                             high_target=status['high_target'], low_target=status['low_target'],
                                             is_rand=status['is_rand'], team=t)


@autopwn.command()
def results():
    p = Project.get_instance()

    if not p.enabled:
        utils.report_error("This command requires a project be active")
        exit(3)

    p.connect_database()

    utils.report_status("Found the following credentials")
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
            utils.report_success("{}/{}:\n{}".format(flag.team.number, notes[0].service.service_name, data))
        else:
            continue

    click.echo()
    utils.report_status("Found the following credentials")

    services = models.Service.select()
    for service in services:
        creds = service.credentials.where(models.Credential.state == models.Credential.WORKS)
        if len(creds) == 0:
            continue

        utils.report_success("{}/{}:{}/{} Succeeded!  Found credentials: {}".format(
            service.team.number, service.service_url, service.service_port, service.service_name,
            ",".join(map(str, creds))
        ))

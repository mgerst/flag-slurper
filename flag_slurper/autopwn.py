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
@click.option('-s', '--service-list', type=click.Path(), default=Project.default('services', 'services.yml'))
@click.option('-t', '--team-list', type=click.Path(), default=Project.default('teams', 'teams.yml'))
@click.option('-r', '--results', type=click.Path(), default=Project.default('results', 'results.yml'))
@click.option('-v', '--verbose', type=click.BOOL, default=False)
def pwn(service_list, team_list, results, verbose):
    utils.report_status("Starting AutoPWN")
    p = Project.get_instance()

    if p.enabled:
        utils.report_status("Loaded project from {}".format(p.base))
        service_list = p.base / service_list
        team_list = p.base / team_list
        results = p.base / results

    with open(str(team_list), 'r') as team_list, open(str(service_list), 'r') as service_list:
        teams = yaml.load(team_list)
        team_map = utils.get_team_map(teams)
        services = yaml.load(service_list)

    def team_name(number):
        return team_map[number]['name']

    pwn_results = {'scan_results': []}
    for team, services in services.items():
        utils.report_status("Checking team: {} ({})".format(team, team_name(team)))
        flags = p.flag(team)
        for service in services:
            service = autolib.coerce_service(service)
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
    for cred in autolib.credential_bag.credentials():
        pwn_results['creds'].append(cred)
        if len(cred.works):
            def display_service(service: autolib.Service):
                return "{}/{}".format(service.team_number, service.service_name)

            utils.report_success("Credential {} works on the following teams: \n\t- {}".format(cred, "\n\t- ".join(
                map(display_service, cred.works))))
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
@click.option('-r', '--results', type=click.Path(), default=Project.default('results', 'results.yml'))
def results(results):
    p = Project.get_instance()
    results = pathlib.Path(results)
    if p.enabled:
        results = p.base / results
    utils.report_status("Loading results from {}".format(results))

    with open(str(results), 'r') as results:
        pwn_results = yaml.load(results)

    if len(pwn_results['flags']) == 0:
        utils.report_warning('No Flags Found')
    else:
        utils.report_status("Found the following flags:")

        for flag in pwn_results['flags']:
            utils.report_success(
                "{}/{}: {} -> {}".format(flag.service.team_number, flag.service.service_name,
                                         flag.contents[0], flag.contents[1]))

    click.echo()
    utils.report_status("Found the following credentials")
    for scan in pwn_results['scan_results']:
        if scan.success:
            utils.report_success(scan)

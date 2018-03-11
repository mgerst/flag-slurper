from collections import defaultdict

import click
import pathlib
import yaml

from . import utils, autolib
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
@click.option('-s', '--service-list', type=click.File('r'), default=Project.default('services', 'services.yml'))
@click.option('-t', '--team-list', type=click.File('r'), default=Project.default('teams', 'teams.yml'))
@click.option('-r', '--results', type=click.File('w'), default=Project.default('results', 'results.yml'))
@click.option('-v', '--verbose', type=click.BOOL, default=False)
def pwn(service_list, team_list, results, verbose):
    utils.report_status("Starting AutoPWN")
    teams = yaml.load(team_list)
    team_map = utils.get_team_map(teams)
    services = yaml.load(service_list)

    def team_name(number):
        return team_map[number]['name']

    pwn_results = {'scan_results': []}
    for team, services in services.items():
        utils.report_status("Checking team: {} ({})".format(team, team_name(team)))
        for service in services:
            service = autolib.coerce_service(service)
            result = autolib.pwn_service(service)
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

    pwn_results['flags'] = autolib.flag_bag.flags
    yaml.dump(pwn_results, results, default_flow_style=False)


@autopwn.command()
@click.option('-s', '--service-list', type=click.Path(), default=Project.default('services', 'services.yml'))
@click.option('-t', '--team-list', type=click.Path(), default=Project.default('teams', 'teams.yml'))
def generate(service_list, team_list):
    service_list = pathlib.Path(service_list)
    team_list = pathlib.Path(team_list)

    p = Project.get_instance()
    if p.enabled:
        service_list = p.base / service_list
        team_list = p.base / team_list

    teams = utils.get_teams()

    with open(str(team_list), 'w') as fp:
        yaml.dump(teams, fp, default_flow_style=False)
        utils.report_success("Wrote team list to: {}".format(team_list))

    # TODO: When /services.json gets fixed, use get_services()
    service_status = utils.get_service_status()
    mapping = defaultdict(list)
    for status in service_status:
        for key in FILTERED_SERVICE_STATUS:
            del status[key]
        team_number = status['team_number']
        mapping[team_number].append(status)
    mapping = dict(mapping)

    with open(str(service_list), 'w') as fp:
        yaml.dump(mapping, fp, default_flow_style=False)
        utils.report_success("Wrote service list to: {}".format(service_list))


@autopwn.command()
@click.option('-r', '--results', type=click.File('r'), default=Project.default('results', 'results.yml'))
def results(results):
    pwn_results = yaml.load(results)

    if len(pwn_results['flags']) == 0:
        utils.report_warning('No Flags Found')
    else:
        utils.report_status("Found the following flags:")

        for flag in pwn_results['flags']:
            utils.report_success(
                "{}/{}: Has flag at {} with contents {}".format(flag.service.team_number, flag.service.service_name,
                                                                flag.contents[0], flag.contents[1]))

    click.echo()
    utils.report_status("Found the following credentials")
    for scan in pwn_results['scan_results']:
        if scan.success:
            utils.report_success(scan)

from collections import defaultdict

import click
import yaml

from . import utils, autolib
from .config import Config

pass_config = click.make_pass_decorator(Config)

FILTERED_SERVICE_STATUS = ['score', 'service_order', 'in_progress', 'service_details', 'service_status',
                           'public_visibility', 'blue_visibility', 'green_visibility', 'red_visibility',
                           'event_time']


@click.group()
def autopwn():
    pass


@autopwn.command()
@click.option('-s', '--service-list', type=click.File('r'), default='services.yml')
@click.option('-t', '--team-list', type=click.File('r'), default='teams.yml')
@click.option('-r', '--results', type=click.File('w'), default='results.yml')
@click.option('-v', '--verbose', type=click.BOOL, default=False)
@pass_config
def pwn(conf, service_list, team_list, results, verbose):
    utils.report_status("Starting AutoPWN")
    teams = yaml.load(team_list)
    team_map = utils.get_team_map(teams)
    services = yaml.load(service_list)

    def team_name(number):
        return team_map[number]['name']

    pwn_results = []
    for team, services in services.items():
        utils.report_status("Checking team: {} ({})".format(team, team_name(team)))
        for service in services:
            service = autolib.coerce_service(service)
            result = autolib.pwn_service(service)
            pwn_results.append(result)
            if result.success:
                utils.report_success(result)
            elif result.skipped:
                if verbose:
                    utils.report_warning(result)
            else:
                utils.report_error(result)
    yaml.dump(pwn_results, results, default_flow_style=False)

    for cred in autolib.credential_bag.credentials():
        if len(cred.works):
            def display_service(service: autolib.Service):
                return "{}/{}".format(service.team_number, service.service_name)

            utils.report_success("Credential {} works on the following teams: \n\t- {}".format(cred, "\n\t- ".join(map(display_service, cred.works))))
        else:
            utils.report_warning("Credential {} works on no teams".format(cred))


@autopwn.command()
@click.option('-s', '--service-list', type=click.File('w'), default='services.yml')
@click.option('-t', '--team-list', type=click.File('w'), default='teams.yml')
def generate(service_list, team_list):
    teams = utils.get_teams()
    yaml.dump(teams, team_list, default_flow_style=False)
    utils.report_success("Fetched team list")

    # TODO: When /services.json gets fixed, use get_services()
    service_status = utils.get_service_status()
    mapping = defaultdict(list)
    for status in service_status:
        for key in FILTERED_SERVICE_STATUS:
            del status[key]
        team_number = status['team_number']
        mapping[team_number].append(status)
    mapping = dict(mapping)
    yaml.dump(mapping, service_list, default_flow_style=False)
    utils.report_success("Fetched service list")


@autopwn.command()
@click.option('-r', '--results', type=click.File('r'), default='results.yml')
def results(results):
    results = yaml.load(results)
    success = list(filter(lambda r: r.success, results))
    skipped = list(filter(lambda r: r.skipped, results))
    failures = list(filter(lambda r: not r.success and not r.skipped, results))

    utils.report_success("Successful pwns: {}".format(len(success)))
    utils.report_warning("Skipped pwns: {}".format(len(skipped)))
    utils.report_error("Failed pwns: {}".format(len(failures)))

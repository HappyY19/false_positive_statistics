"""
pyinstaller -y -F --clean false_positive_statistics.py
"""
import csv
import logging
import pathlib
from CheckmarxPythonSDK.CxODataApiSDK.ProjectsODataAPI import (
    get_all_scan_ids_within_a_predefined_time_range_for_all_projects_in_a_team,
    get_all_projects_id_name_and_team_id_name,
)
from CheckmarxPythonSDK.CxODataApiSDK.ResultsODataAPI import (
    get_number_of_results_for_a_specific_scan_id_with_result_state,
)

# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


def get_command_line_arguments():
    """

    Returns:
        Namespace
    """
    import argparse
    description = 'A simple command-line interface for CxSAST in Python.'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--cxsast_base_url', required=True, help="CxSAST base url, for example: https://localhost")
    parser.add_argument('--cxsast_username', required=True, help="CxSAST username")
    parser.add_argument('--cxsast_password', required=True, help="CxSAST password")
    parser.add_argument('--start_date', help="example: 2023-07-01")
    parser.add_argument('--end_date', help="example: 2023-08-08")
    parser.add_argument('--report_file_path', help="report file path")
    arguments = parser.parse_known_args()
    arguments = arguments[0]

    args = {
        "cxsast_base_url": arguments.cxsast_base_url,
        "cxsast_username": arguments.cxsast_username,
        "start_date": arguments.start_date,
        "end_date": arguments.end_date,
        "report_file_path": arguments.report_file_path
    }
    logger.info(args)
    return args


def get_data(args):
    start_date = args.get("start_date")
    end_date = args.get("end_date")
    result = []
    projects_teams = get_all_projects_id_name_and_team_id_name()
    team_id_list = [item.get("TeamId") for item in projects_teams]
    team_id_set = set(team_id_list)
    for team_id in team_id_set:
        projects = get_all_scan_ids_within_a_predefined_time_range_for_all_projects_in_a_team(
            team_id=team_id, start_date=start_date, end_date=end_date
        )
        updated_projects = [
            {
                "project_name": project.get("Name"),
                "scan_id": project.get("Scans")[-1].get("Id") if len(project.get("Scans")) > 0 else None
            }
            for project in projects
        ]
        for project in updated_projects:
            scan_id = project.get("scan_id")
            if scan_id is None:
                continue
            number_of_not_exploitable = get_number_of_results_for_a_specific_scan_id_with_result_state(
                scan_id=scan_id, result_states=["NOT_EXPLOITABLE"]
            )
            if number_of_not_exploitable == 0:
                continue
            project.update({"number_of_not_exploitable": number_of_not_exploitable})
            result.append(project)
    return result


def create_csv_file(args, data):
    default_file_name = "/number_of_not_exploitable_for_each_project.csv"
    report_path = args.get("report_file_path")
    if report_path is None:
        report_path = "." + default_file_name
    path = pathlib.Path(report_path)
    if path.is_dir():
        report_path += default_file_name
    with open(report_path, 'w', newline='') as csvfile:
        fieldnames = ['project_name', 'scan_id', 'number_of_not_exploitable']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for item in data:
            writer.writerow(item)


if __name__ == '__main__':
    cli_args = get_command_line_arguments()
    api_data = get_data(cli_args)
    create_csv_file(cli_args, api_data)


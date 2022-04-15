'''
WakaTime progress visualizer
'''

import base64
import datetime
import os
import re
import sys

import requests
from github import Github, GithubException

START_COMMENT = '<!--START_SECTION:waka-->'
END_COMMENT = '<!--END_SECTION:waka-->'
GRAPH_LENGTH = 25
TEXT_LENGTH = 16
listReg = f"{START_COMMENT}[\\s\\S]+{END_COMMENT}"

repository = os.getenv('INPUT_REPOSITORY')
waka_key = os.getenv('INPUT_WAKATIME_API_KEY')
api_base_url = os.getenv('INPUT_API_BASE_URL')
ghtoken = os.getenv('INPUT_GH_TOKEN')
show_title = os.getenv("INPUT_SHOW_TITLE")
show_total = os.getenv("INPUT_SHOW_TOTAL")
commit_message = os.getenv("INPUT_COMMIT_MESSAGE")
blocks = os.getenv("INPUT_BLOCKS")
show_time = os.getenv("INPUT_SHOW_TIME")


def this_week() -> str:
    '''Returns a week streak'''
    week_end = datetime.datetime.today() - datetime.timedelta(days=1)
    week_start = week_end - datetime.timedelta(days=6)
    print("Week header created")
    return f"Week: {week_start.strftime('%d %B, %Y')} - {week_end.strftime('%d %B, %Y')}"


def get_stats() -> str:
    '''Gets API data and returns markdown progress'''
    encoded_key: str = str(base64.b64encode(waka_key.encode('utf-8')), 'utf-8')
    data = requests.get(
        f"{api_base_url.rstrip('/')}/v1/users/current/stats/last_7_days",
        headers={
            "Authorization": f"Basic {encoded_key}"
        }).json()
    try:
        lang_data = data['data']['languages']
        total_data = data['data']['human_readable_total']
    except KeyError:
        print("Please Add your WakaTime API Key to the Repository Secrets")
        sys.exit(1)

    data_list = []
    for lang in lang_data[:10]:
        if lang['hours'] == 0 and lang['minutes'] == 0:
            continue
        if lang['name'] == 'Other':
            continue
        if lang['percent'] < 5:
            continue
        # following line provides a neat finish
        data_list.append(
            f""" "{lang['name']}" : {float(lang['decimal'])}""")
    print("Graph Generated")
    data = '\n'.join(data_list)

    return_text = '```mermaid\n pie\n'
    if show_title == 'true':
        print("Stats with Weeks in Title Generated")
        return_text += 'title ' + this_week() + '\n'
    if show_total == 'true':
        print("add Total time")
        return_text += 'title Total: ' + total_data + '\n'
    return return_text + data + '\n```'


def decode_readme(data: str) -> str:
    '''Decode the contents of old readme'''
    decoded_bytes = base64.b64decode(data)
    return str(decoded_bytes, 'utf-8')


def generate_new_readme(stats: str, readme: str) -> str:
    '''Generate a new Readme.md'''
    stats_in_readme = f"{START_COMMENT}\n{stats}\n{END_COMMENT}"
    return re.sub(listReg, stats_in_readme, readme)


if __name__ == '__main__':
    g = Github(ghtoken)
    try:
        repo = g.get_repo(repository)
    except GithubException:
        print("Authentication Error. Try saving a GitHub Token in your Repo Secrets" +
              " or Use the GitHub Actions Token, which is automatically used by the action.")
        sys.exit(1)
    contents = repo.get_readme()
    waka_stats = get_stats()
    rdmd = decode_readme(contents.content)
    new_readme = generate_new_readme(stats=waka_stats, readme=rdmd)
    if new_readme != rdmd:
        repo.update_file(path=contents.path, message=commit_message,
                         content=new_readme, sha=contents.sha)

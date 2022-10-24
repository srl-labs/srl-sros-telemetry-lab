#!/usr/bin/python
###########################################################################
# Description:
#
# Copyright (c) 2020 Nokia
###########################################################################
from srlinux.location.build_path import build_path
from srlinux.mgmt.cli.tools_plugin import ToolsPlugin
from srlinux.mgmt.cli.required_plugin import RequiredPlugin
from srlinux.schema.data_store import DataStore
from srlinux.syntax import Syntax
from srlinux.mgmt.cli.parse_error import ParseError

from srlinux.schema.data_store import DataStore
import requests
import json

class Plugin(ToolsPlugin):
    '''
        git
    '''

    def get_required_plugins(self):
        return [
            RequiredPlugin('tools_mode')
        ]
    def on_tools_load(self, state):
        syntax_git = Syntax('git', 
            help='`Git interaction as a client`')
        git = state.command_tree.tools_mode.root.add_command(syntax_git,
            update_location=False)

        syntax_branch = Syntax('branch', 
            help='git branch creates a branch in github')
        branch = git.add_command(syntax_branch, 
            update_location=False, 
            callback=git_branch_process)
        
        syntax_commit = (Syntax(
            'commit', 
            help='git commit commits the startup config in github')
            .add_unnamed_argument('commitMessage',
                help='commitMessage for the commit'))
        commit = git.add_command(syntax_commit, 
            update_location=False,
            callback=git_commit_process)

        syntax_pull_request = (Syntax(
            'pull-request', 
            help='git pull-request creates a pull request based on the commits in github')
            .add_unnamed_argument('prSubject',
                help='pull request subject fir the pull-request')
            .add_unnamed_argument('prDescription',
                help='pull request Description for the pull-request'))
        pull_request = git.add_command(syntax_pull_request, 
            update_location=False,
            callback=git_pullrequest_process)

def git_branch_process(state, output, arguments, **_kwargs):
    #print(state.server_data_store)
    #print(arguments)
    action_arg = {}

    yang_val, result_string = yang_validation(state)
    if yang_val:
        git_rpc_call('Server.Branch', action_arg, output)
    else:
        output.print_error_line(result_string)


def git_commit_process(state, output, arguments, **_kwargs):
    #print(state.server_data_store)
    #print(arguments)
    action_arg = {}
    action_arg['comment'] = arguments.get('commitMessage')

    yang_val, result_string = yang_validation(state)
    if yang_val:
        git_rpc_call('Server.Commit', action_arg, output)
    else:
        output.print_error_line(result_string)


def git_pullrequest_process(state, output, arguments, **_kwargs):
    #print(state.server_data_store)
    #print(arguments)
    action_arg = {}
    action_arg['subject'] = arguments.get('prSubject')
    action_arg['comment'] = arguments.get('prDescription')
    
    yang_val, result_string = yang_validation(state)
    if yang_val:
        git_rpc_call('Server.PullRequest', action_arg, output)
    else:
        output.print_error_line(result_string)


def yang_validation(state):
    path = build_path('/git-client')
    result = state.server_data_store.get_json(
        path, 
        recursive=True,
        include_field_defaults=True)

    result_json_obj = json.loads(result)
    #print(result_json_obj)

    org_exists = 'organization' in result_json_obj
    own_exists = 'owner' in result_json_obj
    r_exists = 'repo' in result_json_obj
    b_exists = 'repo' in result_json_obj
    f_exists = 'filename' in result_json_obj
    t_exists = 'token' in result_json_obj
    a_exists = 'author' in result_json_obj
    ae_exists = 'author-email' in result_json_obj

    result_string = "Please define the following comamnds before running the git commands: "
    yang_val = True

    if (not org_exists) and (not own_exists):
        result_string += "organizaton or owner "
        yang_val = False
    if not r_exists:
        result_string += " repo"
        yang_val = False
    if not b_exists:
        result_string += " branch"
        yang_val = False
    if not f_exists:
        result_string += " filename"
        yang_val = False
    if not t_exists:
        result_string += " token"
        yang_val = False
    if not a_exists:
        result_string += " author"
        yang_val = False
    if not ae_exists:
        result_string += " author-email"
        yang_val = False

    return yang_val, result_string

def git_rpc_call(method, action_args, output):
    url = "http://localhost:7777"

    s_exists = 'subject' in action_args
    if s_exists:
        subject = action_args['subject']
    else:
        subject = 'dummy'

    c_exists = 'comment' in action_args
    if s_exists:
        comment = action_args['comment']
    else:
        comment = 'dummy'

    payload = {
        "method": method,
        "params": [{"Subject": subject, "Comment": comment}],
        "jsonrpc": "2.0",
        "id": 0,
    }
    response = requests.post(url, json=payload).json()

    if response["result"] != 'success':
        output.print_error_line(response["result"])
    assert response["id"] == 0
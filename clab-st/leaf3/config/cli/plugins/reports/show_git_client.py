#!/usr/bin/python
###########################################################################
# Description:
#
# Copyright (c) 2020 Nokia - modified by Wim henderickx
###########################################################################
from srlinux.mgmt.cli import CliPlugin
from srlinux.syntax import Syntax
from srlinux.schema import FixedSchemaRoot
from srlinux.location import build_path
from srlinux import strings
from srlinux.data import Border, ColumnFormatter, TagValueFormatter, Borders, Data, Indent
import json

class Plugin(CliPlugin):
    '''
        Adds a show command for the git client. 
    '''
    def load(self, cli, **_kwargs):
        cli.show_mode.add_command(
            Syntax(
                'git-client', 
                help='show command for the git-client'
            ),
            update_location=False,
            callback=self._print, 
            schema=self._get_schema(),
        )
    def _print(self, state, arguments, output, **_kwargs):
        self._fetch_state(state)
        result = self._populate_data(state, arguments) 
        self._set_formatters(result) 
        output.print_data(result)

    def _get_schema(self):
        root = FixedSchemaRoot()
        git_client = root.add_child(
            'GitClient',
            fields=[
                'organization',
                'owner',
                'repo', 
                'branch', 
                'filename', 
                'author', 
                'author-email', 
                'oper-state']
        )
        git_client.add_child(
            'statistics',
            fields=[
                'success', 
                'failure']
        )
        return root

    def _fetch_state(self, state):
        path = build_path('/git-client')
        self._server_data = state.server_data_store.get_data(
            path, 
            recursive=True) 
        #    include_container_children=True,
        #    include_field_defaults=True)


    def _populate_data(self, state, arguments):
        result = Data(arguments.schema)
        print(self._server_data.git_client.get())
        data = result.gitclient.create()
        print(data)
        data.organization = self._server_data.git_client.get().organization or '<Unknown>'
        data.owner = self._server_data.git_client.get().owner or '<Unknown>'
        data.repo = self._server_data.git_client.get().repo or '<Unknown>'
        data.branch = self._server_data.git_client.get().branch or '<Unknown>'
        data.filename = self._server_data.git_client.get().filename or '<Unknown>'
        data.author = self._server_data.git_client.get().author or '<Unknown>'
        data.author_email = self._server_data.git_client.get().author_email or '<Unknown>'
        data.oper_state = self._server_data.git_client.get().oper_state or '<Unknown>'
        print(data)
        
        self._add_children(data) 
        
        return result

    def _add_children(self, data):
        child = data.statistics.create()
        child.success = self._server_data.git_client.get().statistics.get().success
        child.failure = self._server_data.git_client.get().statistics.get().failure
    
    def _set_formatters(self, data): 
        data.set_formatter(
            '/GitClient',
            Border(TagValueFormatter(), Border.Above | Border.Below | Border.Between, '='))

        data.set_formatter(
            '/GitClient/statistics',
            Indent(ColumnFormatter(ancestor_keys=False, borders=Borders.Header), indentation=2))
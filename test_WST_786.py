import os
from pathlib import Path
import pytest
from deepdiff import DeepDiff
from helpers import assertion_messages
from fsa import fsa_utils
from qa_ws_api_utils import projects_utils, ws_api_requests_utils
from qa_utils import files_content_utils

from general_tools import general_tools, general_plugin_tools


class cfg():
    project_token = ''
    product_token = ''
    product_name: str = 'WST_786'
    project_name: str = 'WST_786'
    invocation_line: list = ['-d', 'Data']
    expected_licenses: dict = {'threaded_in_memory_queue-0.0.4.gem': {'MIT'}, 'chalk-0.0.2.gem': {'MIT'},
                               'a-0.1.1.gem': {'Requires Review'}, 'proc_to_lambda-1.0.0.gem': {'MIT'},
                               'q-0.0.1.gem': {'MIT'}}


@pytest.mark.xfail(reason='failed for a while(last two sprint) we need to investigate')
@pytest.mark.testrail_id('2202')
@pytest.mark.ruby
@pytest.mark.rubygems
@pytest.mark.usefixtures("fsa_env")
class TestWST786:
    """
        Assert licenses
    """

    def before(self, fsa_env):
        os.chdir(str(Path(__file__).resolve().parent))
        cfg.product_token = general_tools.prepare_product(fsa_env['api_url'], fsa_env['organization_token'],
                                                          cfg.product_name, fsa_env['user_id'])

        files_content_utils.update_config_file(fsa_utils.get_default_fsa_config_filename(),
                                               fsa_utils.get_default_fsa_config_keys_values(fsa_env))

    @pytest.fixture()
    def before_and_after(self, fsa_env):
        self.before(fsa_env)
        yield

    def test_run(self, static_paths, fsa_env, before_and_after):
        # Run FSA
        fsa_output = fsa_utils.run_fsa(static_paths['path_to_fsa_jar'], cfg.invocation_line)

        # Extract the support token
        support_token = general_plugin_tools.extract_support_token('fsa', fsa_output)

        # Wait until the project update is finished
        ws_api_requests_utils.wait_until_request_is_finished(fsa_env['api_url'], fsa_env['organization_token'],
                                                             support_token)

        # Get the project token
        cfg.project_token = projects_utils.get_project_token_by_name(fsa_env['api_url'], cfg.product_token,
                                                                     cfg.project_name)

        # Assert the project token is not empty (In other words, there is a project with the expected name under that product)
        assert cfg.project_token != '', assertion_messages.project_does_not_exist_under_product_error_message(
            cfg.project_name, cfg.product_name)

        # Get the actual licenses
        actual_licenses = projects_utils.get_project_licenses_list(fsa_env['api_url'], cfg.project_token)

        # Assert licenses
        licenses_diff = DeepDiff(actual_licenses,
                                 cfg.expected_licenses, ignore_order=True)
        assert licenses_diff == {}, assertion_messages.generic_diff_error_message(cfg.project_name, 'libraries licenses',
                                                                                  licenses_diff)

import random

from util.data_preparation.prepare_data_common import __write_to_file
from util.common_util import print_timing
from util.api.confluence_clients import ConfluenceRestClient, ConfluenceRpcClient
import util.pmc.constants as pmc_constants
import util.pmc.paths as pmc_paths

TASK_PAGE_TITLE_PREFIX = pmc_constants.PAGE_TITLE_TOKEN + ' loadtest data tasks for '
SPACE_KEY_TASK_PAGES = 'PMSADCCS'
SPACE_KEY_COMMENT_AGGREGATION_MACRO = 'PDCCAM'

# spaces created with modified PMC app contain this token in the title
SPACE_TITLE_TOKEN_MASSDATA = 'PMCMassData'


def _extract_id_of_global_metadata_field(metadata_fields, metadata_field_key):
    for metadata_field in metadata_fields:
        if metadata_field['spaceKey'] == '' and metadata_field['key'] == metadata_field_key:
            return metadata_field['id']
    raise SystemExit(f"Global Metadata field with key {metadata_field_key} does not exist")


def _extract_ids_of_global_metadata_fields(metadata_fields, metadata_field_keys):
    field_ids = list()
    for field_key in metadata_field_keys:
        field_ids.append(_extract_id_of_global_metadata_field(metadata_fields, field_key))
    return ",".join(str(x) for x in field_ids)


def _check_space_for_blueprint_tests(confluence_rest_client: ConfluenceRestClient):
    space = confluence_rest_client.get_space_by_key(pmc_constants.SPACE_KEY_BLUEPRINT_TEST)
    if not space:
        raise SystemExit(f"Space with key {pmc_constants.SPACE_KEY_BLUEPRINT_TEST} does not exist. "
                         f"Please import the prepared space export.")
    if space['name'] != pmc_constants.SPACE_TITLE_BLUEPRINT_TEST:
        raise SystemExit(f"Space with key {pmc_constants.SPACE_KEY_BLUEPRINT_TEST} does not have the expected title "
                         f"(expected: {pmc_constants.SPACE_TITLE_BLUEPRINT_TEST}, actual: {space['name']}). "
                         f"Please import the prepared space export.")


def _check_space_with_mass_data(confluence_rest_client: ConfluenceRestClient):
    """
    Check whether there is at least one space which could/should contain PMC mass data. This test is mainly needed to
    ensure that a space with a title which contains a certain token exists. If there is no such space other preparation
    steps will fail because CQL is buggy will not return any results.
    @param confluence_rest_client: the Confluence client to query the REST API
    """
    cql_query = f"type = space and title ~ {SPACE_TITLE_TOKEN_MASSDATA}"
    spaces = confluence_rest_client.search(cql=cql_query, limit=1)
    if not spaces:
        raise SystemExit(f"Space containing the PMC mass data does not exist. For development it might be enough to "
                         f"just create a space whose title contains '{SPACE_TITLE_TOKEN_MASSDATA}'. For real test "
                         f"runs you have to use the modified PMC app to generate the mass data.")


def _create_confluence_task_list_xhtml(user_name, task_count):
    xhtml = '<ac:task-list>'
    task_id = 1990
    for i in range(task_count):
        day = (i % 31) + 1
        xhtml += f'<ac:task><ac:task-id>{task_id}</ac:task-id><ac:task-status>incomplete</ac:task-status>' \
                 f'<ac:task-body>Task {i}&nbsp;<ac:link><ri:user ri:username="{user_name}" /></ac:link>' \
                 f'<time datetime="2025-12-{day}" /></ac:task-body></ac:task> '
        task_id += 1
    xhtml += '</ac:task-list>'
    return xhtml


def _create_page_with_tasks(confluence_rest_client: ConfluenceRestClient, user_name):
    print(f"Creating page with tasks for user {user_name}")
    page_title = TASK_PAGE_TITLE_PREFIX + user_name
    page_body = ("<p><strong>Additional tasks for " + user_name + ":</strong></p><p><br /></p>"
                 + _create_confluence_task_list_xhtml(user_name, random.randint(10, 30))
                 + "<p><br /></p>")
    page_data = {"type": "page",
                 "title": page_title,
                 "body": {"storage": {"value": page_body, "representation": "storage"}},
                 "space": {"key": SPACE_KEY_TASK_PAGES}}

    confluence_rest_client.create_page(page_data)


def _create_pages_with_tasks(confluence_rest_client: ConfluenceRestClient, users):
    confluence_rest_client.assert_space_exists(SPACE_KEY_TASK_PAGES,
                                               f'Space with key {SPACE_KEY_TASK_PAGES} please import the space export')
    user_names = [user['user']['username'] for user in users]
    page_titles = _get_titles_of_existing_task_pages(confluence_rest_client)
    for user_name in user_names:
        if not (TASK_PAGE_TITLE_PREFIX + user_name) in page_titles:
            _create_page_with_tasks(confluence_rest_client, user_name)


def _get_titles_of_existing_task_pages(confluence_rest_client: ConfluenceRestClient):
    pages = list()
    start_offset = 0
    fetch_limit = 500
    cql_query = f'type=page and space={SPACE_KEY_TASK_PAGES} and title ~ "{TASK_PAGE_TITLE_PREFIX}"'
    while True:
        try:
            found_pages = confluence_rest_client.get_content_search(start_offset, fetch_limit, cql=cql_query, expand='')
            if found_pages:
                pages.extend(found_pages)
            if len(found_pages) < fetch_limit:
                break
            start_offset += fetch_limit
        except Exception:
            print("No existing task pages found.")
            return list()

    return [page['title'] for page in pages]


def _get_pages_with_macro(confluence_rest_client, count, macro_name, space_key=None, expand='space'):
    # title condition is used to limit results to prepared PMC content provided via space exports and ignore pages in
    # the demo space because there pages can contain more than one macro)
    cql = f'type=page and title ~ {pmc_constants.PAGE_TITLE_TOKEN} and macro = "{macro_name}"'
    if space_key:
        cql += ' and space = ' + space_key
    else:
        # ignore space in which tests create content via PMC blueprints. Note: CQL will fail w/ exception when space
        # does not exist!
        cql += ' and space != ' + pmc_constants.SPACE_KEY_BLUEPRINT_TEST
        # ignore pages in mass data spaces as they contain more than one macro. Note: CQL will fail w/ exception or
        # return empty result when space does not exist!
        cql += ' and space.title !~ ' + SPACE_TITLE_TOKEN_MASSDATA

    pages = confluence_rest_client.get_content_search(0, count, cql, expand)
    if not pages:
        raise SystemExit(f"There is no page with macro {macro_name} in Confluence. You might have to import a "
                         f"prepared space export or your search index is broken")

    return pages


def _get_comment_aggregation_macro_data(confluence_rest_client: ConfluenceRestClient, count):
    confluence_rest_client.assert_space_exists(SPACE_KEY_COMMENT_AGGREGATION_MACRO,
                                               f"Space with key {SPACE_KEY_COMMENT_AGGREGATION_MACRO} does not exist. "
                                               f"Please import the prepared space export.")
    pages = _get_pages_with_macro(confluence_rest_client, count, 'display-process-comments',
                                  SPACE_KEY_COMMENT_AGGREGATION_MACRO, 'space,body.storage')
    macro_data = []
    for page in pages:
        body_value = page['body']['storage']['value']
        mode = 'unresolved' if 'showing unresolved comments' in body_value else 'resolved'
        page_info = f'{page["id"]},{page["space"]["key"]},{mode}'
        macro_data.append(page_info)
    return macro_data


def _check_process_search_data(confluence_rest_client: ConfluenceRestClient):
    pages = confluence_rest_client.get_content_search(
        0, 5, cql='type=page'
                  ' and metadataset = "global.metadataset.communardoqmsprocesstype"'
                  ' and space != ' + pmc_constants.SPACE_KEY_BLUEPRINT_TEST +
                  ' order by title')
    if len(pages) < 5:
        raise SystemExit(f"There are not enough Process Type pages in Confluence (minimum: 5, actual: {len(pages)}). "
                         "Please use the mass data generator. For your development environment you can also add the "
                         "missing process types manually. In that case please also add at least 1 process for the type "
                         "and at least 1 sub process to the process.")
    # ensure that each of the process types has at least one process
    for page in pages:
        _assert_process_type_has_processes_and_subprocesses(confluence_rest_client, page)


def _assert_process_type_has_processes_and_subprocesses(rest_client: ConfluenceRestClient, process_type_page):
    process_type_id = process_type_page['id']
    process_type_title = process_type_page['title']
    # fetching 12 items as the Process Search macro would do
    url = (rest_client.host
           + '/rest/communardo/qms/latest/process-search/process-pages?limit=12&offset=0'
           + '&metadataSetProcess=global.metadataset.communardoqmsprocess'
           + '&metadataFieldProcessType=global.metadatafield.communardoqmsprocesstype'
           + '&metadataFieldProcessGoals=global.metadatafield.communardoqmsprocess'
           + '&processTypePagePageId=' + process_type_id)
    error_message = f"Getting processes of process type '{process_type_title}' ({process_type_id}) failed"
    process_pages = rest_client.get(url,error_message).json()['results']
    if not process_pages:
        raise SystemExit(f"The process type '{process_type_title}' ({process_type_id}) has no processes. Use the mass "
                         f"data generator to prepare Confluence. For your development environment you can also prepare "
                         f"data manually by creating a process for the type and adding a sub process to the process.")
    sub_processes_found = False
    for process_page in process_pages:
        # check if process has sub-processes
        if process_page['hasChildren']:
            sub_processes_found = True
            break

    if not sub_processes_found:
        raise SystemExit(f"The process type '{process_type_title}' ({process_type_id}) has processes but none of the "
                         f"first 12 processes (ordered by title) has sub-processes. Use the mass data generator to "
                         f"prepare Confluence. For your development environment you can also add a sub process "
                         f"manually to any of the first 12 processes.")


def _prepare_data_for_contact_person_macro(confluence_rest_client: ConfluenceRestClient,
                                           confluence_rpc_client: ConfluenceRpcClient):
    space_key = "PPTSO"
    username = "contact_person"
    user_list = confluence_rest_client.get_users(username, 1)
    if not user_list:
        confluence_rpc_client.create_user(username, username)
        raise SystemExit(f"User {username} has been created. Metadata can now be imported into space {space_key}.")

    confluence_rest_client.assert_space_exists(space_key, f"Space with key {space_key} does not exist but is required"
                                                          f" for contact person macro tests. Please import the prepared"
                                                          f" space export and the Metadata for that space.")
    cql_query = f'type=page and space = {space_key} and metadataset = "metadataset.spacelocaldemosetone"'
    pages = confluence_rest_client.get_content_search(0, 1, cql = cql_query)
    if not pages:
        raise SystemExit(f"Expected Metadata of space {space_key} is missing. Please import it into the space.")


def _write_pmc_datasets_to_file(pmc_datasets):
    for macro_name in pmc_constants.MACRO_NAMES:
        pages = [f"{page['id']},{page['space']['key']}" for page in pmc_datasets[macro_name]]
        __write_to_file(pmc_paths.get_macro_csv_file(macro_name), pages)

    __write_to_file(pmc_paths.get_comment_aggregation_macro_data_csv_file(),
                                         pmc_datasets[pmc_constants.COMMENT_AGGREGATION_DATA])


@print_timing('Process Management Suite data preparation')
def prepare_pmc_data(confluence_rest_client: ConfluenceRestClient, confluence_rpc_client: ConfluenceRpcClient, dataset):
    _check_space_for_blueprint_tests(confluence_rest_client)
    _check_space_with_mass_data(confluence_rest_client)
    _check_process_search_data(confluence_rest_client)
    _create_pages_with_tasks(confluence_rest_client, dataset['users'])
    _prepare_data_for_contact_person_macro(confluence_rest_client, confluence_rpc_client)
    # pages which contain the given macro but no other macros
    pmc_datasets = dict()
    for macro_name in pmc_constants.MACRO_NAMES:
        pmc_datasets[macro_name] = _get_pages_with_macro(confluence_rest_client, 20, macro_name)
    pmc_datasets[pmc_constants.COMMENT_AGGREGATION_DATA] = _get_comment_aggregation_macro_data(confluence_rest_client,
                                                                                               20)
    _write_pmc_datasets_to_file(pmc_datasets)

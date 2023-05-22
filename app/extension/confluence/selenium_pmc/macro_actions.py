import random

from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import text_to_be_present_in_element,\
    visibility_of_element_located, staleness_of
from selenium.webdriver.support.wait import WebDriverWait

import util.pmc.constants as pmc_constants
from selenium_ui.base_page import AnyEc
from selenium_ui.confluence.pages.pages import Page
from selenium_ui.conftest import print_timing

COMMENT_AGGREGATION_TIMING_PREFIX = "selenium_comment_aggregation_macro"
PROCESS_SEARCH_TIMING_PREFIX = "selenium_process_search_macro"


def _get_random_macro_dataset_entry(datasets, dataset_identifier):
    return random.choice(datasets[dataset_identifier])


def _measure_view_page_with_macro(page_with_macro: Page, visibility_locator, timing_label):
    @print_timing(f"{timing_label}:view_page")
    def open_page_and_wait_until_loaded():
        page_with_macro.go_to()
        page_with_macro.wait_for_page_loaded()
        if visibility_locator:
            page_with_macro.wait_until_visible(visibility_locator, timeout=10)

    open_page_and_wait_until_loaded()


def _simple_macro_scenario(webdriver, datasets, macro_name, visibility_locator, timing_label):
    macro_dataset_entry = _get_random_macro_dataset_entry(datasets, macro_name)
    page = Page(webdriver, page_id=macro_dataset_entry[0])
    _measure_view_page_with_macro(page, visibility_locator, timing_label)


def _measure_comment_aggregation_resolve_unresolve(page_with_macro: Page, showing_resolved_comments):
    first_comment_css_selector = ".conf-macro .communardo-qms-display-process-comments-list ul li:first-child"
    btn_locator = (By.CSS_SELECTOR,
                   f"{first_comment_css_selector} .communardo-qms-display-process-comments-actions > button")

    @print_timing(f"{COMMENT_AGGREGATION_TIMING_PREFIX}:resolve_comment")
    def resolve_first_comment():
        page_with_macro.wait_until_visible(btn_locator, 10).click()
        # after successfully resolving the comment is still shown but the status lozenge is changed
        page_with_macro.wait_until_visible((By.CSS_SELECTOR, f"{first_comment_css_selector} .aui-lozenge-success"), 10)

    @print_timing(f"{COMMENT_AGGREGATION_TIMING_PREFIX}:unresolve_comment")
    def unresolve_first_comment():
        page_with_macro.wait_until_visible(btn_locator, 10).click()
        # after successfully resolving the comment is still shown but the status lozenge is changed
        page_with_macro.wait_until_visible((By.CSS_SELECTOR, f"{first_comment_css_selector} .aui-lozenge-complete"), 10)

    # order of operations depends on what is currently rendered. We always do both operations to undo the change so that
    # macro is not running out of resolved or unresolved comments if test is run many times.
    if showing_resolved_comments:
        unresolve_first_comment()
        resolve_first_comment()
    else:
        resolve_first_comment()
        unresolve_first_comment()


def _measure_comment_aggregation_load_more(page_with_macro: Page):
    @print_timing(f"{COMMENT_AGGREGATION_TIMING_PREFIX}:load_more")
    def click_load_more_and_wait_until_loaded():
        # have to use JavaScript to click the load more button because Selenium clicks are ignored, although no error is
        # logged and page_with_macro.wait_until_clickable(locator) works w/o problems. Possible reason could be QMS-681
        # and the incorrectly set aria-disabled attribute on the button.
        page_with_macro.execute_js(
            "document.querySelector('.conf-macro button.communardo-qms-display-process-comments-load-more').click()")
        # after loading more another UL with the next result set is added to the comments-list, thus, after first click
        # there will be 2 ULs
        second_result_set_locator = (By.CSS_SELECTOR,
                                     ".conf-macro .communardo-qms-display-process-comments-list ul:nth-child(even) "
                                     ".communardo-qms-display-process-comments-comment-title")
        page_with_macro.wait_until_visible(second_result_set_locator, 10)

    click_load_more_and_wait_until_loaded()


def _comment_aggregation_macro_scenarios(webdriver, datasets):
    comment_aggregation_macro_data = _get_random_macro_dataset_entry(datasets, pmc_constants.COMMENT_AGGREGATION_DATA)
    page = Page(webdriver, page_id=comment_aggregation_macro_data[0])
    _measure_view_page_with_macro(page,
                                  (By.CSS_SELECTOR,
                                      ".conf-macro .communardo-qms-display-process-comments-comment-title"),
                                  COMMENT_AGGREGATION_TIMING_PREFIX)

    # resolve / unresolve and load_more is not run in every iteration as these are not so common scenarios
    # important: resolve / unresolve test always has to be run before load more otherwise the first-comment CSS selector
    # used there will not work
    if random.randint(1, 100) <= 18:
        _measure_comment_aggregation_resolve_unresolve(page, comment_aggregation_macro_data[2] == 'resolved')
    if random.randint(1, 100) <= 25:
        _measure_comment_aggregation_load_more(page)


def _measure_process_search_explore_processes_actions(page: Page):
    @print_timing(f"{PROCESS_SEARCH_TIMING_PREFIX}:explore_processes")
    def click_process_type_tile_and_wait_until_processes_loaded():
        tiles = page.get_elements((By.CSS_SELECTOR, ".communardo-qms-process-search-processtype-tile"))
        # select one of the first 5 tiles randomly and click it (preparation code ensures that the first 5 process types
        # all have at least 1 process)
        tiles[random.randint(0, 4)].click()
        page.wait_until_visible((By.CSS_SELECTOR, ".communardo-qms-process-search-processpage-PROCESS"), 10)

    click_process_type_tile_and_wait_until_processes_loaded()


def _measure_process_search_explore_subprocesses_actions(page: Page):
    @print_timing(f"{PROCESS_SEARCH_TIMING_PREFIX}:explore_subprocesses")
    def click_process_tile_and_wait_until_subprocesses_loaded():
        # pick a random tile which has sub processes
        tiles = page.get_elements(
            (By.CSS_SELECTOR,
             '.communardo-qms-process-search-result-tile[data-communardo-qms-process-page-has-children="true"]'))
        tile = tiles[random.randint(0, len(tiles) - 1)]
        # click on the title in the tile to ensure we are really clicking the tile and not the button or the fav icon
        
        tile.find_element(By.CSS_SELECTOR, ".communardo-qms-process-search-page-title span").click()
        # wait for sub process tile being loaded
        page.wait_until_visible((By.CSS_SELECTOR, ".communardo-qms-process-search-processpage-SUB_PROCESS"), 10)

    click_process_tile_and_wait_until_subprocesses_loaded()


def _measure_process_search_full_text_search(page: Page, search_term):
    @print_timing(f"{PROCESS_SEARCH_TIMING_PREFIX}:search")
    def insert_search_term_and_start_search():
        result_tiles_element = page.get_element((By.CSS_SELECTOR, ".communardo-qms-process-search-result-tiles"))
        input_elem = page.get_element((By.CSS_SELECTOR, ".communardo-qms-process-search-fulltext-input-wrapper input"))
        input_elem.send_keys(search_term)
        page.get_element((By.CSS_SELECTOR, ".communardo-qms-process-search-fulltext-input-wrapper button")).click()
        # as workaround for QMS-754 we selected a process type so that the macro already shows processes. Since a search
        # can also return processes we have to make sure that we really wait until the search is done. So wait for the
        # results container to become stale because the node is replaced when the search completed
        WebDriverWait(page.driver, timeout=10).until(staleness_of(result_tiles_element),
                                                     message="Timeout while waiting for old results to be replaced")
        # like in real life some search terms will lead to results and some won't. We support both and wait until
        # found content is shown or we see the message that no results exist.
        nothing_found_condition = text_to_be_present_in_element(locator=(By.CSS_SELECTOR,
                                                                         ".communardo-qms-process-search-results"),
                                                                text_="No matching process pages could be found.")
        content_found_condition = visibility_of_element_located((By.CSS_SELECTOR,
                                                                 ".communardo-qms-process-search-processpage-tile"))
        any_condition = AnyEc(nothing_found_condition, content_found_condition)
        WebDriverWait(page.driver, timeout=10).until(any_condition,
                                                     message="Timeout while waiting for process search to complete")

    insert_search_term_and_start_search()


def _process_search_macro_scenarios(webdriver, datasets):
    macro_dataset_entry = _get_random_macro_dataset_entry(datasets, pmc_constants.PROCESS_SEARCH_MACRO)
    page = Page(webdriver, page_id=macro_dataset_entry[0])
    _measure_view_page_with_macro(page,
                                  (By.CSS_SELECTOR, ".conf-macro .communardo-qms-process-search-process-type-content"),
                                  PROCESS_SEARCH_TIMING_PREFIX)

    # TODO this is a workaround for QMS-754. The original search scenario for the Process Search macro should search
    # over everything, but this would lead to a server side error as described in the ticket. By first selecting a
    # process type before starting the search the CQL will be built differently (because not all processes have to be
    # considered) and the error will not happen. Note: for this workaround we also had to change the implementation of
    # the insert_search_term_and_start_search function that does the search.
    _measure_process_search_explore_processes_actions(page)

    if random.randint(1, 100) < 51:
        _measure_process_search_explore_subprocesses_actions(page)
    else:
        search_term = random.choice(datasets[pmc_constants.PROCESS_SEARCH_TERMS])
        _measure_process_search_full_text_search(page, search_term)


def pmc_macros(webdriver, datasets):
    _simple_macro_scenario(webdriver, datasets, pmc_constants.NO_PRINT_MACRO,
                           (By.CSS_SELECTOR, ".communardo-qms-no-print-macro"), "selenium_no_print_macro")
    # the Export Workflow Information macro renders nothing when viewing on desktop. It only renders stuff when
    # exporting to PDF or Word. Thus, there is no special visibility check, waiting for the page being loaded is enough
    # (decision whether something should be rendered for the current request is done on server side and tested with this
    # test).
    _simple_macro_scenario(webdriver, datasets, pmc_constants.EXPORT_WORKFLOW_INFORMATION_MACRO, None,
                           "selenium_workflow_information_macro")
    _simple_macro_scenario(webdriver, datasets, pmc_constants.CONTACT_PERSON_MACRO,
                           (By.CSS_SELECTOR, ".communardo-qms-contact-person-outputstyletype-desktop img.userLogo"),
                           "selenium_contact_person_macro")
    _simple_macro_scenario(webdriver, datasets, pmc_constants.MY_TASKS_MACRO,
                           (By.CSS_SELECTOR, "table.tasks-report tbody tr td.tasks-report-date"),
                           "selenium_my_tasks_macro")
    _simple_macro_scenario(webdriver, datasets, pmc_constants.APPLICABLE_DOCUMENTS_MACRO,
                           (By.CSS_SELECTOR, ".conf-macro .communardo-qms-applicable-attachments"),
                           "selenium_applicable_documents_macro")

    _comment_aggregation_macro_scenarios(webdriver, datasets)
    _process_search_macro_scenarios(webdriver, datasets)

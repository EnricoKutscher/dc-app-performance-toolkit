import random

from selenium.webdriver.common.by import By
from selenium_ui.base_page import BasePage
from selenium_ui.confluence.pages.pages import Page
from selenium_ui.conftest import print_timing
from selenium_ui.confluence.pages.selectors import EditorLocators
from util.conf import CONFLUENCE_SETTINGS

import util.pmc.constants as pmc_constants

def _got_to_space(page: Page):
    page.go_to_url(f"{CONFLUENCE_SETTINGS.server_url}/display/{pmc_constants.SPACE_KEY_BLUEPRINT_TEST}/")
    page.wait_until_visible((By.ID, "title-text"))  # Wait for title field visible

def _click_three_dots(page: Page):
    page.wait_until_clickable((By.ID, "create-page-button")).click()

def _write_searchbox_template(page: Page, template):
    searchbox = page.wait_until_visible((By.ID, "createDialogFilter"))
    # Wait until the templates are available
    page.wait_until_visible((By.CSS_SELECTOR, "div.template-select-container-body .template.selected"))
    searchbox.clear()
    searchbox.send_keys(template)
    # The filtering for the template can take a while. In such a case the next step "create template"
    # would start before the filter is applied and would continue with creating a blank page since 
    # "Blank page" is the preselected/default value.
    page.wait_until_visible((By.CSS_SELECTOR, ".template.selected[data-blueprint-module-complete-key*='de.communardo.confluence.communardo.qms.plugin:qms-page-blueprint']"))

def _click_create_template(page: Page):
    page.wait_until_clickable((By.CSS_SELECTOR, ".create-dialog-create-button.aui-button.aui-button-primary")).click()        

def _template_write_page_title_field(page: Page, template):
    page_title_field = page.wait_until_visible((By.ID, "qmsPageTitle"))
    title = f"Zzz PMC loadtest page blueprint {template} - " + page.generate_random_string(9)
    page_title_field.clear()
    page_title_field.send_keys(title)  

def _template_write_pmc_process_user(page: Page):
    page.wait_until_clickable((By.XPATH, "(//span[@class='select2-chosen'])[2]")).click()

    input_field = page.wait_until_visible((By.CSS_SELECTOR, ".select2-input.select2-focused"))
    input_field.clear()
    input_field.send_keys("admin")

    page.wait_until_clickable((By.CLASS_NAME, "select2-result-label")).click()

def _template_click_create_page(page: Page):
    page.wait_until_clickable((By.XPATH, "//button[text()='Create']")).click()   

def _wait_for_page_loaded(page: Page):
    page.wait_until_any_ec_text_presented_in_el(selector_text_list=[(EditorLocators.status_indicator, 'Ready to go'),
                                                                (EditorLocators.status_indicator, 'Changes saved')])
    page.wait_until_clickable(EditorLocators.publish_button)

def _click_submit(page: Page):
    page.get_element(EditorLocators.publish_button).click()


def blueprint_load_test(webdriver, datasets):
    page = BasePage(webdriver)
    template = random.choice(["process type", "sub process"])

    @print_timing("selenium_blueprint:open_selection_dialog")
    def open_blueprint_selection_dialog():
        _got_to_space(page)
        _click_three_dots(page)
        _write_searchbox_template(page, template)

    @print_timing("selenium_blueprint:open_and_fill_wizard")
    def open_and_fill_blueprint_wizard():
        _click_create_template(page)
        _template_write_page_title_field(page, template)
        if template == "sub process":
            _template_write_pmc_process_user(page)

    @print_timing("selenium_blueprint:submit_wizard")
    def submit_blueprint_wizard():
        _template_click_create_page(page)
        _wait_for_page_loaded(page)

    @print_timing("selenium_blueprint:save_page")
    def save_page():    
        _click_submit(page)       
        page.wait_until_visible((By.ID, "title-text"))  # Wait for title field visible 

    open_blueprint_selection_dialog()
    open_and_fill_blueprint_wizard()
    submit_blueprint_wizard()
    save_page()
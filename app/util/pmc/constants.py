NO_PRINT_MACRO = 'no-print'
EXPORT_WORKFLOW_INFORMATION_MACRO = 'approval-print-metadata'
APPLICABLE_DOCUMENTS_MACRO = 'qms-applicable-documents-macro'
MY_TASKS_MACRO = 'my-tasks-report-macro'
CONTACT_PERSON_MACRO = 'qms-contact-person-macro'
PROCESS_SEARCH_MACRO = 'qms-process-search-macro'
# list with names of the PMC macros. These names are also used to save the loaded CSV data in the datasets.
MACRO_NAMES = [EXPORT_WORKFLOW_INFORMATION_MACRO, NO_PRINT_MACRO, MY_TASKS_MACRO, APPLICABLE_DOCUMENTS_MACRO,
               CONTACT_PERSON_MACRO, PROCESS_SEARCH_MACRO]
# identifier of the data of the Comment Aggregation macro in the datasets
COMMENT_AGGREGATION_DATA = 'comment_aggregation_macro_data'
# identifier of the search terms of the Process Search macro scenario in the datasets
PROCESS_SEARCH_TERMS = 'process_search_search_terms'
# token that is used in all page titles of pages which belong to the PMC test data, including those which are created
# during test runs. This token can therefore be used to exclude PMC content from other tests.
PAGE_TITLE_TOKEN = 'PMC'
# key of the space for the blueprint tests
SPACE_KEY_BLUEPRINT_TEST = 'PMCBLUEPRINT'
# name of the space for the blueprint tests
SPACE_TITLE_BLUEPRINT_TEST = 'PMCBlueprintDataCenterSpace'

from util.project_paths import CONFLUENCE_DATASETS


def get_macro_csv_file(macro_name):
    return CONFLUENCE_DATASETS / ('pmc_macro-pages-' + macro_name + '.csv')


# note: the Comment Aggregation macro is handled in a special way because we need additional data for the tests. This
# data is also written to the CSV file. To make this special handling of the macro and the difference in the content of
# the file a bit more transparent for devs we decided to have a file name which diverges from those of the other macros.
def get_comment_aggregation_macro_data_csv_file():
    return CONFLUENCE_DATASETS / 'pmc_comment_aggregation_macro_data.csv'


def get_process_search_terms_file():
    return CONFLUENCE_DATASETS / 'static-content/pmc_process-search-macro_search-terms.csv'

import getopt
import queue
import sys
import threading

from util.api.confluence_clients import ConfluenceRestClient
from util.conf import CONFLUENCE_SETTINGS

THREAD_LIMIT = 5


class DeletionThread(threading.Thread):
    def __init__(self, thread_id, rest_client, content_type, content_id_queue):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.rest_client = rest_client
        self.content_type = content_type
        self.content_id_queue = content_id_queue

    def run(self):
        print('Starting ' + self.thread_id)
        while True:
            content_id = self.content_id_queue.get()
            if content_id is None:
                break
            _delete_content(self.rest_client, self.content_type, content_id)
            self.content_id_queue.task_done()
        print('Exiting ' + self.thread_id)


def _delete_content_entities(rest_client, content_type, delete_limit, delete_after_date):
    cql = 'type = ' + content_type
    # only delete the pages created by Locust
    if content_type == 'page':
        cql += ' AND title ~ locust'
    if delete_after_date:
        cql += ' AND created > ' + delete_after_date
    cql += ' order by created desc'
    content_entities = rest_client.get_content_search(0, delete_limit, cql, '')
    print(f'Found {len(content_entities)} {content_type} for deletion')
    _delete_content_entities_multi_threaded(rest_client, content_type, content_entities)


def _delete_content_entities_multi_threaded(rest_client, type, content_entities):
    content_id_queue = queue.Queue(len(content_entities))
    for entity in content_entities:
        content_id_queue.put(entity['id'])
    threads = []
    for i in range(THREAD_LIMIT):
        thread = DeletionThread('Thread-' + str(i), rest_client, type, content_id_queue)
        thread.start()
        threads.append(thread)
    content_id_queue.join()
    # stop workers
    for i in range(THREAD_LIMIT):
        content_id_queue.put(None)
    for t in threads:
        t.join()


def _delete_content(rest_client, type, content_id):
    api_url = f'{rest_client.host}/rest/api/content/{content_id}'
    response = rest_client.session.delete(api_url, auth=rest_client.base_auth, timeout=rest_client.requests_timeout)
    status_code = response.status_code
    if status_code == 204:
        if type == 'comment':
            print(f'Deleted comment with ID {content_id}')
        else:
            __purge_content(rest_client, type, content_id)
    else:
        Exception(
            f"Deletion of content with ID {content_id} failed. Response code:[{response.status_code}], response text:[{response.text}]")


def __purge_content(rest_client, type, content_id):
    api_url = f'{rest_client.host}/rest/api/content/{content_id}?status=trashed'
    response = rest_client.session.delete(api_url, auth=rest_client.base_auth, timeout=rest_client.requests_timeout)
    status_code = response.status_code
    if status_code == 204:
        print(f'Purged {type} with ID {content_id}')
    else:
        Exception(
            f"Purging of trashed {type} with ID {content_id} failed. Response code:[{response.status_code}], response text:[{response.text}]")


def __print_help():
    print('clean-data.py -l <limit> [-d <date>]')
    print('Cleanup by deleting latest created comments, (Locust) pages, blogposts and attachments.')
    print('-l Maximum number of items to delete per content type')
    print('-d date in format yyyy-mm-dd to delete only content created after this date')


def main(argv):
    delete_limit = 0
    delete_after_date = None

    try:
        opts, remaining_args = getopt.getopt(argv, "hd:l:")
    except getopt.GetoptError:
        __print_help()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            __print_help()
            sys.exit()
        elif opt == '-d':
            delete_after_date = arg
        elif opt == '-l':
            delete_limit = int(arg)

    if delete_limit <= 0:
        print('No limit defined, nothing to do.')
        sys.exit()

    print(f'Going to delete a maximum of {delete_limit} pages, blogposts, attachments and comments')

    url = CONFLUENCE_SETTINGS.server_url
    print("Server url: ", url)

    rest_client = ConfluenceRestClient(url, CONFLUENCE_SETTINGS.admin_login, CONFLUENCE_SETTINGS.admin_password)
    _delete_content_entities(rest_client, 'comment', delete_limit, delete_after_date)
    _delete_content_entities(rest_client, 'page', delete_limit, delete_after_date)
    _delete_content_entities(rest_client, 'blogpost', delete_limit, delete_after_date)
    _delete_content_entities(rest_client, 'attachment', delete_limit, delete_after_date)

    print("Finished cleaning data data")


if __name__ == "__main__":
    main(sys.argv[1:])

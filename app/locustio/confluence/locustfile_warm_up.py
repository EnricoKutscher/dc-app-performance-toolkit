from locust import HttpUser, task, between

from locustio.common_utils import LocustConfig, MyBaseTaskSet
from locustio.confluence.http_actions import login_and_view_dashboard, view_page, view_dashboard, view_blog, \
    search_cql_and_view_results, view_attachments
from util.conf import CONFLUENCE_SETTINGS

config = LocustConfig(config_yml=CONFLUENCE_SETTINGS)

class ConfluenceBehavior(MyBaseTaskSet):

    def on_start(self):
        self.client.verify = config.secure
        login_and_view_dashboard(self)

    @task(75)
    def view_page_action(self):
        view_page(self)

    @task(10)
    def view_dashboard_action(self):
        view_dashboard(self)

    @task(5)
    def view_blog_action(self):
        view_blog(self)

    @task(5)
    def search_cql_action(self):
        search_cql_and_view_results(self)

    @task(5)
    def view_attachments_action(self):
        view_attachments(self)

class ConfluenceUser(HttpUser):
    host = CONFLUENCE_SETTINGS.server_url
    tasks = [ConfluenceBehavior]
    wait_time = between(0, 0)

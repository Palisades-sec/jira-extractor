import base64, tempfile, logging, requests, io, re
from PIL import Image
from urllib.parse import unquote
from bs4 import BeautifulSoup
from bs4.element import Comment
from requests.auth import HTTPBasicAuth

from .confluence import ConfluenceCollector, ConfluenceConfig




class ConfluencePagehelper:
    def __init__(self, atlassian_url, atlassian_api_user, atlassian_api_token) -> None:
        self.ATLASSIAN_URL = atlassian_url
        self.ATLASSIAN_API_USER = atlassian_api_user
        self.ATLASSIAN_API_TOKEN = atlassian_api_token

    def get_content_by_page_url(self, page_url: str):
        dev_config = ConfluenceConfig(
            url=self.ATLASSIAN_URL,
            username=self.ATLASSIAN_API_USER,
            api_token=self.ATLASSIAN_API_TOKEN,
            cloud=True,
        )
        dev_collector = ConfluenceCollector(dev_config)
        content = dev_collector.get_page_content_from_url(page_url)

        attachments = dev_collector.get_page_attachements_from_url(page_url)

        links = self.__links_from_html(content.content)

        return content, attachments, links

    def __links_from_html(self, body):
        soup = BeautifulSoup(body, "html.parser")
        links = soup.find_all("a")  # Find all elements with the tag <a>
        return links

    def text_from_html(self, body):
        soup = BeautifulSoup(body, "html.parser")
        texts = soup.findAll(string=True)
        visible_texts = filter(self.__tag_visible, texts)
        return " ".join(t.strip() for t in visible_texts)

    def image_from_html(self, body, attachments):
        soup = BeautifulSoup(body, "html.parser")
        image_tags = soup.find_all("ac:image")
        if image_tags:
            i = 0
            for image_tag in image_tags:
                image_summary = soup.new_tag("div")

                image_url = image_tag.get("ac:src")
                print(image_url)
                if image_url:
                    resp = requests.get(image_url)
                    response = self.process_image(resp)
                    print(response)
                else:
                    image_url = attachments[i]
                    auth = HTTPBasicAuth(
                        self.ATLASSIAN_API_USER, self.ATLASSIAN_API_TOKEN
                    )
                    resp = requests.get(str(image_url), auth=auth)
                    response = self.process_image(resp)
                    i += 1

               


        return str(soup)


    def __tag_visible(self, element):
        if element.parent.name in [
            "style",
            "script",
            "head",
            "title",
            "meta",
            "[document]",
        ]:
            return False
        if isinstance(element, Comment):
            return False
        return True

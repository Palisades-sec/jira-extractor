import re
from atlassian import Confluence


class ConfluenceConfig:
    def __init__(self, url: str, **kwargs):
        """Create a new ConfluenceConfig.

        Args:
            url: The URL of the Confluence instance to connect to.
        Optional Arg Sets:
            These are mutualy exclusive, only one may be set.
            If multiple are set, the first one in the list will be used.
        Basic Auth:
            username: The username to connect with.
            password: The password to connect with.
            cloud: Whether to connect to a Confluence Cloud instance (default: False)
        API Token Auth:
            username: The username to connect with.
            api_token: The API token to connect with.
            cloud: Must be set to True for this auth mode.
        OAuth:
            access_token: The access token to connect with.
            access_token_secret: The access token secret to connect with.
            consumer_key: The consumer key to connect with.
            key_cert: The key certificate to connect with.
        OAuth2:
            oauth_client_id: The OAuth client ID to connect with.
            oauth_token: The OAuth token to connect with."""
        if url is None or url == "":
            raise ValueError("url be set and non-empty")
        self.url = url
        # kwargs parsing
        username = kwargs.get("username", None)
        password = kwargs.get("password", None)
        api_token = kwargs.get("api_token", None)
        cloud = kwargs.get("cloud", False)
        access_token = kwargs.get("access_token", None)
        access_token_secret = kwargs.get("access_token_secret", None)
        consumer_key = kwargs.get("consumer_key", None)
        key_cert = kwargs.get("key_cert", None)
        oauth_client_id = kwargs.get("oauth_client_id", None)
        oauth_token = kwargs.get("oauth_token", None)
        # kwargs validation
        if username is not None and password is not None and cloud is False:
            self.auth_mode = "basic"
            self.auth_parameters = {"username": username, "password": password}
        elif username is not None and api_token is not None and cloud is True:
            self.auth_mode = "api_token"
            self.auth_parameters = {"username": username, "api_token": api_token}
        elif (
            access_token is not None
            and access_token_secret is not None
            and consumer_key is not None
            and key_cert is not None
        ):
            self.auth_mode = "oauth"
            self.auth_parameters = {
                "access_token": access_token,
                "access_token_secret": access_token_secret,
                "consumer_key": consumer_key,
                "key_cert": key_cert,
            }
        elif oauth_client_id is not None and oauth_token is not None:
            self.auth_mode = "oauth2"
            self.auth_parameters = {
                "oauth_client_id": oauth_client_id,
                "oauth_token": oauth_token,
            }
        else:
            raise ValueError(
                "Invalid auth mode/parameters, see docstring for valid auth modes/parameters"
            )


class ConfluenceAttachementContent:
    def __init__(self, content: dict, url: str):
        self.download_urls = []
        file_data = content["results"]

        for file in file_data:
            self.download_urls.append(f"{url}/wiki{file['_links']['download']}")
            # response = requests.get(download_url, auth=auth)
            # image_file = ContentFile(response.content)

    def __str__(self) -> str:
        fmtstr = """\nDownload Urls:\n{urls}"""
        return fmtstr.format(
            urls=self.download_urls,
        )

    def get_urls(self) -> list:
        return self.download_urls


class ConfluenceContent:
    def __init__(self, content: dict):
        self.id = content["id"]
        self.title = content["title"] if "title" in content else None
        comment_list = content["descendants"]["comment"]["results"]
        inline_comments = [
            comment
            for comment in comment_list
            if comment["extensions"]["location"] == "inline"
        ]
        other_comments = [
            comment
            for comment in comment_list
            if comment["extensions"]["location"] != "inline"
        ]
        self.inline_comments = self.process_inline_comments(inline_comments)
        self.content = (
            content["body"]["storage"]["value"] if "body" in content else None
        )
        self.type = content["type"] if "type" in content else "Unknown"
        self.status = content["status"] if "status" in content else "Unknown"
        version_data = content["version"] if "version" in content else None
        self.version = version_data["number"] if version_data else None
        self.updated = version_data["when"] if version_data else None
        self.updated_by = version_data["by"]["publicName"] if version_data else None
        self.expandables = content["_expandable"] if "_expandable" in content else None

    def process_inline_comments(self, comment_list: list) -> list:
        output_list = []
        for comment in comment_list:
            created_by: dict = comment["history"]["createdBy"]
            parent_id = comment["ancestors"][0]["id"] if comment["ancestors"] else None
            parent_exists = False
            if parent_id is not None:
                for out_item in output_list:
                    if out_item["id"] == parent_id:
                        parent_exists = True
                        out_item["comments"].append(
                            {
                                "author": created_by["displayName"],
                                "comment": comment["body"]["storage"]["value"],
                            }
                        )
                        break
                if parent_exists is False:
                    raise ValueError(f"Parent ID {parent_id} not found in output list")
            else:
                comment_dict = {
                    "author": created_by["displayName"],
                    "comment": comment["body"]["storage"]["value"],
                }
                output_list.append(
                    {
                        "id": comment["id"],
                        "inline_source": comment["extensions"]["inlineProperties"][
                            "originalSelection"
                        ],
                        "comments": [comment_dict],
                    }
                )
        return output_list

    def __str__(self) -> str:
        # create a string with the comments, each parent/inline should be on new lines with the comments on the next line, each indented
        inline_comments_str = ""
        for comment in self.inline_comments:
            inline_comments_str += f'\n\tID: {comment["id"]}\n\tSource: {comment["inline_source"]}\n\tComments:'
            for inline_comment in comment["comments"]:
                inline_comments_str += f'\n\t\tAuthor: {inline_comment["author"]}\n\t\tComment: {inline_comment["comment"]}'
        fmtstr = """
Metadata:
    ID: {id}
    Type: {type}
    Status: {status}
    Version: {version}
    Updated Time: {updated}
    Updated By: {updated_by}
Title: {title}
Inline Comments: {inline_comments}
Content: {content}"""
        return fmtstr.format(
            id=self.id,
            type=self.type,
            status=self.status,
            version=self.version,
            updated=self.updated,
            updated_by=self.updated_by,
            title=self.title,
            inline_comments=inline_comments_str,
            content=self.content,
        )


class ConfluenceCollector:
    def __init__(self, config: ConfluenceConfig):
        """Create a new ConfluenceCollector.

        Args:
            config: The ConfluenceConfig to use to connect to the Confluence instance.
        """
        self.config = config
        self.instance = self.create_instance(config)

    def create_instance(self, config: ConfluenceConfig) -> Confluence:
        if config.auth_mode == "basic":
            return Confluence(
                url=config.url,
                username=config.auth_parameters["username"],
                password=config.auth_parameters["password"],
            )
        elif config.auth_mode == "api_token":
            return Confluence(
                url=config.url,
                username=config.auth_parameters["username"],
                password=config.auth_parameters["api_token"],
                cloud=True,
            )
        elif config.auth_mode == "oauth":
            return Confluence(
                url=config.url,
                oauth=config.auth_parameters,
            )
        elif config.auth_mode == "oauth2":
            return Confluence(
                url=config.url,
                oauth2=config.auth_parameters,
            )
        else:
            raise ValueError(
                "Invalid auth mode, see ConfluenceConfig docstring for valid auth modes"
            )

    def extract_inline_comments_from_page_content(self, content: str) -> list:
        """Extract inline comments from a Confluence page content string.

        Args:
            content: The content of the page to extract inline comments from.

        Returns:
            list: A list of dicts containing the ID and source of each inline comment.
        """
        # Currently unused, using expansion in the get_page_by_id call instead
        re_pattern = (
            '<ac:inline-comment-marker ac:ref="(.*?)">(.*?)</ac:inline-comment-marker>'
        )
        comments = []
        if "ac:inline-comment-marker" not in content:
            return comments
        comment_data = re.findall(re_pattern, content)
        for comment in comment_data:
            comments.append({"id": comment[0], "source": comment[1]})
        return comments

    def get_id_from_url(self, url: str) -> str:
        """Get the ID of a Confluence page from its URL.

        Args:
            url: The URL of the page to get the ID of.

        Returns:
            str: The ID of the page.
        """
        id = ""
        id_string = url.split("pages/")[1]
        id = id_string.split("/")[0]
        return id

    def get_page_attachments_from_id(
        self,
        page_id: str,
    ) -> ConfluenceContent:
        """Get the content of a Confluence page by ID.

        Args:
            page_id: The ID of the page to get the content of.
            page_version: The version of the page to get the content of (default: latest)

        Returns:
            The ConfluenceContent of the page.
        """
        confluence_return = self.instance.get_attachments_from_content(
            page_id=page_id,
        )
        if type(confluence_return) is not dict:
            raise ValueError(
                f"Got content of type {type(confluence_return)}, expected dict"
            )
        content: dict = confluence_return
        # if content['type'] != 'page':
        #     raise ValueError(f'Got content with type {content["type"]}, expected "page"')
        return ConfluenceAttachementContent(content, self.config.url).get_urls()

    def get_page_attachements_from_url(
        self,
        page_url: str,
    ) -> ConfluenceContent:
        """Get the content of a Confluence page by URL.
        This method wraps get_page_content_from_id.

        Args:
            page_url: The URL of the page to get the content of.
            page_version: The version of the page to get the content of (default: latest)

        Returns:
            The ConfluenceContent of the page."""
        return self.get_page_attachments_from_id(
            page_id=self.get_id_from_url(page_url),
        )

    def get_page_content_from_id(
        self, page_id: str, page_version: int | None = None
    ) -> ConfluenceContent:
        """Get the content of a Confluence page by ID.

        Args:
            page_id: The ID of the page to get the content of.
            page_version: The version of the page to get the content of (default: latest)

        Returns:
            The ConfluenceContent of the page.
        """
        confluence_return = self.instance.get_page_by_id(
            page_id=page_id,
            version=page_version,
            expand="body.storage,descendants.comment.ancestors,descendants.comment.body.storage,descendants.comment.extensions.inlineProperties,descendants.comment.history,history,space,version",
        )
        if type(confluence_return) is not dict:
            raise ValueError(
                f"Got content of type {type(confluence_return)}, expected dict"
            )
        content: dict = confluence_return
        if content["type"] != "page":
            raise ValueError(
                f'Got content with type {content["type"]}, expected "page"'
            )
        return ConfluenceContent(content)

    def get_page_content_from_url(
        self, page_url: str, page_version: int | None = None
    ) -> ConfluenceContent:
        """Get the content of a Confluence page by URL.
        This method wraps get_page_content_from_id.

        Args:
            page_url: The URL of the page to get the content of.
            page_version: The version of the page to get the content of (default: latest)

        Returns:
            The ConfluenceContent of the page."""
        return self.get_page_content_from_id(
            page_id=self.get_id_from_url(page_url),
            page_version=page_version,
        )

    def get_all_pages(self, space):
        pages = self.instance.get_all_pages_from_space(space)
        return pages

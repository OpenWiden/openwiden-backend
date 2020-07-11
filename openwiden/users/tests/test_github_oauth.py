import json
import os
import pytest
import typing as t
import imaplib
import time

from enum import Enum, auto

from django.urls import reverse

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions

from openwiden.enums import VersionControlService

from .selenium_helpers import save_current_state

pytestmark = [pytest.mark.django_db, pytest.mark.functional]

GITHUB_VERIFICATION_CODE_LENGTH = 6

GITHUB_USER_LOGIN = os.getenv("TEST_GITHUB_USER_LOGIN")
GITHUB_USER_PASSWORD = os.getenv("TEST_GITHUB_USER_PASSWORD")

EMAIL_LOGIN = os.getenv("TEST_EMAIL_LOGIN")
EMAIL_PASSWORD = os.getenv("TEST_EMAIL_PASSWORD")
EMAIL_IMAP_HOST = os.getenv("TEST_EMAIL_IMAP_HOST")


def search_github_verification_code(user: str, password: str, imap_host: str, timeout: int = 60) -> str:
    """
    Connects to the imap server and returns verification code.
    """
    connection = imaplib.IMAP4_SSL(imap_host)
    connection.login(user=user, password=password)

    while True:
        connection.select(mailbox="INBOX")
        typ, data = connection.search(None, '(SUBJECT "[GitHub] Please verify your device")')

        if typ == "OK":
            messages_ids = data[0].split()

            # Check for a new messages
            if len(messages_ids) == 0:
                if timeout > 0:
                    time.sleep(1)
                    timeout -= 1
                    continue
                else:
                    raise Exception("e-mail search failed (timed out).")

            # Fetch last e-mail
            typ, data = connection.fetch(messages_ids[-1], "(RFC822)")

            if typ == "OK":
                email_text = data[0][1]

                # Parse email for code
                search_text = "Verification code: "
                start = email_text.find(search_text.encode()) + len(search_text)
                end = start + GITHUB_VERIFICATION_CODE_LENGTH
                code = email_text[start:end]

                # Delete all messages before connection close
                for message_id in messages_ids:
                    connection.store(message_id, "+FLAGS", "\\Deleted")
                connection.expunge()

                # Close connection and logout
                connection.close()
                connection.logout()

                # Return code
                return code.decode()
            else:
                raise Exception("Fetch failed")


class OAuthRedirectType(Enum):
    VERIFY_DEVICE = auto()
    AUTHORIZE = auto()
    COMPLETE = auto()


def oauth_redirect(driver: webdriver.Remote) -> t.Union[bool, OAuthRedirectType]:
    """
    Custom redirect waiter for selenium driver.
    """
    if driver.current_url == "https://github.com/sessions/verified-device":
        return OAuthRedirectType.VERIFY_DEVICE
    elif driver.current_url.startswith("https://github.com/login/oauth/authorize"):
        return OAuthRedirectType.AUTHORIZE
    elif driver.current_url.startswith("http://0.0.0.0:8000/"):
        return OAuthRedirectType.COMPLETE
    else:
        return False


def verify_device(selenium: webdriver.Remote) -> None:
    verify_button = selenium.find_element_by_xpath("//button[contains(text(), 'Verify')]")

    # Get verification code from email
    verification_code = search_github_verification_code(
        user=EMAIL_LOGIN,
        password=EMAIL_PASSWORD,
        imap_host=EMAIL_IMAP_HOST,
    )

    # Set code
    selenium.find_element_by_id("otp").send_keys(verification_code)
    save_current_state(selenium, "github", "verify_set_code")

    # Click on verify button
    verify_button.click()
    save_current_state(selenium, "github", "verify_clicked")


def authorize(selenium: webdriver.Remote) -> None:
    try:
        authorize_button = selenium.find_element_by_xpath("//button[@name='authorize']")
    except NoSuchElementException:
        # Do nothing (already completed case)
        return

    # Select & submit clicks + 1 for just in case
    wait = WebDriverWait(selenium, 10)
    wait.until(expected_conditions.staleness_of(authorize_button))
    authorize_button.click()
    save_current_state(selenium, "github", "authorize_clicked")

    selenium.implicitly_wait(3)
    save_current_state(selenium, "github", "authorize_success")


@pytest.mark.selenium
def test_run(selenium, live_server, create_api_client):
    url = live_server.url + reverse("api-v1:login", kwargs={"vcs": VersionControlService.GITHUB.value})
    wait = WebDriverWait(selenium, 10)

    # Open API url, that redirects to sign in form
    selenium.get(url)

    # Sign in
    save_current_state(selenium, "github", "sign_in_open")
    selenium.find_element_by_id("login_field").send_keys(GITHUB_USER_LOGIN)
    selenium.find_element_by_id("password").send_keys(GITHUB_USER_PASSWORD)
    selenium.find_element_by_xpath("//input[@name='commit' and @value='Sign in']").click()
    save_current_state(selenium, "github", "sign_in_clicked")

    # Wait for redirect and check received type
    try:
        redirect_type = wait.until(oauth_redirect, "url: {url}".format(url=selenium.current_url))
    finally:
        save_current_state(selenium, "github", "sign_in_redirect_fail")

    # Do action depends on redirect type
    if redirect_type == OAuthRedirectType.AUTHORIZE:
        authorize(selenium)
    elif redirect_type == OAuthRedirectType.VERIFY_DEVICE:
        verify_device(selenium)

    save_current_state(selenium, "github", "after_redirect")

    # Check if authorize is required
    try:
        redirect_type = wait.until(oauth_redirect, "url: {url}".format(url=selenium.current_url))
    finally:
        save_current_state(selenium, "github", "sign_in_redirect_fail")

    # Check if authorize required
    if redirect_type == OAuthRedirectType.AUTHORIZE:
        authorize(selenium)
    elif redirect_type != OAuthRedirectType.COMPLETE:
        raise ValueError(redirect_type)

    # OAuth complete
    url = selenium.current_url.replace("http://0.0.0.0:8000", live_server.url)
    complete_url = "view-source:{url}&format=json".format(url=url)
    selenium.get(complete_url)
    save_current_state(selenium, "github", "complete")

    pre_element = selenium.find_element_by_tag_name("pre")
    tokens = json.loads(pre_element.text)

    # Get user
    client = create_api_client(access_token=tokens["access"])
    response = client.get(reverse("api-v1:user-me"))

    assert response.status_code == 200
    assert response.data["username"] == GITHUB_USER_LOGIN

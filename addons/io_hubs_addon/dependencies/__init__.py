from ..utils import load_dependency

selenium = None


def get_selenium():
    global selenium
    if selenium is None:
        selenium = load_dependency("selenium.webdriver")

    return selenium

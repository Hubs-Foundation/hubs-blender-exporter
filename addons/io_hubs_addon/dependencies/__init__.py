from ..utils import load_dependency

selenium = None


def get_selenium():
    global selenium
    if selenium == None:
        selenium = load_dependency("selenium.webdriver")

    return selenium

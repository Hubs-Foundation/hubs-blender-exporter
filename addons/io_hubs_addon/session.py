import bpy
from .preferences import get_addon_pref, EXPORT_TMP_FILE_NAME
from .utils import isModuleAvailable, get_browser_profile_directory

PARAMS_TO_STRING = {
    "newLoader": {
        "name": "Use New Loader",
        "description": "Creates the room using the new bitECS loader"
    },
    "ecsDebug": {
        "name": "Show ECS Debug Panel",
        "description": "Enables the ECS debugging side panel"
    },
    "vr_entry_type": {
        "name": "Skip Entry",
        "description": "Omits the entry setup panel and goes straight into the room",
        "value": "2d_now"
    },
    "debugLocalScene": {
        "name": "Allow Scene Update",
        "description": "Allows scene override. Use this if you want to update the scene. If you just want to spawn an object disable it."
    },
}

JS_DROP_FILE = """
    var target = arguments[0],
        offsetX = arguments[1],
        offsetY = arguments[2],
        document = target.ownerDocument || document,
        window = document.defaultView || window;

    var input = document.createElement('INPUT');
    input.type = 'file';
    input.onchange = function () {
      var rect = target.getBoundingClientRect(),
          x = rect.left + (offsetX || (rect.width >> 1)),
          y = rect.top + (offsetY || (rect.height >> 1)),
          dataTransfer = { files: this.files };
          dataTransfer.getData = o => undefined;

      ['dragenter', 'dragover', 'drop'].forEach(function (name) {
        var evt = document.createEvent('MouseEvent');
        evt.initMouseEvent(name, !0, !0, window, 0, 0, 0, x, y, !1, !1, !1, !1, 0, null);
        evt.dataTransfer = dataTransfer;
        target.dispatchEvent(evt);
      });

      setTimeout(function () { document.body.removeChild(input); }, 25);
    };
    document.body.appendChild(input);
    return input;
"""


class Session:
    _web_driver = None
    _user_logged_in = False
    _user_in_room = False
    _room_name = ""
    _room_params = {}

    def init(self, context):
        browser = get_addon_pref(context).browser
        if self.is_alive():
            if self._web_driver.name != browser.lower():
                self.close()
                self.__create_instance(context)
                return False
            return True
        else:
            self.__create_instance(context)
            return False

    def close(self):
        if self._web_driver:
            # Hack, without this the browser instances don't close the session correctly and
            # you get a "[Browser] didn't shutdown correctly" message on reopen.
            # Only seen in Windows so far so limiting to it for now.
            import platform
            if platform == "windows":
                windows = self._web_driver.window_handles
                for w in windows:
                    self._web_driver.switch_to.window(w)
                    self._web_driver.close()

            self._web_driver.quit()
            self._web_driver = None

    def __create_instance(self, context):
        if not self._web_driver or not self.is_alive():
            self.close()
            browser = get_addon_pref(context).browser
            import os
            file_path = get_browser_profile_directory(browser)
            if not os.path.exists(file_path):
                os.mkdir(file_path)
            if browser == "Firefox":
                from selenium import webdriver
                options = webdriver.FirefoxOptions()
                override_ff_path = get_addon_pref(
                    context).override_firefox_path
                ff_path = get_addon_pref(context).firefox_path
                if override_ff_path and ff_path:
                    options.binary_location = ff_path
                # This should work but it doesn't https://github.com/SeleniumHQ/selenium/issues/11028 so using arguments instead
                # firefox_profile = webdriver.FirefoxProfile(file_path)
                # firefox_profile.accept_untrusted_certs = True
                # firefox_profile.assume_untrusted_cert_issuer = True
                # options.profile = firefox_profile
                options.add_argument("-profile")
                options.add_argument(file_path)
                options.set_preference("javascript.options.shared_memory", True)
                self._web_driver = webdriver.Firefox(options=options)
            else:
                from selenium import webdriver
                options = webdriver.ChromeOptions()
                options.add_argument('--enable-features=SharedArrayBuffer')
                options.add_argument('--ignore-certificate-errors')
                options.add_argument(
                    f'user-data-dir={file_path}')
                override_chrome_path = get_addon_pref(
                    context).override_chrome_path
                chrome_path = get_addon_pref(context).chrome_path
                if override_chrome_path and chrome_path:
                    options.binary_location = chrome_path
                self._web_driver = webdriver.Chrome(options=options)

    def update_session_state(self):
        url = self._web_driver.current_url
        from urllib.parse import urlparse
        from urllib.parse import parse_qs
        parsed = urlparse(url)
        params = parse_qs(parsed.query, keep_blank_values=True)
        self._room_params = {k: v for k, v in params.items() if k != "hub_id"}

        if "debugLocalScene" in self.room_params:
            self._user_logged_in = bool(self._web_driver.execute_script(
                'try { return APP?.hubChannel?.signedIn; } catch(e) { return false; }'))
        else:
            self._user_logged_in = True

        self._user_in_room = bool(self._web_driver.execute_script(
            'try { return APP?.scene?.is("entered"); } catch(e) { return false; }'))

        self._room_name = self._web_driver.execute_script(
            'try { return APP?.hub?.name || APP?.hub?.slug || APP?.hub?.hub_id; } catch(e) { return ""; }')

    def bring_to_front(self, context):
        # In some systems switch_to doesn't work, the code below is a hack to make it work
        # for the affected platforms/browsers that we have detected so far.
        browser = get_addon_pref(context).browser
        import platform
        if browser == "Firefox" or platform.system == "Windows":
            ws = self._web_driver.get_window_size()
            self._web_driver.minimize_window()
            self._web_driver.set_window_size(ws['width'], ws['height'])
        self._web_driver.switch_to.window(self._web_driver.current_window_handle)

    def is_alive(self):
        try:
            if not self._web_driver or not isModuleAvailable("selenium"):
                return False
            else:
                return bool(self._web_driver.current_url)
        except Exception:
            return False

    def update(self):
        import os
        document = self._web_driver.find_element("tag name", "html")
        file_input = self._web_driver.execute_script(JS_DROP_FILE, document, 0, 0)
        file_input.send_keys(os.path.join(bpy.app.tempdir, EXPORT_TMP_FILE_NAME))

    def get_local_storage(self):
        storage = None
        if self.is_alive():
            storage = self._web_driver.execute_script("return window.localStorage;")

        return storage

    def get_url(self):
        return self._web_driver.current_url

    def get_url_params(self, context):
        params = ""
        keys = list(PARAMS_TO_STRING.keys())
        for key in keys:
            if getattr(context.scene.hubs_scene_debugger_room_create_prefs, key):
                value = f'={PARAMS_TO_STRING[key]["value"]}' if "value" in PARAMS_TO_STRING[key] else ""
                key = key if not params else f'&{key}'
                params = f'{params}{key}{value}'

        return params

    def load(self, url):
        self._web_driver.get(url)

    @property
    def user_logged_in(self):
        return self._user_logged_in

    @property
    def user_in_room(self):
        return self._user_in_room

    @property
    def room_name(self):
        return self._room_name

    @property
    def room_params(self):
        return self._room_params

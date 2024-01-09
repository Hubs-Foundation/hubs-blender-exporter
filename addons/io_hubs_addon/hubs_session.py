import bpy
from .preferences import get_addon_pref, EXPORT_TMP_FILE_NAME
from .utils import isModuleAvailable, get_browser_profile_directory

PARAMS_TO_STRING = {
    "newLoader": {
        "name": "Use New Loader",
        "description": "Makes the room use the new bitECS loader.  This causes all media/objects in the room and scene to be loaded with the new loader and has various changes to the UI interface and functionality of objects.  This is required for Behavior Graphs. (newLoader)"
    },
    "ecsDebug": {
        "name": "Show ECS Debug Panel",
        "description": "Enables the ECS debugging side panel to get hierarchical information on the underlying structure of elements in the room and which components are applied to each element. (ecsDebug)"
    },
    "vr_entry_type": {
        "name": "Skip Entry",
        "description": "Omits the entry setup panel and goes straight into the room. (vr_entry_type=2d_now)",
        "value": "2d_now"
    },
    "debugLocalScene": {
        "name": "Allow Scene Update",
        "description": "Allows the scene to be overridden by the contents of the current Blender scene. Enable this if you want to update the scene.  Disable this if you just want to spawn an object in the room. (debugLocalScene)"
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

JS_STATE_UPDATE = """
    let params = { signedIn: false, entered: false, roomName: "", reticulumUrl: "" };
    try { params["signedIn"] = APP?.hubChannel?.signedIn; } catch(e) {};
    try { params["entered"] = APP?.scene?.is("entered"); } catch(e) {};
    try { params["roomName"] = APP?.hub?.name || APP?.hub?.slug || APP?.hub?.hub_id; } catch(e) {};
    try { params["reticulumUrl"] = window.$P.getReticulumFetchUrl(""); } catch (e) {};
    return params;
"""
JS_WAYPOINT_UPDATE = """
    window.__scene_debugger_scene_update_listener = () => {
        try {
            setTimeout(() => {
                window.location = `${window.location.href}#${arguments[0]}`;
                const mat = APP.world.scene.getObjectByName("__scene_debugger_viewpoint").matrixWorld;
                APP.scene.systems["hubs-systems"].characterController.travelByWaypoint(mat, false, false);
            }, 0);
        } catch(e) {
            console.warn(e);
        };
        APP.scene.removeEventListener("environment-scene-loaded", window.__scene_debugger_scene_update_listener);
        delete window.__scene_debugger_scene_update_listener;
    };
    APP.scene.addEventListener("environment-scene-loaded", window.__scene_debugger_scene_update_listener);
"""


class HubsSession:
    _web_driver = None
    _user_logged_in = False
    _user_in_room = False
    _room_name = ""
    _room_params = {}
    _reticulum_url = ""
    _client_url = ""

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
        if self.is_alive():
            url = self._web_driver.current_url
            from urllib.parse import urlparse
            from urllib.parse import parse_qs
            parsed = urlparse(url)
            params = parse_qs(parsed.query, keep_blank_values=True)
            self._room_params = {k: v for k, v in params.items() if k != "hub_id"}

            self._client_url = f'{parsed.scheme}://{parsed.hostname}:{parsed.port}'

            params = self._web_driver.execute_script(JS_STATE_UPDATE)
            self._user_logged_in = params["signedIn"] or "debugLocalScene" not in self._room_params
            self._user_in_room = params["entered"]
            self._room_name = params["roomName"]
            self._reticulum_url = params["reticulumUrl"]
            if not self._reticulum_url:
                import urllib
                base_assets_path = self._get_env_meta("base_assets_path")
                isUsingCloudflare = base_assets_path and "workers.dev" in base_assets_path
                if isUsingCloudflare:
                    ret_host = urllib.parse.urlparse(base_assets_path).hostname
                else:
                    ret_host = self._get_env_meta("upload_host")
                    if not ret_host:
                        ret_host = self._get_env_meta("reticulum_server")
                if ret_host:
                    ret_port = urllib.parse.urlparse(ret_host).port
                    self._reticulum_url = f'https://{ret_host}{":"+ret_port if ret_port else ""}'

        else:
            self._user_logged_in = False
            self._user_in_room = False
            self._room_name = ""
            self.reticulumUrl = ""

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

    def get_local_storage(self, item):
        store = None
        if self.is_alive():
            store = self._web_driver.execute_script(f'return window.localStorage.getItem("{item}");')

        return store

    def set_local_storage(self, data):
        if self.is_alive():
            self._web_driver.execute_script(f'window.localStorage.setItem("___hubs_store", {data});')

    def get_url(self):
        return self._web_driver.current_url

    def url_params_string_from_prefs(self, context):
        params = ""
        keys = list(PARAMS_TO_STRING.keys())
        for key in keys:
            if getattr(context.scene.hubs_scene_debugger_room_create_prefs, key):
                value = f'={PARAMS_TO_STRING[key]["value"]}' if "value" in PARAMS_TO_STRING[key] else ""
                key = key if not params else f'&{key}'
                params = f'{params}{key}{value}'

        return params

    def _get_env_meta(self, name):
        return self._web_driver.execute_script(f'return document.querySelector(\'meta[name="env:{name}"]\')?.content')

    def get_token(self):
        if self.is_alive():
            hubs_store = self.get_local_storage("___hubs_store")
            if hubs_store:
                import json
                hubs_store = json.loads(hubs_store)
                has_credentials = "credentials" in hubs_store
                if has_credentials:
                    credentials = hubs_store["credentials"]
                    if "token" in credentials:
                        return credentials["token"]

        return None

    def set_credentials(self, email, token):
        if self.is_alive():
            hubs_store = self.get_local_storage("___hubs_store")
            if hubs_store:
                import json
                hubs_store = json.loads(hubs_store)
                has_credentials = "credentials" in hubs_store
                if has_credentials:
                    credentials = hubs_store["credentials"]
                    credentials["email"] = email
                    credentials["token"] = token
                    self.set_local_storage(hubs_store)

    def set_creator_assignment_token(self, hub_id, creator_token, embed_token):
        if self.is_alive():
            hubs_store = self.get_local_storage("___hubs_store")
            if hubs_store:
                import json
                hubs_store = json.loads(hubs_store)
                has_token = "creatorAssignmentTokens" in hubs_store
                if not has_token:
                    hubs_store["creatorAssignmentTokens"] = []
                #  creator
                if creator_token:
                    creator_tokens = hubs_store["creatorAssignmentTokens"]
                    if creator_tokens:
                        creator_tokens.append({
                            "hub_id": hub_id,
                            "creatorAssignmentToken": creator_token
                        })
                    else:
                        creator_tokens = [{
                            "hub_id": hub_id,
                            "creatorAssignmentToken": creator_token
                        }]
                # embed
                if embed_token:
                    embed_tokens = hubs_store["embed_tokens"]
                    if embed_tokens:
                        embed_tokens.append({
                            "hub_id": hub_id,
                            "embedToken": embed_token
                        })
                    else:
                        embed_tokens = [{
                            "hub_id": hub_id,
                            "embedToken": embed_token
                        }]
                self.set_local_storage(hubs_store)

    def load(self, url):
        self._web_driver.get(url)

    def is_local_instance(self):
        return "hub_id" in self._web_driver.current_url

    def move_to_waypoint(self, name):
        self._web_driver.execute_script(JS_WAYPOINT_UPDATE, name)

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

    @property
    def reticulum_url(self):
        return self._reticulum_url

    @property
    def client_url(self):
        return self._client_url

import os

from bs4 import BeautifulSoup
import requests


class NoCredentialsError(Exception):
    def __init__(self, message):
        super().__init__(message)


class ConfigError(Exception):
    def __init__(self, message):
        super().__init__(message)


class NoElementError(Exception):
    def __init__(self, message):
        super().__init__(message)


class CourseNaviInterface:
    def __init__(self):
        # TODO: add config file manipulation (raise error instead of processing)
        self.email = 'shoyo@toki.waseda.jp'
        self.password = os.environ['CNAVI_PASSWORD']
        self.base_url = 'https://cnavi.waseda.jp/index.php'
        self.session = requests.Session()
        self.headers = {
            'accept':          'text/html,application/xhtml+xml,'
                                   + 'application/xml;q=0.9,'
                                   + 'image/webp,image/apng,*/*;'
                                   + 'q=0.8,application/signed-exchange;v=b3',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control':   'max-age=0',
            'content-type':    'application/x-www-form-urlencoded',
            'sec-fetch-site':  'same-origin',
            'sec-fetch-mode':  'navigate',
            'user-agent':      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) '
                                   + 'AppleWebKit/537.36 (KHTML, like Gecko) '
                                   + 'Chrome/78.0.3904.97 '
                                   + 'Safari/537.36',

            'upgrade-insecure-requests': '1',
        }

    
    def login(self):
        dummy = self._login()
        print(dummy)
        return self._login_redirect(dummy)


    def course_detail(self, dashboard, course):
        dummy, params = self._course_detail(dashboard, course)
        return self._course_detail_redirect(dummy, params)


    def get_courses(self, dashboard):
        """Return a list of HTML row elements containing courses in dashboard.

        Typically used on the return value of `self.login()` to extract
        relevant course data.
        """
        return dashboard.find_all('div', 'w-conbox')


    def get_lectures(self, course_detail):
        pass


    def _login(self):
        if not self.email or not self.password:
            raise NoCredentialsError('No email or password found.')

        login_html = self._get(self.base_url)

        params = {
            'id': self.email,
            'password': self.password,
            'vertype': 1,
            'simpletype': 0,
        }
        other_fields = [
            'lang',
            'ControllerParameters',
            'ControllerParameters2',
            'hidSessionKey',
            'hidSessionKeyFlg',
            'hidPankuzuSessionKey',
            'SessionIdEncodeKey',
            'hidLogin_flg',
            'hidInquiry', 
            'hidNameFlg', 
            'hidAdmission',
            'hidAdmKey01',
            'hidAdmKey02',
            'hidAdmKey03',
            'hidAdmKey04',
            'hidAdmKey05',
            'hidAdmKey06',
            'hidAdmKey07',
            'hidAdmKey08',
            'hidAdmKey90',
            'hidAdmKey91',
        ]

        for field in other_fields:
            params[field] = self._find_value_by_name(login_html, field)

        return self._post(self.base_url, params)


 
    def _login_redirect(self, dummy):
        params = {}
        fields = [
            'ControllerParameters',
            'hidCommunityId',
            'hidCommKcd',
            'hidCommBcd',
            'hidFolderId',
            'hidContentsId',
            'hidListMode',
            'hidEditButton',
            'hidInputFuncType',
            'hidsocial_no',
            'hidDesignInfo',
            'simpletype',
            'SessionIdEncodeKey',
            'hidLogin_flg',
            'hidAdmission',
        ]
        for field in fields:
            params[field] = self._find_value_by_name(dummy, field)
        
        return self._post(self.base_url, params)


    def _course_detail(self, dashboard, course_row):
        params = {}
        general_fields = [
            'hidCurrentViewID',
            'hidCloseFlg',
            'hidSessionDelFlg',
            'hidContactFunTypeCd',
            'hidContactFolderId',
            'hidContactCommunityId',
            'hidContactContentsId',
            'hidKamokuId',
            'hidSessionTimeOut',
            'hidWarningForSessionTimeOut',
            'hidWarningForSessionTimeOutDispLogin',
            'xpoint',
            'ypoint',
            'tagname',
            'SessionIdEncodeKey',
            'hidAdmission',
            'hidAdmKey01',
            'hidAdmKey02',
            'hidAdmKey03',
            'hidAdmKey04',
            'hidAdmKey05',
            'hidAdmKey06',
            'hidAdmKey07',
            'hidAdmKey08',
            'hidAdmKey90',
            'hidAdmKey91',
            'hidLanguage',
            'hidState',
            'hidCommounity',
            'hidDesignFlg',
            'hidCurrentStudyFlg',
            'simpletype',
            'hidListMode',
            'hidFolderId',
            'hidContentsId',
            'hidCurrentFolderId',
            'hidNewListFlg',
            'hidMenuFlg',
            'hidEditButton',
            'hidNewWindowFlg',
            'hidCommunityId',
            'hidCommKcd',
            'hidCommBcd',
            'hidCheckSelectFlg',
            'hidSwfFileName',
            'hidFlg',
            'hidUsers',
            'hidListCnt',
            'hidLogoutFlg',
            'hidLoginID',
            'hidSessionKey',
            'hidPankuzuSessionKey',
            'ControllerParameters',
            'hidTabId',
            'hidMenuId',
            'hidDesignId',
            'hidURL',
        ]
        specific_fields = [
            'folder_id[]',
            'community_name[]',
            'hdnIcon[]',
            'communityIdInfo[]',
            'sequenceInfo[]',
        ]

        for field in general_fields:
            params[field] = self._find_value_by_name(dashboard, field)
        for field in specific_fields:
            params[field] = self._find_value_by_name(course_row, field)

        return self._post(self.base_url, params), params


    def _course_detail_redirect(self, dummy, init_params):
        params = {}
        fields = [

        ]
        for field in fields:
            params[field] = self._find_value_by_name(dummy, field)


    def _find_value_by_name(self, html, name):
        element = html.find(attrs={'name': name})
        if element is None:
            raise NoElementError(f'No element found for "name={name}"')
        return element['value']


    def _get(self, url):
        response = self.session.get(url, headers=self.headers)
        return self._soupify(response.text)


    def _post(self, url, params):
        response = self.session.post(url, params=params, headers=self.headers)
        return self._soupify(response.text)


    def _soupify(self, html):
        return BeautifulSoup(html, 'html.parser')


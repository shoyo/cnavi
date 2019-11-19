import os

from bs4 import BeautifulSoup
import requests
from requests_toolbelt import MultipartEncoder


class CourseNaviInterface:
    def __init__(self):
        # TODO: add config file manipulation (raise error instead of processing)
        self.email = os.environ['CNAVI_ID']
        self.password = os.environ['CNAVI_PASSWORD']
        self.base_url = 'https://cnavi.waseda.jp/index.php'
        self.session = requests.Session()
        self.verify = True

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
        return self._login_redirect(dummy)


    def course_detail(self, dashboard, course):
        dummy, params = self._course_detail(dashboard, course)
        return self._course_detail_redirect(dummy, params)


    def get_title(self, course):
        """Return the title of a course as a string."""
        return course.find('p', 'w-col1').find('a').text.strip()


    def get_courses(self, dashboard):
        """Return a list of HTML row elements containing courses in dashboard.

        Typically used on the return value of `self.login()` to extract
        relevant course data.
        """
        return dashboard.find_all('div', 'w-conbox')


    def select_course(self, course, dashboard):
        """Simulate clicking a given course on the dashboard.

        course -- Soupified HTML of a given course row from `self.get_courses()`
        """
        course_data = course.find('p', 'w-col6') # Find hidden form fields
        dummy, params = self._course_detail(course_data, dashboard)
        course_detail = self._course_detail_redirect(dummy, params)

        return course_detail.prettify()

        # lectures = course_detail.find('ul', re.compile('^folder_open*'))


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

        return self._post(self.base_url, params, 'url-encoded')


 
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
        
        return self._post(self.base_url, params, 'url-encoded')


    def _course_detail(self, course_data, dashboard):
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
            try:
                params[field] = self._find_value_by_name(course_data, field)
            except NoElementError:
                # `communityIdInfo[]` sometimes returns as empty string name
                params[field] = self._find_value_by_name(course_data, '')

        return self._post(self.base_url, params, 'multipart-form'), params


    def _course_detail_redirect(self, dummy, init_params):
        """Handle redirect after POSTing to base_url for course detail.

        Course detail dummy contains every possible value for each field in
        `specific_fields`. For these fields, the initial params that were posted
        for course_detail are used to prevent parser error.
        """
        params = {}
        general_fields = [
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
            'hidAdmission',
        ]
        specific_fields = [
            'community_name[]',
            'communityIdInfo[]',
            'folder_id[]',
        ]

        for field in general_fields:
            params[field] = self._find_value_by_name(dummy, field)
        for field in specific_fields:
            params[field] = init_params[field]

        return self._post(self.base_url, params, 'url-encoded')


    def _find_value_by_name(self, html, name):
        element = html.find(attrs={'name': name})
        if element is None:
            raise NoElementError(f'No element found for "name={name}"')
        return element['value']


    def _get(self, url):
        response = self.session.get(url,
                                    headers=self.headers,
                                    verify=self.verify)
        return self._soupify(response.text)


    def _post(self, url, params, content_type):
        if content_type == 'url-encoded':
            self.headers['content-type'] = 'application/x-www-form-urlencoded'
            response = self.session.post(url,
                                         data=params,
                                         headers=self.headers,
                                         verify=self.verify)
        elif content_type == 'multipart-form':
            multipart = MultipartEncoder(fields=params)
            self.headers['content-type'] = multipart.content_type
            response = self.session.post(url,
                                         data=multipart,
                                         headers=self.headers,
                                         verify=self.verify)
        else:
            raise InvalidContentTypeError(f'Cannot set header to {content_type}')

        return self._soupify(response.text)


    def _soupify(self, html):
        return BeautifulSoup(html, 'html.parser')


# ---- Custom Errors ----

class NoCredentialsError(Exception):
    def __init__(self, message):
        super().__init__(message)


class ConfigError(Exception):
    def __init__(self, message):
        super().__init__(message)


class NoElementError(Exception):
    def __init__(self, message):
        super().__init__(message)


class InvalidContentTypeError(Exception):
    def __init__(self, message):
        super().__init__(message)


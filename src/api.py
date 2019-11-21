import os
import re

from bs4 import BeautifulSoup
import keyring
import requests
from requests_toolbelt import MultipartEncoder


class CourseNaviInterface:
    def __init__(self):
        self.email = keyring.get_password('cnavi-cli-email', 'cnaviauth')
        self.password = keyring.get_password('cnavi-cli-password', 'cnaviauth')
        self.base_url = 'https://cnavi.waseda.jp/index.php'
        self.session = requests.Session()
        self.cache = {}

        self.verify = True
#        # --- TEMP for proxying traffic from requests
#        self.session.proxies = {
#            'http': 'socks5://localhost:8080',
#            'https': 'socks5://localhost:8080',
#        }
#        self.verify = False
#        # ----

        self.headers = {
            'Accept':          'text/html,application/xhtml+xml,'
                                   + 'application/xml;q=0.9,'
                                   + 'image/webp,image/apng,*/*;'
                                   + 'q=0.8,application/signed-exchange;v=b3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control':   'max-age=0',
            'Content-Type':    'application/x-www-form-urlencoded',
            'Origin':          'https://cnavi.waseda.jp',
            'Referer':         self.base_url,
            'Sec-Fetch-Site':  'same-origin',
            'Sec-Fetch-Mode':  'navigate',
            'User-Agent':      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) '
                                   + 'AppleWebKit/537.36 (KHTML, like Gecko) '
                                   + 'Chrome/78.0.3904.97 '
                                   + 'Safari/537.36',

            'Upgrade-Insecure-Requests': '1',
        }
    
    def login(self):
        """Login to the dashboard."""
        dummy = self._login()
        return self._login_redirect(dummy)

    def select_course(self, course, dashboard):
        """Select a course in the dashboard.

        course    -- Soupified HTML of a single course row
        dashboard -- Soupified HTML of entire dashboard
        """
        hidden_fields = course.find(attrs={'class': 'w-col6'})
        ad_hoc_fields = course.find(attrs={'class': 'w-col1'})
        course_data = (hidden_fields, ad_hoc_fields)

        dummy = self._course_detail(course_data, dashboard)
        course_detail = self._course_detail_redirect(dummy)

        return course_detail

    def get_courses(self, dashboard):
        """Return a list of tuples of courses' titles and respective HTML.

        Typically used on the return value of `self.login()` to extract
        relevant course data.

        dashboard -- Soupified HTML of entire dashboard
        """
        rows = dashboard.find_all(attrs={'class': 'w-conbox'})
        date_of = lambda row: row.find(attrs={'class': 'w-col4'}).text
        is_course = lambda row: self._is_valid_date(date_of(row))
        return [(self._get_course_title(row), row)
                for row in rows
                if is_course(row)]

    def get_lectures(self, course_detail):
        """Return a list of tuples of lectures' titles and respective HTML.

        Typically used on the return value of `self.select_course()` to extract
        relevant lecture data.

        course_detail -- Soupified HTML of entire course detail
        """
        rows = course_detail.find_all(attrs={'class': 'c-mblock'})
        titles = [self._get_lecture_title(row) for row in rows]
        is_lecture_title = lambda title: title != 'お知らせ'
        lectures = [(title, row)
                    for (title, row) in zip(titles, rows)
                    if is_lecture_title(title)]

        return lectures

    def _get_course_title(self, course):
        """Return the title of a course as a string.

        course -- Soupified HTML of a single course row
        """
        return course.find(attrs={'class': 'w-col1'}).find('a').text.strip()

    def _get_lecture_title(self, lecture):
        """Return the title of a lecture as a string.

        course -- Soupified HTML of a single lecture row
        """
        return lecture.find(attrs={'class': 'ta1col-left'})['title'].strip()

    def _login(self):
        """POST login form and return the dummy response."""
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
        """Handle redirect after POSTing for login.

        dummy -- Soupified HTML of initial response after POSTing for login
        """
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
        """POST for course detail on dashboard and return the dummy response.

        course_data -- a tuple of: (<hidden fields>, <ad hoc fields>)
                       Hidden fields is a soupified <p> tag containing
                         hidden input fields needed for POST
                       Ad hoc fields is a soupified <p> tag containing
                         an onclick function with parameters needed for POST
        dashboard   -- a soupified HTML of the entire dashboard containing
                         general input fields


        Illustration of `ad hoc fields`
        -------------------------------
        Contains a function:
          post_submit_edit('<ControllerParameters>',
                           '<hidFolderId>',
                           '',
                           'list',
                           '<hidCommunityId>')
          Ad hoc fields:
          * ControllerParameters -> pull from above
          * hidFolderId -> pull from above
          * hidCommunityId -> pull from above
          * hidNewWindowFlg -> just set to 1
        """
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
            params[field] = self._find_value_by_name(course_data[0], field)
            self.cache[field] = params[field]

        # Ad hoc headers
        ad_hoc_fields = self._parse_ad_hoc(course_data[1])
        params['ControllerParameters'] = ad_hoc_fields['ControllerParameters']
        params['hidFolderId'] = ad_hoc_fields['hidFolderId']
        params['hidCommunityId'] = ad_hoc_fields['hidCommunityId']
        params['hidNewWindowFlg'] = '1'

        return self._post(self.base_url, params, 'multipart-form')

    def _course_detail_redirect(self, dummy):
        """Handle redirect after POSTing for course detail in the dashboard.

        dummy -- Soupified HTML of initial response after POSTing for course
                 detail

        Dummy contains a value for every field in `specific_fields`.
        For these fields, the values that were intially posted to course_detail
        and stored in self.cache are used to prevent parser error.
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
            params[field] = self.cache[field]

        return self._post(self.base_url, params, 'url-encoded')

    def _is_valid_date(self, string):
        """Return True if string is a valid date format. False otherwise."""
        ids = ['月', '火', '水', '木', '金', '土',
               'Mon', 'Tues', 'Wed', 'Thur', 'Fri', 'Sat']
        for id in ids:
            if string.startswith(id):
                return True
        return False

    def _parse_ad_hoc(self, html):
        """Parse ad hoc fields from HTML for use in `self.course_detail()`.

        Return a dictionary mapping each ad hoc field name to the appropriate
        argument of `post_submit_edit()` shown below.

        html -- typically looks like:
                <p class="w-col1">
                  <span>...</span>
                  <a href="#" onclick="post_submit_edit(...); return False;">
                    ...
                  </a>
                </p>
        """
        # Returns: "post_submit_edit('foo', 'bar', '', 'baz'); return False;"
        func = html.find('a')['onclick']

        # Returns: ['foo', 'bar', '', 'baz']
        args = re.findall("(?<=')([^',]*)(?=')", func)

        fields = {
            'ControllerParameters': args[0],
            'hidFolderId': args[1],
            'hidCommunityId': args[4],
        }

        return fields

    def _find_value_by_name(self, html, name):
        """Find an HTML element with a given name and return its value.

        Name refers to an HTML tag's <name=""> attribute, while value refers
        to an HTML tag's <value=""> attribute.

        html -- Soupified HTML
        name -- queried name value
        """
        element = html.find(attrs={'name': name})
        if element is None:
            raise NoElementError(f'No element found for "name={name}"')
        return element['value']

    def _get(self, url):
        """Make a GET request and return a soupified response."""
        response = self.session.get(url,
                                    headers=self.headers,
                                    verify=self.verify)
        return self._soupify(response.text)

    def _post(self, url, params, content_type):
        """Make a POST request and return a soupified response."""
        if content_type == 'url-encoded':
            self.headers['Content-Type'] = 'application/x-www-form-urlencoded'
            response = self.session.post(url,
                                         data=params,
                                         headers=self.headers,
                                         verify=self.verify)
        elif content_type == 'multipart-form':
            multipart = MultipartEncoder(fields=params)
            self.headers['Content-Type'] = multipart.content_type
            response = self.session.post(url,
                                         data=multipart,
                                         headers=self.headers,
                                         verify=self.verify)
        else:
            raise InvalidContentTypeError(f'Invalid keyword: {content_type}')

        return self._soupify(response.text)

    def _soupify(self, html):
        """Convert a given HTML string to an instance of BeautifulSoup.

        The parser 'html5lib' is used over the built-in 'html.parser' because
        there were issues where 'html.parser' failed to read certain values in
        large HTML strings.
        """
        return BeautifulSoup(html, 'html5lib')


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


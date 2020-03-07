import requests
import os
import json

class NoTokenError(Exception):
    """
    Raised when a token is needed but no token is defined
    """

class SignInError(Exception):
    """
    Raised when something went wrong during signing in. Presumed to be caused by incorrect credentials
    """

class sisAPI:
    """
    This class provides an API for retrieving data from osiris.ru.nl

   
    """
    
    def _readToken(self):
        """
        Try to find previously stored token at ~/.osiris_token

        Return:
            Previously retrieved authentication, or None if could not find.
        """
        try:
            token_file = open(os.environ['HOME'] + '/.osiris_token', 'r')
            access_token = token_file.read()
            if access_token is None:
                return None
            self.access_token = access_token
        except:    
            return None 

    def _assureSuccess(self, ret):
        """
        Thrown an error if the request was unsuccesful
        """
        if ret.status_code != 200:
            raise SignInError()

    def _getToken(self, username:str, password:str):
        """
        Obtain new token using passed credentials

        Args:
            username: str, s-number (including s)
            password: str, corresponding password

        Return:
            Authentication token, or throws an error if something went wrong.
        """
        ses = requests.Session()
        req1 = requests.Request('GET', 'https://auth-app-ruprd-ruprd.xpaas.caci.nl/oauth2/authorize?response_type=token&client_id=osiris-student-mobile-ruprd&redirect_uri=https://ru.osiris-student.nl').prepare()
        r = ses.send(req1)
        _assureSuccess(r)

        auth_state_start_idx = r.url.find('AuthState=')+10

        auth_state = r.url[auth_state_start_idx:]

        language = 'EN'
        submit = 'Login'

        payload = {'username': username, 'password': password, 'submit': submit, 'AuthState': requests.compat.unquote(auth_state)}

        req2 = requests.Request('POST', 'https://conext.authenticatie.ru.nl/simplesaml/module.php/core/loginuserpass.php?', params=payload, cookies=r.cookies).prepare()
        r2 = ses.send(req2)
        _assureSuccess(r2)

        saml_form = r2.text[r2.text.find('name="SAMLResponse"')+27:]
        saml_form = saml_form[:saml_form.find('"')]

        req = requests.Request('POST', 'https://engine.surfconext.nl/authentication/sp/consume-assertion', data={'SAMLResponse': saml_form}, cookies={'main': ses.cookies.get('main'), 'HTTPSERVERID': ses.cookies.get('HTTPSERVERID')})
        r3 = req.prepare()
        ret = ses.send(r3)
        _assureSuccess(ret)

        saml_form = ret.text[ret.text.find('name="SAMLResponse"')+27:]
        saml_form = saml_form[:saml_form.find('"')]

        relay_state = ret.text[ret.text.find('name="RelayState"')+25:]
        relay_state = relay_state[:relay_state.find('"')]

        req = requests.Request('POST', 'https://auth-app-ruprd-ruprd.xpaas.caci.nl/oauth2/authorize', data={'SAMLResponse': saml_form, 'RelayState': relay_state}, cookies={}).prepare()
        ret = ses.send(req)
        _assureSuccess(ret)

        access_token = ret.url[ret.url.find('access_token')+13:]
        access_token = access_token[:access_token.find('&')]
        return access_token
    
    def _getData(self, suff : str, method : str = 'GET', payload : str = ""):
        """
        Helper method for executing GET requests

        Args:
            method: GET, POST or POT, specifies request method
            suff: str, request URL suffix
            payload: (optional) str, request payload

        Return:
            request response
        """
        
        assert(method == 'POST' or method == 'GET' or method == 'PUT')
        assert isinstance(suff, str)
        assert isinstance(payload, str) 

        if self.access_token is None:
            raise NoTokenError()
        ses = requests.Session()
        req = requests.Request(method, 'https://ru.osiris-student.nl/student/osiris/student/' + suff, headers={'Authorization': 'Bearer ' + self.access_token, 'taal': 'EN'}, data=payload).prepare()
        return ses.send(req)

    def __init__(self):
        self.access_token = None
        self._readToken()
    
    def sign_in(self, username:str, password:str):
        """
        Sign in using credentials and store new token

        Args:
            username: str, s-number (including s)
            password: str, corresponding password

        Return:
            Login success status
        """
        
        assert isinstance(username, str)
        assert isinstance(password, str)

        try:
            self.access_token = self._getToken(self, username, password)
            token_file = open(os.environ['HOME'] + '/.osiris_token', 'w')
            token_file.write(self.access_token)
            return True
        except:
            return False

    def grades(self, limit:int):
        """
        Returns list of grades

        Args:
            limit: int, maximum number of results
        Return:
            List of grades
        """
        
        assert isinstance(limit, int)

        return self._getData('resultaten?limit=' + str(limit)).json()['items']

    def schedule(self, n_weeks:int):
        """
        Returns list representing schedule

        Args:
            n_weeks: int, number of weeks to be returned

        Return:
            Next n_weeks of schedule
        """
        
        assert isinstance(n_weeks, int)

        return self._getData('rooster/per_week?limit=' + str(n_weeks)).json()['items']

    def registered_courses(self, limit:int):
        """
        Returns list of courses registered for

        Args:
            limit: int, maximum number of courses

        Return:
            list of courses registered for
        """

        assert isinstance(limit, int)

        return list(self._getData('inschrijvingen/cursussen').json()['items']) + list(self._getData('inschrijvingen/wachtlijsten_cursus').json()['items']) + list(self._getData('inschrijvingen/voorinschrijvingen_cursus').json()['items'])

    def search_for_course(self, query:str):
        """
        Returns list of results after searching for query
        
        Args:
            query: str, query to search for

        Return:
            list of results
        """
        return self._getData('cursussen_voor_cursusinschrijving/zoeken', 'POST', '{"from":0,"size":25,"sort":[{"cursus_korte_naam.raw":{"order":"asc"}},{"cursus":{"order":"asc"}},{"collegejaar":{"order":"desc"}},{"blok":{"order":"asc"}}],"aggs":{"agg_terms_inschrijfperiodes_cursus.datum_vanaf":{"filter":{"bool":{"must":[{"range":{"inschrijfperiodes_cursus.datum_vanaf":{"lte":"now"}}},{"range":{"inschrijfperiodes_cursus.datum_tm":{"gte":"now"}}},{"terms":{"collegejaar":[2019]}}]}},"aggs":{"models":{"terms":{"field":"inschrijfperiodes_cursus.datum_vanaf","size":500,"order":{"_term":"asc"}}}}},"agg_terms_programma":{"filter":{"bool":{"must":[{"terms":{"id_cursus_blok":[147435,147607]}},{"terms":{"collegejaar":[2019]}}]}},"aggs":{"models":{"terms":{"field":"id_cursus_blok","size":500,"order":{"_term":"asc"}}}}},"agg_terms_collegejaar":{"filter":{"bool":{"must":[]}},"aggs":{"models":{"terms":{"field":"collegejaar","size":500,"order":{"_term":"desc"}}}}},"agg_terms_periode_omschrijving":{"filter":{"bool":{"must":[{"terms":{"collegejaar":[2019]}}]}},"aggs":{"models":{"terms":{"field":"periode_omschrijving","size":500,"order":{"_term":"asc"},"exclude":"Period: [0-9][0-9]-[0-9][0-9]-[0-9][0-9][0-9][0-9]"}}}},"agg_terms_aanvangsmaand":{"filter":{"bool":{"must":[{"terms":{"collegejaar":[2019]}}]}},"aggs":{"models":{"terms":{"field":"aanvangsmaand","size":500,"order":{"_term":"asc"}}}}},"agg_terms_faculteit_naam":{"filter":{"bool":{"must":[{"terms":{"collegejaar":[2019]}}]}},"aggs":{"models":{"terms":{"field":"faculteit_naam","size":500,"order":{"_term":"asc"}}}}},"agg_terms_cursustype_omschrijving":{"filter":{"bool":{"must":[{"terms":{"collegejaar":[2019]}}]}},"aggs":{"models":{"terms":{"field":"cursustype_omschrijving","size":500,"order":{"_term":"asc"}}}}},"agg_terms_voertalen.voertaal_omschrijving":{"filter":{"bool":{"must":[{"terms":{"collegejaar":[2019]}}]}},"aggs":{"models":{"terms":{"field":"voertalen.voertaal_omschrijving","size":500,"order":{"_term":"asc"}}}}},"agg_terms_bijvakker":{"filter":{"bool":{"must":[{"terms":{"collegejaar":[2019]}}]}},"aggs":{"models":{"terms":{"field":"bijvakker","size":500,"order":{"_term":"asc"}}}}},"agg_terms_docenten.docent":{"filter":{"bool":{"must":[{"terms":{"collegejaar":[2019]}}]}},"aggs":{"models":{"terms":{"field":"docenten.docent","size":500,"order":{"_term":"asc"}}}}}},"post_filter":{"terms":{"collegejaar":[2019]}},"query":{"bool":{"should":[{"match_phrase_prefix":{"cursus":"' + query + '"}},{"match_phrase_prefix":{"cursus_korte_naam":"' + query + '"}}],"minimum_should_match":1}}}').json()

    def get_course_info(self, course_id:str):
        """
        Obtains information about course

        Args:
            course_id: str, id_cursus_blok

        Return:
            information about course
        """
        return self._getData('cursussen_voor_cursusinschrijving/' + str(course_id)).json()

    def register_for_course(self, course_info):
        """
        Enrols in course

        Args:

        Return:

        """
        course_info['toets_voorzieningen'] = []
        course_info['toetsen'] = []
        course_info['werkvorm_groepen'] = []
        course_info['werkvormen'] = []
        # maybe something to do with dyselxia?
        course_info['werkvorm_voorzieningen'] = []
        course_info['blokken'] = []
        course_info['kosten'] = []
        course_info['inschrijfperiodes'] = []
        course_info['enrollment_type'] = 'regular'
        course_info['onderdeel_van'] = ''
        course_info['is_in_enrolment_period'] = False
        course_info['groepen'] = []
        print(course_info['id_cursus_blok'])
        return self._getData('inschrijvingen/cursussen/' + str(course_info['id_cursus_blok']), 'PUT', json.dumps(course_info))

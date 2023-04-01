# Request object to handle http requests
import re
import json

class RequestParser:

    def __init__(self, raw_request):
        # make sure raw_request is a str
        if isinstance(raw_request, bytes):
            raw_request = raw_request.decode("utf-8")
        self.method = ""
        self.full_url = ""
        self.url = ""
        self.query_string = ""
        self.protocol = ""
        self.headers = {}
        self.query_params = {}
        self.post_data = {}
        self.boundary = False
        self.content = []

        self.parse_request(raw_request)

    def parse_request(self, raw_request):

        if len(raw_request) > 0:
            # some data supplied
            # check end of line chars
            eol_char = '\r\n'  # default as per HTTP protocol
            if raw_request.find('\r\n') == -1:
                # some systems may use single char newline
                eol_char = '\n'
            # split request into individual lines
            request_lines = raw_request.split(eol_char)

            # first line holds request verb, url and protocol
            self.parse_first_line(request_lines[0])

            if len(request_lines) > 1:
                # next section holds header information - section ends with blank line
                # parse header lines
                line_num = 1  # skip first line
                while line_num < len(request_lines) and len(request_lines[line_num]) != 0:
                    header, value = self.parse_header_line(request_lines[line_num])
                    if header:
                        self.headers[header] = value
                    line_num += 1

                # check if any lines left for content
                # headers must be followed by blank line, then content lines
                line_num += 1  # skip blank line (if there)
                if line_num > (len(request_lines) - 1):
                    # no lines left
                    return

                # content is any remaining lines
                self.content = request_lines[line_num:]

                # handle content depending on Content-Type header
                content_type = self.get_header_value('Content-Type')
                if content_type:
                    # filter out form submissions
                    if content_type.find('multipart/form-data') != -1:
                        # data is in multipart/form-data format
                        # get boundary string
                        content_type_parts = content_type.split('boundary=')
                        if len(content_type_parts) == 2:
                            # found boundary
                            self.boundary = content_type_parts[1]
                        else:
                            # boundary not found - error
                            self.boundary = False
                            return
                        self.parse_content_form_data()

                    elif content_type.find('application/x-www-form-urlencoded') != -1:
                        # data is in application/x-www-form-urlencoded format
                        self.parse_content_form_url_encoded()

                    elif content_type.find('application/json') != -1 \
                            or content_type.find('application/javascript') != -1:
                        # data is in application/json format
                        self.parse_json_body()

                    else:
                        # treat as text
                        # leave content lines as list
                        pass
                else:
                    # no content type - ignore
                    pass

        else:
            return

    def get_header_value(self, header_name):
        if header_name in self.headers:
            return self.headers[header_name]
        else:
            return False

    def parse_first_line(self, first_line):
        # split line on spaces to get words
        line_parts = first_line.split()
        # should be three parts
        if len(line_parts) == 3:
            self.method = line_parts[0]
            self.full_url = line_parts[1]
            # try to split the full_url
            url_parts = line_parts[1].split('?', 1)
            self.url = url_parts[0]
            # is there a query string?
            if len(url_parts) > 1:
                self.query_string = url_parts[1]
            self.protocol = line_parts[2]
            # decode query string if it's there
            if len(self.query_string) > 0:
                self.query_params = self.decode_query_string(self.query_string)
        else:
            # something is wrong - flag it
            self.method = "ERROR"

    def parse_header_line(self, header_line):
        # split header line on : to get name and value
        line_parts = header_line.split(':')
        # should be two parts
        if len(line_parts) != 2:
            return (False, False)
        else:
            # strip leading and trailing spaces
            header_name = line_parts[0].strip()
            header_value = line_parts[1].strip()
            # return as tuple
            return (header_name, header_value)

    def decode_query_string(self, query_string):
        # split query string on &
        # this gives key=value list
        param_strings = query_string.split('&')
        params = {}
        for param_string in param_strings:
            try:
                # correctly formatted value
                # splits into 2 on =
                key, value = param_string.split('=')
                # values may be url encoded
                # unquote decodes special characters (well just a couple!)
                value = self.unquote(value)
            except:
                # no value specified
                key = param_string
                value = False

            # save param in dictionary
            params[key] = value
        return params

    def parse_content_form_data(self):
        # check if boundary found
        if not self.boundary:
            return
        line_num = 0  # first line in content
        while line_num < len(self.content):
            # find next section
            # will start with line --boundary
            while line_num < len(self.content) and self.content[line_num].find(self.boundary) == -1:
                line_num += 1
            # check end of lines
            if line_num >= len(self.content) - 1:
                # past end
                return
            # found boundary line
            # skip boundary line
            line_num += 1
            # section headers - find Content-Disposition or end of headers
            while line_num < len(self.content) and self.content[line_num].find("Content-Disposition:") == -1 \
                    and len(self.content[line_num]) != 0:
                line_num += 1
            # check end of lines
            if line_num >= len(self.content) - 1:
                # past end
                return
            # line num points at content-disposition line
            # extract name of variable - note does not handle arrays!
            # uses regular expression - learn how to use these!!
            match = re.search(r'name=\"([^\"]+)', self.content[line_num])
            # move pointer to next line
            line_num += 1
            try:
                # check if regular expression caught a variable
                var_name = match.group(1)
            except:
                continue  # skip this section
            # skip rest of section headers to find blank line
            while line_num < len(self.content) and len(self.content[line_num]) != 0:
                line_num += 1
            # skip blank line
            line_num += 1
            # check end of lines
            if line_num > len(self.content) - 1:
                # past last line
                return
            # line_num points at first line of data
            # read lines until we find start of next section
            # will start with line --boundary
            var_value = ""
            while line_num < len(self.content) and self.content[line_num].find(self.boundary) == -1:
                # build value from data lines
                if len(var_value) > 0:
                    var_value += "\n"
                var_value += self.content[line_num]
                line_num += 1
            # save data value
            self.post_data[var_name] = var_value
            # process next section

    def parse_content_form_url_encoded(self):
        # first line of content will contain data
        self.post_data = self.decode_query_string(self.content[0])

    def parse_json_body(self):
        # content contains json string
        line_num = 0  # first line in content
        json_string = ""
        # build json string from content lines
        while line_num < len(self.content):
            if len(json_string) > 0:
                json_string += "\n"
            json_string += self.content[line_num]
            line_num += 1
        # parse json string to dictionary
        self.post_data = json.loads(json_string)

    def url_match(self, test_url):
        # make sure string is cleaned and has leading /
        test_url = '/' + str(test_url).strip().strip('/')
        # check for / route
        if test_url == '/':
            if self.url == '/':
                return True
            else:
                return False
        if self.url == test_url:
            return True
        else:
            return False

    def unquote(self, url_string):
        # replaces %20 with space
        # %0A with newline
        url_string = re.sub(r'%20', ' ', url_string)
        url_string = re.sub(r'%0A', '\n', url_string)
        return url_string

    # return relevant data set depending on request method
    def data(self):
        if self.method == 'POST':
            return self.post_data
        elif self.method == 'GET':
            return self.query_params
        else:
            return False

    # return the request action
    # gets the value from the request method data section
    def get_action(self):
        if self.method == 'POST':
            if 'action' in self.post_data:
                return self.post_data['action']
            else:
                return False
        elif self.method == 'GET':
            if 'action' in self.query_params:
                return self.query_params['action']
            else:
                return False
        else:
            return False

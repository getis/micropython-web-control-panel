# Class to build an HTTP response

import json
import os


class ResponseBuilder:
    protocol = "HTTP/1.1"
    server = "Pi Pico Micropython"

    def __init__(self):
        # set default values
        self.status = 200
        self.content_type = "text/html"
        self.body = ""
        self.response = ""

    def set_content_type(self, content_type):
        self.content_type = content_type

    def set_status(self, status):
        self.status = status

    def set_body(self, body):
        self.body = body

    def serve_static_file(self, req_filename, default_file="/index.html"):
        # make sure filename starts with /
        if req_filename.find("/") == -1:
            req_filename = "/" + req_filename
        # remove query string
        if req_filename.find("?") != -1:
            req_filename, qs = req_filename.split("?", 1)
        # remove bookmark
        if req_filename.find("#") != -1:
            req_filename, qs = req_filename.split("#", 1)
        # filter out default file
        if req_filename == "/":
            req_filename = default_file
        # break filename into path and filename
        path, filename = req_filename.rsplit("/", 1)
        # reinstate root path for listdir
        if len(path) == 0:
            path = "/"
        # print(path, filename)
        # make sure working from root directory
        os.chdir("/")
        # get directory listing
        dir_contents = os.listdir(path)
        # check if file exists
        if filename in dir_contents:
            # file found
            # get file type
            name, file_type = filename.rsplit(".", 1)
            if file_type == "htm" or file_type == "html":
                self.content_type = "text/html"
            elif file_type == "js":
                self.content_type = "text/javascript"
            elif file_type == "css":
                self.content_type = "text/css"
            else:
                # let browser work it out
                self.content_type = "text/html"
            # load content
            file = open(path + "/" + filename)
            self.set_body(file.read())
            self.set_status(200)
        else:
            # file not found
            self.set_status(404)

    def set_body_from_dict(self, dictionary):
        self.body = json.dumps(dictionary)
        self.set_content_type("application/json")

    def build_response(self):
        self.response = ""
        # status line
        self.response += self.__class__.protocol \
                         + " " \
                         + str(self.status) \
                         + " " \
                         + self.get_status_message() \
                         + "\r\n"
        # Headers
        self.response += "Server: " + self.server + "\r\n"
        self.response += "Content-Type: " + self.content_type + "\r\n"
        self.response += "Content-Length: " + str(len(self.body)) + "\r\n"
        self.response += "Connection: Closed\r\n"
        self.response += "\r\n"
        # body
        if len(self.body) > 0:
            self.response += self.body

    def get_status_message(self):
        status_messages = {
            200: "OK",
            400: "Bad Request",
            403: "Forbidden",
            404: "Not Found"
        }
        if self.status in status_messages:
            return status_messages[self.status]
        else:
            return "Invalid Status"

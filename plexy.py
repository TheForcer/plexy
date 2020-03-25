import requests
import json


class Plexy(object):
    def __init__(self, config):
        """
        Object which contains the core code for managing requests.

        Args:
            config (Config): Bot configuration parameters
        """
        self.config = config

    def getAvailRequests(self):
        """Return a list of all available movie requests from ombi"""
        url = f"{self.config.url}/api/v1/Request/movie"

        payload = ""
        headers = {"apikey": self.config.ombi_apikey}

        json_data = json.loads(
            requests.request("GET", url, data=payload, headers=headers).text
        )
        json_list = [str(dict["id"]) for dict in json_data if dict["available"]]
        return json_list

    def delAvailRequests(self, availRequests):
        """Delete movie request given in the given list"""
        if not availRequests:
            return 0
        for x in availRequests:
            url = self.config.url + "/api/v1/Request/movie/" + x

            payload = ""
            headers = {"request": "", "apikey": self.config.ombi_apikey}

            requests.request("DELETE", url, data=payload, headers=headers)
        return 1

    def getID(self, title):
        """Get MovieDB ID from the movie title"""
        url = "https://api.themoviedb.org/3/search/movie"

        querystring = {
            "api_key": self.config.moviedb_apikey,
            "language": self.config.language,
            "query": title,
        }

        response = requests.request("GET", url, params=querystring)

        json_data = json.loads(response.text)
        if json_data["total_results"] < 1:
            return "nothing"

        id = str(json_data["results"][0]["id"])
        print(str(json_data["results"][0]["title"]))
        return id

    def sendRequest(self, id):
        """Request specific movie ID via ombi"""
        url = self.config.url + "/api/v1/Request/movie"

        payload = '{ "theMovieDbId": "' + id + '", "languageCode": "string"}'
        headers = {
            "content-type": "application/json-patch+json",
            "apikey": self.config.ombi_apikey,
            "accept": "application/json",
        }

        response = requests.request("POST", url, data=payload, headers=headers)
        return response

    def getTitle(self, id):
        """Return German title of a specific MovieDB movie ID"""
        url = "https://api.themoviedb.org/3/movie/" + str(id)

        payload = ""
        querystring = {
            "api_key": self.config.moviedb_apikey,
            "language": self.config.language,
        }

        response = requests.get(url, data=payload, params=querystring)
        return response.json()["title"]

    def requestList(self):
        """Return list of currently requested movies from Ombi"""
        url = self.config.url + "/api/v1/Request/movie"

        payload = '[\n  {\n    "id": 0,\n    "title": "string",\n    "overview": "string",\n    "imdbId": "string",\n    "tvDbId": "string",\n    "theMovieDbId": "string",\n    "releaseYear": "string",\n    "addedAt": "2018-12-22T12:05:24.510Z",\n    "quality": "string"\n  }\n]'
        querystring = {"": ""}
        headers = {
            "content-type": "application/json",
            "apikey": self.config.ombi_apikey,
        }

        response = requests.get(url, data=payload, headers=headers, params=querystring)

        requestList = []
        for request in response.json():
            singleMovie = {}
            if request["approved"]:
                singleMovie["id"] = request["theMovieDbId"]
                singleMovie["title"] = self.getTitle(request["theMovieDbId"])
                requestList.append(singleMovie)
        return requestList

    def getPopularMovies(self, amount):
        """Returns a list of the most popular movies from MovieDB"""

        url = "https://api.themoviedb.org/3/discover/movie"

        params = {
            "api_key": self.config.moviedb_apikey,
            "language": self.config.language,
            "sort_by": "popularity.desc",
        }

        json_response = requests.get(url, params=params).json()
        popular_list = [
            (movie["id"], movie["title"]) for movie in json_response["results"][:amount]
        ]
        return popular_list

    def delete_requests(self):
        """Delete all requests from ombi, which are available in Plex"""
        if not self.delAvailRequests(self.getAvailRequests()):
            return 0
        else:
            return 1

from chat_functions import send_text_to_room
from plexy import Plexy


class Command(object):
    def __init__(self, client, store, config, command, room, event):
        """A command made by a user

        Args:
            client (nio.AsyncClient): The client to communicate to matrix with

            store (Storage): Bot storage

            config (Config): Bot configuration parameters

            command (str): The command and arguments

            room (nio.rooms.MatrixRoom): The room the command was sent in

            event (nio.events.room_events.RoomMessageText): The event describing the command
        """
        self.client = client
        self.store = store
        self.config = config
        self.command = command
        self.room = room
        self.event = event
        self.args = self.command.split()[1:]
        self.plexy = Plexy(self.config)

    async def process(self):
        """Process the command"""
        if self.command.startswith("ping"):
            await send_text_to_room(self.client, self.room.room_id, "Pong!")
        elif self.command.startswith("commands"):
            await self._show_commands()
        elif self.command.startswith("help"):
            await self._show_help()
        elif self.command.startswith("request"):
            await self._request_movie()
        elif self.command.startswith("list"):
            await self._show_requests()
        elif self.command.startswith("delete"):
            await self._delete_requests()
        elif self.command.startswith("popular"):
            await self._show_popular_movies()
        else:
            await self._unknown_command()

    async def _show_help(self):
        """Show the Plexy help text"""
        if not self.args:
            text = "Hallo, ich bin **Plexy**, ein Bot für den Plex-Mediaserver von Lukas. Mit `!plex commands` kannst du dir alle meine Befehle anzeigen lassen."
            await send_text_to_room(self.client, self.room.room_id, text)
            return

    async def _show_commands(self):
        """Show all available commands"""
        text = "**Verfügbare Befehle**:<br>- `!plex help` -- Zeigt die Hilfe an.<br>- `!plex commands` -- Zeigt alle verfügbaren Befehle an.<br>- `!plex request <Filmname>` -- Fordert einen gewünschten Film an.<br>- `!plex list` -- Listet alle angefragten Filme auf.<br>- `!plex delete` -- Löscht alle verfügbaren Anfragen in ombi.<br>- `!plex popular <Anzahl>` -- Zeigt aktuell beliebte Filme an."
        await send_text_to_room(self.client, self.room.room_id, text)

    async def _show_requests(self):
        """Shows the movies which are currently requested in Ombi."""
        requests = self.plexy.getAvailRequests(available=False)
        text = "Das sind die aktuell in Ombi angefragten Filme:"
        if not requests:
            text = f"Aktuell sind keine Filme angefragt!"
            await send_text_to_room(self.client, self.room.room_id, text)
            return
        for movie in requests:
            text = f"{text}<br>- [{movie['title']}](https://www.themoviedb.org/movie/{movie['theMovieDbId']})"
        await send_text_to_room(self.client, self.room.room_id, text)
        return

    async def _show_popular_movies(self):
        """Shows the most popular movies from MovieDB"""
        text = f"Hey {self.event.sender}, hier sind aktuell beliebte Kinofilme:"
        # Default to three movies if no parameter is given
        if not self.args:
            movies = self.plexy.getPopularMovies(3)
            for x in movies:
                text = f"{text}<br>- [{x[1]}](https://www.themoviedb.org/movie/{x[0]})"
        else:
            # Check if a integer value has been entered and is in range
            try:
                amount = int(self.args[0])
                if amount not in range(1, 16):
                    raise ValueError
                movies = self.plexy.getPopularMovies(int(self.args[0]))
                for x in movies:
                    text = (
                        f"{text}<br>- [{x[1]}](https://www.themoviedb.org/movie/{x[0]})"
                    )
            except ValueError:
                text = f"Du hast keine gültige Zahl (1-15) eingegeben."

        await send_text_to_room(self.client, self.room.room_id, text)
        return

    async def _request_movie(self):
        """Request a movie via ombi"""
        # Output if no film title is given as parameter
        if not self.args:
            text = "Bitte einen Filmtitel angeben :) `!plex request Deadpool` zum Beispiel. "
            await send_text_to_room(self.client, self.room.room_id, text)
            return
        requested_title = " ".join(self.args)
        id = self.plexy.getID(requested_title)
        # If above method returns no movies, send info regarding that
        if id == "nothing":
            await send_text_to_room(
                self.client, self.room.room_id, "Nichts dazu gefunden :("
            )
            return
        # Get German movie title for display reasons
        title = self.plexy.getTitle(id)
        try:
            self.plexy.sendRequest(id)
            text = f"Ich habe den Film [{title}](https://www.themoviedb.org/movie/{id}) für dich angefordert. Du wirst benachrichtigt werden, sobald der Film verfügbar ist :)"
            await send_text_to_room(self.client, self.room.room_id, text)
        except UserWarning:
            text = "Es trat ein Fehler beim Anfordern des Titels auf."
            await send_text_to_room(self.client, self.room.room_id, text)
        return

    async def _delete_requests(self):
        """Delete all movie requests in ombi which are available within Plex"""
        # Check if event.sender is in whitelist, else cancel command
        if (self.config.admin_whitelist_enabled) and (
            self.event.sender not in self.config.admin_whitelist
        ):
            return
        # Response depending if any requests are available for deletion
        if self.plexy.delete_requests():
            text = f"Hey {self.event.sender}, ich habe die verfügbaren Filme gelöscht!"
        else:
            text = "Es gibt keine Requests zum Löschen!"
        await send_text_to_room(self.client, self.room.room_id, text)

    async def _unknown_command(self):
        await send_text_to_room(
            self.client,
            self.room.room_id,
            f"Unbekannter Befehl '{self.command}'. Mit `!plex commands` kannst du dir meine Befehle anzeigen lassen.",
        )

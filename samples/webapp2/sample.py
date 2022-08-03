import webapp2

from pytracts import messages, webapp2 as pt


class TeamMessage(messages.Message):
    name = messages.StringField()
    colors = messages.StringField(repeated=True)
    mascot = messages.StringField()


class TeamsResponseMessage(messages.Message):
    page = messages.IntegerField()
    teams = messages.MessageField(TeamMessage)


gophers = TeamMessage(name='Minnesota', colors=['maroon', 'gold'], mascot='Goldy Gopher')
badgers = TeamMessage(name='Wisconsin', colors=['cardinal', 'gold'], mascot='Bucky Badger')


class TeamHandler(webapp2.RequestHandler):

    # Annotate endpoints to automatically serialize to JSON
    @pt.endpoint
    def get_teams(self):

        response = TeamsResponseMessage()
        response.page = 1
        response.teams = [gophers, badgers]

        return response

    # Use Webapp2 exceptions for other status codes
    @pt.endpoint
    def get_team(self, team_id):
        if team_id == 'gophers':
            return gophers
        elif team_id == 'badgers':
            return badgers
        else:
            raise webapp2.exc.HTTPNotFound()

    # Take a message from the JSON body of the request
    @pt.endpoint(team_details=TeamMessage)
    def create_team(self, team_details):
        # Create the team based on details

        # Return 201 status with a location header
        return 201, {'Location': webapp2.uri_for('get_team', team_id='new-team-id')}


app = webapp2.WSGIApplication([
    webapp2.Route(r'/v1/teams',
                  methods=['GET'],
                  handler='example.TeamHandler:get_teams',
                  name='get_teams'),
    webapp2.Route(r'/v1/teams',
                  methods=['POST'],
                  handler='example.TeamHandler:create_team',
                  name='create_team'),
    webapp2.Route(r'/v1/teams/<team_id>',
                  methods=['GET'],
                  handler='example.TeamHandler:get_team',
                  name='get_team')
], debug=True)
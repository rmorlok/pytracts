from flask import Flask, url_for
import werkzeug

from pytracts import messages, flask as pt

class TeamMessage(messages.Message):
    id = messages.StringField()
    name = messages.StringField()
    colors = messages.StringField(repeated=True)
    mascot = messages.StringField()


class TeamsResponseMessage(messages.Message):
    page = messages.IntegerField()
    teams = messages.MessageField(TeamMessage, repeated=True)


gophers = TeamMessage(id='gophers', name='Minnesota', colors=['maroon', 'gold'], mascot='Goldy Gopher')
badgers = TeamMessage(id='badgers', name='Wisconsin', colors=['cardinal', 'gold'], mascot='Bucky Badger')
teams = dict([(t.id, t) for t in [gophers, badgers]])

# Annotate endpoints to automatically serialize to JSON
@pt.endpoint('/v1/teams')
def get_teams():

    response = TeamsResponseMessage()
    response.page = 1
    response.teams = list(teams.values())

    return response

# Use Webapp2 exceptions for other status codes
@pt.endpoint('/v1/teams/<team_id>')
def get_team(team_id):
    if team_id in teams:
        return teams[team_id]
    else:
        raise werkzeug.exceptions.NotFound(f'Team {team_id} not found')

# Take a message from the JSON body of the request
@pt.endpoint('/v1/teams', methods=['POST'], body={'team_details': TeamMessage})
def create_team(team_details):
    # Create the team based on details
    if team_details.id in teams:
        raise werkzeug.exceptions.Forbidden(f'Team {team_details.id} already exists')

    teams[team_details.id] = team_details
    # Return 201 status with a location header
    return 201, {'Location': url_for('get_team', team_id=team_details.id)}

# Run with
# $ export FLASK_APP=sample
# $ flask run
app = Flask(__name__)
pt.register_endpoints(app)
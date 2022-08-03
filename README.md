# pytracts

[![Downloads](https://img.shields.io/pypi/dm/pytracts)](https://pypistats.org/packages/pytracts)

A library for defining data contracts in native Python code, based on the [Google ProtoRPC library](https://code.google.com/p/google-protorpc/)

## Define JSON Contracts with Python Objects
 
```python
from pytracts import messages, to_json, to_dict

class TeamMessage(messages.Message):
    name = messages.StringField()
    colors = messages.StringField(repeated=True)
    mascot = messages.StringField()

gophers = TeamMessage(name='Minnesota', colors=['maroon', 'gold'], mascot='Goldy Gopher')

# Export data to python dictionary
print to_dict.encode_message(gophers)
#=> {'colors': ['maroon', 'gold'], 'name': 'Minnesota', 'mascot': 'Goldy Gopher'}

# Export data to json string
print to_json.encode_message(gophers)
#=> {"colors": ["maroon", "gold"], "name": "Minnesota", "mascot": "Goldy Gopher"}

# Load data from dict
badgers = to_dict.decode_message(TeamMessage, {
    "name": "Wisconsin", 
    "mascot": "Bucky Badger", 
    "colors": ["cardinal", "white"]})
print badgers.name
#=> Wisconsin

# Load data from JSON
badgers = to_json.decode_message(TeamMessage, '{
    "name": "Wisconsin", 
    "mascot": "Bucky Badger", 
    "colors": ["cardinal", "white"]}')
print badgers.mascot
#=> Bucky Badger
```

## Support for nested messages

```python
from pytracts import messages

class AddressMessage(messages.MessageField)
    street = messages.StringField()
    city = messages.StringField()
    state = messages.StringField()
    zip = messages.IntegerField()

    
class PersonMessage(messages.Message):
    home_address = messages.MessageField(AddressMessage)
    work_address = messages.MessageField(AddressMessage)

leslie = PersonMessage(
    home_address=AddressMessage(
        street='123 Sesame St', 
        city='Pawnee', state='IN', zip=22113),
    work_address=AddressMessage(
        street='987 Brookstone Ln', 
        city='Pawnee', state='IN', zip=22113)
)
```

## Support for Arbitrary Data Types and Unstructured JSON

Arbitrary types:

```python
from pytracts import messages, to_json

class BoxMessage(messages.Message):
    height = messages.UntypedField()
    width = messages.UntypedField()

b = BoxMessage(height=123, width="65%")

print to_json.encode_message(b)
#=> {"width": "65%", "height": 123}
```

Unstructured dictionaries:

```python
from pytracts import messages, to_json

class UserMessage(messages.Message):
    name = messages.StringField()
    email = messages.StringField()
    metadata = messages.DictField()

bob = UserMessage(name='Bob', email='bob@example.com', metadata={'height': 72, 'weight': 180})

print to_json.encode_message(bob)
#=> {"metadata": {"weight": 180, "height": 72}, "email": "bob@example.com", "name": "Bob"}
```

## Annotate Flask Handlers for JSON serialization

```python
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

app = Flask(__name__)
pt.register_endpoints(app)
```

See [full sample app](./samples/flask/README.md) for more details.

# PATCH support

Check if properties have any value set, as opposed to the default value

```python
t = TeamMessage()

print TeamMessage.name.is_set(t)
#=> False

print t.name
#=> None

t.name = None

print TeamMessage.name.is_set(t)
#=> True

print t.name
#=> None
```
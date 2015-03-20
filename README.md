# protopy

A library for defining data contracts in native Python code, based on the Google ProtoRPC library (https://code.google.com/p/google-protorpc/)

## Define JSON Contracts with Python Objects
 
```
from protopy import messages, protojson, protodict

class TeamMessage(messages.Message):
    name = messages.StringField()
    colors = messages.StringField(repeated=True)
    mascot = messages.StringField()

gophers = TeamMessage(name='Minnesota', colors=['maroon', 'gold'], mascot='Goldy Gopher')

# Export data to python dictionary
print protodict.encode_message(gophers)
#=> {'colors': ['maroon', 'gold'], 'name': 'Minnesota', 'mascot': 'Goldy Gopher'}

# Export data to json string
print protojson.encode_message(gophers)
#=> {"colors": ["maroon", "gold"], "name": "Minnesota", "mascot": "Goldy Gopher"}

# Load data from dict
badgers = protodict.decode_message(TeamMessage, {"name": "Wisconsin", "mascot": "Bucky Badger", "colors": ["cardinal", "white"]})
print badgers.name
#=> Wisconsin

# Load data from JSON
badgers = protojson.decode_message(TeamMessage, '{"name": "Wisconsin", "mascot": "Bucky Badger", "colors": ["cardinal", "white"]}')
print badgers.mascot
#=> Bucky Badger
```

## Support for nested messages

```
from protopy import messages

class AddressMessage(messages.MessageField)
    street = messages.StringField()
    city = messages.StringField()
    state = messages.StringField()
    zip = messages.IntegerField()

    
class PersonMessage(messages.Message):
    home_address = messages.MessageField(AddressMessage)
    work_address = messages.MessageField(AddressMessage)

leslie = PersonMessage(
    home_address=AddressMessage(street='123 Sesame St', city='Pawnee', state='IN', zip=22113),
    work_address=AddressMessage(street='987 Brookstone Ln', city='Pawnee', state='IN', zip=22113)
)
```

## Support for Arbitrary Data Types and Unstructured JSON

Arbitrary types:

```
from protopy import messages, protojson

class BoxMessage(messages.Message):
    height = messages.UntypedField()
    width = messages.UntypedField()

b = BoxMessage(height=123, width="65%")

print protojson.encode_message(b)
#=> {"width": "65%", "height": 123}
```

Unstructured dictionaries:

```
from protopy import messages, protojson

class UserMessage(messages.Message):
    name = messages.StringField()
    email = messages.StringField()
    metadata = messages.DictField()

bob = UserMessage(name='Bob', email='bob@example.com', metadata={'height': 72, 'weight': 180})

print protojson.encode_message(bob)
#=> {"metadata": {"weight": 180, "height": 72}, "email": "bob@example.com", "name": "Bob"}
```

## Annotate Webapp2 Handlers to handle automatice JSON serialization

```
import webapp2

import protopy
from protopy import messages

class TeamMessage(messages.Message):
    name = messages.StringField()
    colors = messages.StringField(repeated=True)
    mascot = messages.StringField()

    
class TeamsResponseMessage(messages.Message):
    page = messages.IntegerField()
    teams = messages.MessageField(TeamMessage)

gophers = TeamMessage(name='Minnesota', colors=['maroon', 'gold'], mascot='Goldy Gopher')
badgers = TeamMessage(name='Wisconsin', colors=['cardinal', 'gold'], masot='Bucky Badger')


class TeamHandler(webapp2.RequestHandler):
    
    # Annotate endpoints to automatically serialize to JSON
    @protopy.endpoint
    def get_teams(self):
        
        response = TeamsResponseMessage()
        response.page = 1
        response.teams = [gophers, badgers]

        return response

    # Use Webapp2 exceptions for other status codes
    @protopy.endpoint
    def get_team(self, team_id):
        if team_id == 'gophers':
            return gophers
        elif team_id == 'badgers':
            return badgers
        else:
            raise webapp2.exc.HTTPNotFound()
    
    # Take a message from the JSON body of the request
    @protopy.endpoint(team_details=TeamMessage)
    def create_team(self, team_details):
        # Create the team based on details 

        # Return 201 status with a location header
        return 201, {'Location': webapp2.uri_for('get_team', team_id='new-team-id')}

app = webapp2.WSGIApplication([
    webapp2.Route(r'/v1/teams',             methods=['GET'],    handler='example.TeamHandler:get_teams',       name='get_teams'),
    webapp2.Route(r'/v1/teams',             methods=['POST'],   handler='example.TeamHandler:create_team',     name='create_team'),
    webapp2.Route(r'/v1/teams/<team_id>',   methods=['GET'],    handler='example.TeamHandler:get_team',        name='get_team')
], debug=True)
```
# Flask Sample

This folder contains a sample Flask application with a Postman collection to query the endpoints.

To install/run (assuming using [pyenv](https://github.com/pyenv/pyenv)):

```bash
# Setup pyenv
pyenv install 3.10.3
pyenv local 3.10.3

# Install prerequisites
pip install -r requirements.txt

# Run the application
export FLASK_APP=sample
flask run
```

In a separate termination you can verify that the app is working using:

```bash
curl http://localhost:5000/v1/teams
# {
#   "page": 1, 
#   "teams": [
#     {
#       "id": "gophers", 
#       "name": "Minnesota", 
#       "colors": ["maroon", "gold"], 
#       "mascot": "Goldy Gopher"
#     }, {
#       "id": "badgers", 
#       "name": "Wisconsin", 
#       "colors": ["cardinal", "gold"], 
#       "mascot": "Bucky Badger"
#     }
#   ]
# }
```

Additional commands can be run using the [Postman](https://www.postman.com/) collection.
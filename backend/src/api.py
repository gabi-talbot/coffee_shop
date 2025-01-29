import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth
from werkzeug.exceptions import NotFound, BadRequest, UnprocessableEntity

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the database
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this function will add one
'''
db_drop_and_create_all()


# utility function to check data format of drink recipe
def check_recipe(recipe):
    """
    Checks format of drink recipe passed via a request
    :param recipe: The data to be checked
    :return: Boolean
    """
    flag = True
    if not isinstance(recipe, dict):
        flag = False
        print("no recipe")
    if not isinstance(recipe['color'], str):
        flag = False
        print("color not str")
    if not isinstance(recipe['name'], str):
        flag = False
        print("name not str")
    if not isinstance(recipe['parts'], int):
        flag = False
        print("parts not int")

    return flag
# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''

@app.route('/headers')
def headers():
    return jsonify({
        'success': True,
        'description': 'it works!'
    }, 200)

@app.route('/drinks')
@requires_auth('get:drinks')
def get_drinks(jwt):
    """
    Retrieves all drinks from the database
    :return: 200 and formatted drinks if successful, 404 if not found
    """
    try:
        # query db for all drinks
        drinks = Drink.query.all()

        # format drinks
        drink_short = [drink.short() for drink in drinks]

        return jsonify(
            {'success': True,
             'drinks': drink_short
             }), 200

    except Exception as e:
        print(e)
        raise NotFound('Drinks not found')

'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_detail(jwt):
    """
    Retrieves all detailed drinks from the database
    :return: 200 and formatted drinks if successful, 404 if not found
    """
    try:
        # query db for all drinks
        drinks = Drink.query.all()

        #format drinks
        drinks_long = [drink.long() for drink in drinks]

        return jsonify({
            'success': True,
            'drinks': drinks_long
        }), 200

    except Exception as e:
        print(e)
        raise NotFound('Drinks not found')

'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} 
    where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def post_drinks(jwt):
    """
    Checks request is valid and saves a new drink to the database

    :return: 200 and drink if successful, 400 if recipe format is not
    correct, 422 if request data cannot be processed
    """
    try:
        data = request.get_json()
        recipe = data['recipe']
        list_recipe = [recipe]

        if not check_recipe(recipe):
            raise BadRequest('Invalid recipe')

        str_recipe = json.dumps(list_recipe)

        drink = Drink(title=data['title'], recipe=str_recipe)

        drink.insert()

        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        }), 200

    except Exception as e:
        print(e)
        raise UnprocessableEntity('Request data cannot be processed')

'''
@COMPLETED implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} 
    where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks/<id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def patch_drinks(jwt, id):
    """
    Patches drink of same id, if found

    :param id: int

    :return: 200 and drink if successful, 404 if not found, 400 if recipe
    format is not correct, 422 if request data cannot be processed
    """
    try:
        drink = Drink.query.get_or_404(id)

        data = request.get_json()
        title = data.get('title', None)
        recipe = data.get('recipe', None)

        if title:
            drink.title = title
            print(drink.title)
            print(drink)

        if recipe:
            if not check_recipe(data['recipe']):
                raise BadRequest('Invalid recipe')
            list_recipe = [recipe]
            drink.recipe = json.dumps(list_recipe)

        drink.update()

        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        }), 200

    except Exception as e:
        print(e)
        raise UnprocessableEntity('Request data cannot be processed')
'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(jwt, id):
    """
    Deletes drink of same id, if found

    :param id: int

    :return: 200 and drink id, 404 if not found.
    """
    try:
        drink = Drink.query.get_or_404(id)
        drink.delete()

        return jsonify({
            'success': True,
            'delete': id
        })
    except Exception as e:
        print(e)
        raise NotFound('Drink not found')

# Error Handling

@app.errorhandler(UnprocessableEntity)
def unprocessable(e):
    """
    Receives the error and propagates response
    """
    return jsonify({
        "success": False,
        "error": UnprocessableEntity.code,
        "message": e.description
    }), 422

@app.errorhandler(BadRequest)
def bad_request(e):
    """
    Receives the error and propagates response
    """
    return jsonify({
        "success": False,
        "error": BadRequest.code,
        "message": e.description
    }), 400

'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''

'''
@COMPLETE implement error handler for 404
    error handler should conform to general task above
'''
@app.errorhandler(NotFound)
def not_found(e):
    """
    Receive the NotFound error and propagates response
    """

    return jsonify({
        "success": False,
        "error": NotFound.code,
        "message": e.description
    }), 404

'''
@COMPLETE implement error handler for AuthError
    error handler should conform to general task above
'''
@app.errorhandler(AuthError)
def handle_auth_error(e):
    """
    Receive the raised authorization error and propagates response
    """
    response = jsonify(e.error)
    response.status_code = e.status_code
    return response
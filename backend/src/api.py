import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

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
    if not recipe['color'] or recipe['name'] or recipe['parts']:
        flag = False
    if not isinstance(recipe['color'], str):
        flag = False
    if not isinstance(recipe['name'], str):
        flag = False
    if not isinstance(recipe['parts'], int):
        flag = False

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
def get_drinks():
    # query db for all drinks
    drinks = Drink.query.all()

    # format drinks
    drink_short = [drink.short() for drink in drinks]

    return jsonify(
        {'success': True,
         'drinks': drink_short
         }), 200

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
def get_drinks_detail():
    # query db for all drinks
    drinks = Drink.query.all()

    #format drinks
    drinks_long = [drink.long() for drink in drinks]

    return jsonify({
        'success': True,
        'drinks': drinks_long
    }), 200

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
def post_drinks():
    """
    Checks request is valid and saves a new drink to the database
    :return: 200 and drink if successful, 400 if invalid request
    """

    try:
        data = request.get_json()
        recipe = data['recipe']

        if not check_recipe(recipe):
            abort(400)

        str_recipe = json.dumps(recipe)
        drink = Drink(title=data['title'], recipe=str_recipe)

        drink.insert()

    except Exception as e:
        abort(400)

    return jsonify({
        'success': True,
        'drinks': [drink.long()]
    }), 200


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
def patch_drinks(id):
    """
    Patches drink of same id, if found
    :param id: int
    :return: 200 and drink if successful, 404 if not found
    """

    try:
        drink = Drink.query.get_or_404(id)
        data = request.get_json()
        if data['title']:
            drink.title = data['title']
        if data['recipe']:
            if not check_recipe(data['recipe']):
                abort(400)

            drink.recipe = data['recipe']

        drink.update()

    except Exception as e:
        abort(400)

    return jsonify({
        'success': True,
        'drinks': [drink.long()]
    }), 200

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
def delete_drinks(id):
    """
    Deletes drink of same id, if found
    :param id: int
    :return: 200 and drink id, 404 if not found.
    """
    try:
        drink = Drink.query.get_or_404(id)
        drink.delete()
    except Exception as e:
        abort(400)

# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(e):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


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
@app.errorhandler(404)
def not_found(e):
    """
    Receive the NotFound error and propagates response
    """
    return jsonify({
        "success": False,
        "error": 404,
        "message": "Resource not found"
    })

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
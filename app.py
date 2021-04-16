"""REST API app using "Flask + SQLAlchemy" with marshmallow. """

from flask import Flask,jsonify,request,make_response
from http import HTTPStatus
from flask_sqlalchemy import SQLAlchemy  #thorugh python change is databse
from marshmallow import fields,ValidationError #handle ValidationError
from marshmallow_sqlalchemy import ModelSchema
from sqlalchemy.types import TypeDecorator

### ERRORS HANDLING ##
def page_not_found(e):  # error:URL Not Found
    return jsonify({'message': 'URL not found !!'}), HTTPStatus.NOT_FOUND
def BAD_REQUEST(e): #errpr: check syntax error, Invalid Request message
    return jsonify({'message': 'BAD REQUEST !! Syntax,Invalid Request Message Framing,Or Deceptive Request Routing'}),HTTPStatus.BAD_REQUEST
def method_not_allowed(e): # error:when you pass wrong url
    return jsonify({'message': 'Method Not Allowed !!'}), HTTPStatus.METHOD_NOT_ALLOWED

### DATABASE DEFINATION ###
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']="sqlite:///recipe.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']= False

app.register_error_handler(404,page_not_found)
app.register_error_handler(400,BAD_REQUEST)
app.register_error_handler(405,method_not_allowed)
db=SQLAlchemy(app)


##### MODELS #####
class StrippedString(TypeDecorator):

    impl = db.String

    def process_bind_param(self, value, dialect):
        # In case you have nullable string fields and pass None
        return value.strip() if value else value

    def copy(self, **kw):
        return StrippedString(self.impl.length)
class recipe(db.Model):
    Recipe_ID=db.Column(db.Integer,primary_key=True)
    Recipe=db.Column(StrippedString(500),nullable=False)
    Dish=db.Column(StrippedString(20),nullable=False)

    def create(self):
       db.session.add(self)
       db.session.commit()
       return self

    def __init__(self,Dish,Recipe):
            self.Dish = Dish
            self.Recipe=Recipe

    def __repr__(self):
                return f"{self.Recipe_ID}"



### Custom validator ###
def must_not_be_blank(data):
    if not data:
        raise ValidationError("Can't be Empty!") #raise Validation error on empty input data

def null_and_type_check(data, recipeObject): #check for not empty-string data input
   messageString = []
   emptyVariables = []   
   if data.get('Recipe'):
      recipeObject.Recipe = data['Recipe']
      if type(recipeObject.Recipe)!=str:
         messageString.append("Invalid data type: Recipe needs to be String")
      if type(recipeObject.Recipe)==str and data.get('Recipe').strip() == '':
         emptyVariables.append("Error: Recipe cannot be empty")
   else:
      emptyVariables.append("Error: Recipe cannot be empty")

   if data.get('Dish'):
      recipeObject.Dish = data['Dish']
      if type(recipeObject.Dish)!=str or (recipeObject.Dish==''):
         messageString.append(" Invalid data type: Dish needs to be String")
      if  type(recipeObject.Dish)==str and data.get('Dish').strip() == '' : 
         emptyVariables.append("Error: Dish cannot be empty")
   else:
      emptyVariables.append("Error: Dish cannot be empty")
   output = emptyVariables + messageString
   if output:
      return ', '.join(output)
   else:
      return '' 

### SCHEMAS ###
class recipeSchema(ModelSchema):
      class Meta(ModelSchema.Meta):
           model = recipe
           sqla_session = db.session
      Recipe_ID = fields.Integer(dump_only=True)
      Recipe = fields.String(required=True,validate=must_not_be_blank)  #custom error
      Dish = fields.String(required=True,validate=must_not_be_blank)  #custom error

##### API #####

# Get All Recipes    
@app.route('/recipes', methods=['GET'])
def get_recipes():
   
   get_all = recipe.query.all()
   recipe_schema = recipeSchema(many=True)
   recipes = recipe_schema.dump(get_all)
   if recipes:
      return make_response(jsonify({"Recipes": recipes}),HTTPStatus.OK)
   return jsonify({'message': 'recipes not found !'}), HTTPStatus.NOT_FOUND

# Get All Recipes By ID
@app.route('/recipes/<int:Recipe_ID>', methods=['GET'])
def get_recipe_by_id(Recipe_ID):
   get_recipe = recipe.query.get(Recipe_ID)
   recipe_schema = recipeSchema()
   recipes = recipe_schema.dump(get_recipe)
   if recipes:
          return make_response(jsonify({"Recipe": recipes}),HTTPStatus.OK)
   return jsonify({'message': 'recipe not found'}), HTTPStatus.NOT_FOUND

#Add Recipe 
@app.route('/recipes', methods=['POST'])
def create_recipe():
   data = request.get_json()
   if not data:
        return {"message": "No input data provided"},400 #error:data is not in json format
   recipe_schema = recipeSchema()
   try:
      recipes = recipe_schema.load(data)
   except ValidationError as err:
        return err.messages, 422    #error: invalid datatype of input data
   improper_data = null_and_type_check(data, recipes)
   if improper_data:
      return {"message": improper_data}, 422
   result = recipe_schema.dump(recipes.create())
   return make_response(jsonify({"Recipe": result})),HTTPStatus.CREATED
   
#Update Recipe
@app.route('/recipes/<int:Recipe_ID>', methods=['PUT'])
def update_receipe(Recipe_ID):
      data=request.get_json()
      if not data:
        return {"message": "No input data provided"} ,400 #error:data is not in json format
      get_recipe=recipe.query.get(Recipe_ID)
      if(get_recipe == None):
         return {"message": "Recipe Id doesn't exist, can't update!"}, 404
      improperData = null_and_type_check(data, get_recipe) #error: check for not empty-string data input
      if improperData:
            return {"message": improperData}, 422
      db.session.add(get_recipe)
      db.session.commit()
      recipe_schema = recipeSchema(only=['Recipe_ID', 'Recipe', 'Dish'])
      recipes = recipe_schema.dump(get_recipe)
      if recipes:
          return make_response(jsonify({"Recipe": recipes})),HTTPStatus.OK
      return jsonify({'message': 'recipe not found'}),HTTPStatus.NOT_FOUND 
     
#Delete Recipe By ID
@app.route('/recipes/<int:Recipe_ID>', methods=['DELETE'])
def delete_recipe_by_id(Recipe_ID):
   get_recipe = recipe.query.get(Recipe_ID)
   if get_recipe:
      db.session.delete(get_recipe)
      db.session.commit()
      return make_response(jsonify({'message':'Recipe Deleted!'})),HTTPStatus.OK # recipe deleted sucessfully
   return jsonify({'message': 'recipe not found'}), HTTPStatus.NOT_FOUND  #error:if recipe not found in database

#Delete All Recipes
@app.route('/recipes',methods=['DELETE'])
def delete_all():
   db.session.query(recipe).delete()
   db.session().commit()
   return make_response(jsonify({'message':' ALL The Recipes Are Deleted!'})),HTTPStatus.OK


  

if __name__=="__main__":
    app.run(host="0.0.0.0",port=5000,debug=True)
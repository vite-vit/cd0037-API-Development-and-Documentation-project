import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def numbered_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app, resources={r"*": {"origins": "*"}})

    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET, PUT, POST, DELETE, OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """
    @app.route('/categories')
    def retrieve_categories():
        categories = Category.query.order_by(Category.type).all()
        return jsonify({
            'success': True,
            'categories': {category.id: category.type for category in categories}
        })

    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """
    @app.route('/questions')
    def retrieve_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = numbered_questions(request, selection)
        categories = Category.query.order_by(Category.type).all()

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(selection),
            'categories': {category.id: category.type for category in categories},
            'current_category': None
        })

    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        question = Question.query.filter(
            Question.id == question_id).one_or_none()

        if question is None:
            abort(404)

        question.delete()
        # selection = Question.query.order_by(Question.id).all()
        # current_questions = numbered_questions(request, selection)

        return jsonify({
            'success': True,
            'deleted': question_id,
            # 'questions': current_questions,
            # 'total_questions': len(selection)
        })

    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """
    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()

        if not body:
            abort(400)

        new_category = body.get('category', None)
        new_difficulty = body.get('difficulty', None)
        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
      

        if new_question is None or new_answer is None or new_category is None or new_difficulty is None:
            abort(400)

        try:
            question = Question(category=new_category,
                                difficulty=new_difficulty,
                                question=new_question,
                                answer=new_answer,
                               )
            question.insert()

            # selection = Question.query.order_by(Question.id).all()
            # current_questions = numbered_questions(request, selection)

            return jsonify({
                'success': True,
                # 'created': question.id,
                # 'questions': current_questions,
                # 'total_questions': len(selection)
            })
        except:
            abort(422)

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """
    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        body = request.get_json()
        if not body:
            abort(400)

        search_term = body.get('searchTerm',None)

        questions = Question.query.filter(
            Question.question.ilike(f'%{search_term}%')).all()
        current_questions = [question.format() for question in questions]
        return jsonify({
            'success': True,
            'questions': current_questions, 
            'total_questions': len(questions),
            'current_category': None,
        })

    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    @app.route('/categories/<int:category_id>/questions',methods=['GET'])
    def retrieve_questions_by_category(category_id):
        current_category = Category.query.get(category_id)
        if current_category is None:
            abort(404)

        current_questions = Question.query.filter(Question.category == category_id).all()
        if not current_questions:
            return abort(404)
        result_questions = [question.format() for question in current_questions]
        return jsonify({
            'success': True,
            'questions': result_questions,
            'total_questions': len(result_questions),
            'current_category': current_category.format(),
            'categories': [category.format() for category in Category.query.all()]
    })

    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    @app.route('/quizzes', methods=['POST'])
    def play_quizzes():
        body = request.get_json()
        if not body:
            abort(400)
        previous_question = body.get('previous_questions')
        quiz_categories = body.get('quiz_category')
        if not quiz_categories:
            abort(400)
        category_id = quiz_categories.get('id')
        if category_id == 0:
            questions = Question.query.all()
        else:
            questions = Question.query.filter(
                Question.category == category_id).all()
        current_questions = [question.format() for question in questions]
        if previous_question:
            current_questions = [question for question in current_questions if question.get(
                'id') not in previous_question]
        if len(current_questions) == 0:
            return jsonify({
                'success': False
            })
        question = random.choice(current_questions)
        return jsonify({
            'success': True,
            'question': question
    })

    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 400,
            'message': 'Bad request'
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'Resource not found'
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            'success': False,
            'error': 422,
            'message': 'Unprocessable'
        }), 422

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            'success': False,
            'error': 500,
            'message': 'Internal server error'
        }), 500

    return app
"""Local Flask application for repair requests."""

import argparse
import importlib.util
import secrets
from pathlib import Path

from flask import Flask, abort, render_template, request, session

from store import DEVICE_TYPES, PRIORITIES, STATUSES, initialize


def create_app(database=None):
    app = Flask(__name__)
    app.config.update(
        DATABASE=str(database or Path(__file__).parent / 'data' / 'requests.db'),
        SECRET_KEY=secrets.token_hex(32), MAX_CONTENT_LENGTH=32 * 1024,
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
    )
    initialize(app.config['DATABASE'])

    @app.before_request
    def protect_forms():
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(24)
        if request.method == 'POST':
            token = request.form.get('csrf_token', '')
            if not secrets.compare_digest(token, session['csrf_token']):
                abort(400, description='Форма устарела. Обновите страницу и повторите действие.')

    @app.context_processor
    def shared_context():
        return dict(device_types=DEVICE_TYPES, priorities=PRIORITIES, statuses=STATUSES,
                    csrf_token=session.get('csrf_token', ''),
                    has_create='creation.new_request' in app.view_functions)

    @app.template_filter('date_ru')
    def date_ru(value):
        from datetime import datetime
        return datetime.fromisoformat(value).strftime('%d.%m.%Y, %H:%M')

    # Each branch adds its own blueprint; either branch can run independently.
    for module in ('creation', 'management'):
        if importlib.util.find_spec(module):
            blueprint = __import__(module).blueprint
            app.register_blueprint(blueprint)

    if 'management.index' not in app.view_functions:
        @app.get('/')
        def index():
            return render_template('base_index.html')

    @app.errorhandler(400)
    @app.errorhandler(404)
    @app.errorhandler(413)
    def error_page(error):
        return render_template('error.html', error=error), error.code

    return app


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5050)
    args = parser.parse_args()
    create_app().run(host='127.0.0.1', port=args.port, debug=False)

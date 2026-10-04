from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from store import PRIORITIES, STATUSES, create_request, validate

blueprint = Blueprint('creation', __name__)


@blueprint.route('/requests/new', methods=['GET', 'POST'])
def new_request():
    values = dict(priority=PRIORITIES[0], status=STATUSES[0])
    errors = {}
    if request.method == 'POST':
        values, errors = validate(request.form)
        if not errors:
            request_id = create_request(current_app.config['DATABASE'], values)
            flash(f'Заявка № {request_id} создана.', 'success')
            if 'management.detail' in current_app.view_functions:
                return redirect(url_for('management.detail', request_id=request_id))
            return redirect('/')
    return render_template('new.html', values=values, errors=errors), 422 if errors else 200

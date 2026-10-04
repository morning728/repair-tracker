from math import ceil
from datetime import datetime

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for

from store import DEVICE_TYPES, STATUSES, connect, get_request, validate

blueprint = Blueprint('management', __name__)


def require_request(request_id):
    row = get_request(current_app.config['DATABASE'], request_id)
    if row is None:
        abort(404, description='Заявка не найдена.')
    return row


@blueprint.get('/requests/<int:request_id>')
def detail(request_id):
    return render_template('detail.html', row=require_request(request_id))


@blueprint.route('/requests/<int:request_id>/edit', methods=['GET', 'POST'])
def edit(request_id):
    values = dict(require_request(request_id))
    errors = {}
    if request.method == 'POST':
        values, errors = validate(request.form)
        if not errors:
            with connect(current_app.config['DATABASE']) as db:
                db.execute('''UPDATE requests SET client=:client,phone=:phone,
                    device=:device,device_type=:device_type,problem=:problem,
                    priority=:priority,status=:status,updated=:updated WHERE id=:id''',
                    {**values, 'updated': datetime.now().isoformat(timespec='seconds'), 'id': request_id})
            flash(f'Заявка № {request_id} обновлена.', 'success')
            return redirect(url_for('management.detail', request_id=request_id))
    return render_template('edit.html', values=values, errors=errors,
                           request_id=request_id), 422 if errors else 200


@blueprint.get('/')
def index():
    query = request.args.get('q', '').strip()[:150]
    status = request.args.get('status', '')
    device_type = request.args.get('device_type', '')
    if status and status not in STATUSES or device_type and device_type not in DEVICE_TYPES:
        abort(400, description='Некорректный фильтр.')
    with connect(current_app.config['DATABASE']) as db:
        all_rows = db.execute('SELECT * FROM requests ORDER BY id DESC').fetchall()
    rows = [r for r in all_rows if
            (not query or query.casefold() in ' '.join(str(r[k]) for k in
                ('id', 'client', 'phone', 'device', 'problem')).casefold())
            and (not status or r['status'] == status)
            and (not device_type or r['device_type'] == device_type)]
    pages = max(1, ceil(len(rows) / 15))
    page = min(max(1, request.args.get('page', 1, type=int)), pages)
    stats = {s: sum(r['status'] == s for r in all_rows) for s in STATUSES}
    return render_template('list.html', rows=rows[(page-1)*15:page*15], total=len(rows),
                           stats=stats, count=len(all_rows), page=page, pages=pages,
                           query=query, selected_status=status, selected_type=device_type)

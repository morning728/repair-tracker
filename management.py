from math import ceil

from flask import Blueprint, abort, current_app, render_template, request

from store import DEVICE_TYPES, STATUSES, connect

blueprint = Blueprint('management', __name__)


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

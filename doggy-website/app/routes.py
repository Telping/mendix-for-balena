from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from app import db
from app.models import (DiaryEntry, Media, Tag,
                        TrainingResource, ResourceCategory, ResourceTag,
                        TrainingProgram, WeeklyActivity,
                        Appointment, AppointmentType, RecurrenceFrequency)
from werkzeug.utils import secure_filename
import os
from datetime import datetime, time, date, timedelta
from dateutil.relativedelta import relativedelta

main = Blueprint('main', __name__)

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'heic'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}

def allowed_file(filename, file_type):
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    if file_type == 'image':
        return ext in ALLOWED_IMAGE_EXTENSIONS
    elif file_type == 'video':
        return ext in ALLOWED_VIDEO_EXTENSIONS
    return False


@main.route('/')
def index():
    entries = DiaryEntry.query.order_by(DiaryEntry.date.desc()).all()
    return render_template('index.html', entries=entries)


@main.route('/entry/new', methods=['GET', 'POST'])
def new_entry():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        date_str = request.form.get('date')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        location_name = request.form.get('location_name')
        tags_str = request.form.get('tags', '')

        # Parse date
        entry_date = datetime.fromisoformat(date_str) if date_str else datetime.utcnow()

        # Create entry
        entry = DiaryEntry(
            title=title,
            description=description,
            date=entry_date,
            latitude=float(latitude) if latitude else None,
            longitude=float(longitude) if longitude else None,
            location_name=location_name
        )

        # Handle tags
        if tags_str:
            tag_names = [t.strip() for t in tags_str.split(',') if t.strip()]
            for tag_name in tag_names:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                entry.tags.append(tag)

        db.session.add(entry)
        db.session.flush()  # Get entry.id

        # Handle file uploads
        files = request.files.getlist('media')
        upload_folder = os.path.join('app', 'static', 'uploads')

        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                # Add timestamp to avoid conflicts
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"

                # Determine media type
                if allowed_file(file.filename, 'image'):
                    media_type = 'image'
                elif allowed_file(file.filename, 'video'):
                    media_type = 'video'
                else:
                    continue

                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)

                # Save to database
                media = Media(
                    filename=filename,
                    media_type=media_type,
                    file_path=f'uploads/{filename}',
                    entry_id=entry.id
                )
                db.session.add(media)

        db.session.commit()
        flash('Diary entry created successfully!', 'success')
        return redirect(url_for('main.index'))

    return render_template('new_entry.html')


@main.route('/entry/<int:entry_id>')
def view_entry(entry_id):
    entry = DiaryEntry.query.get_or_404(entry_id)
    return render_template('view_entry.html', entry=entry)


@main.route('/entry/<int:entry_id>/delete', methods=['POST'])
def delete_entry(entry_id):
    entry = DiaryEntry.query.get_or_404(entry_id)

    # Delete associated media files
    upload_folder = os.path.join('app', 'static', 'uploads')
    for media in entry.media:
        file_path = os.path.join(upload_folder, media.filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    db.session.delete(entry)
    db.session.commit()
    flash('Diary entry deleted successfully!', 'success')
    return redirect(url_for('main.index'))


@main.route('/map')
def map_view():
    entries = DiaryEntry.query.filter(
        DiaryEntry.latitude.isnot(None),
        DiaryEntry.longitude.isnot(None)
    ).all()
    return render_template('map.html', entries=entries)


@main.route('/api/entries')
def api_entries():
    entries = DiaryEntry.query.order_by(DiaryEntry.date.desc()).all()
    return jsonify([entry.to_dict() for entry in entries])


@main.route('/uploads/<filename>')
def uploaded_file(filename):
    upload_folder = os.path.join('app', 'static', 'uploads')
    return send_from_directory(upload_folder, filename)


# ============================================
# TRAINING RESOURCES
# ============================================

# File type mappings for training resources
FILE_TYPE_MAPPING = {
    # Documents
    'pdf': 'document', 'doc': 'document', 'docx': 'document',
    'txt': 'document', 'rtf': 'document', 'odt': 'document',
    # Videos
    'mp4': 'video', 'mov': 'video', 'avi': 'video',
    'mkv': 'video', 'webm': 'video', 'wmv': 'video',
    # Images
    'jpg': 'image', 'jpeg': 'image', 'png': 'image',
    'gif': 'image', 'webp': 'image', 'heic': 'image', 'svg': 'image',
    # Spreadsheets
    'xls': 'spreadsheet', 'xlsx': 'spreadsheet', 'csv': 'spreadsheet', 'ods': 'spreadsheet',
    # Presentations
    'ppt': 'presentation', 'pptx': 'presentation', 'odp': 'presentation',
}


def get_file_type(filename):
    """Determine file type category from filename extension"""
    if '.' not in filename:
        return 'other', ''
    ext = filename.rsplit('.', 1)[1].lower()
    file_type = FILE_TYPE_MAPPING.get(ext, 'other')
    return file_type, ext


@main.route('/training/resources')
def training_resources():
    """List all training resources with optional filtering"""
    category_id = request.args.get('category', type=int)
    file_type = request.args.get('type')
    search = request.args.get('search', '')

    query = TrainingResource.query

    if category_id:
        query = query.filter(TrainingResource.categories.any(ResourceCategory.id == category_id))
    if file_type:
        query = query.filter(TrainingResource.file_type == file_type)
    if search:
        query = query.filter(
            db.or_(
                TrainingResource.title.ilike(f'%{search}%'),
                TrainingResource.description.ilike(f'%{search}%')
            )
        )

    resources = query.order_by(TrainingResource.created_at.desc()).all()
    categories = ResourceCategory.query.order_by(ResourceCategory.name).all()

    return render_template('training/resources.html',
                           resources=resources,
                           categories=categories,
                           selected_category=category_id,
                           selected_type=file_type,
                           search=search)


@main.route('/training/resources/new', methods=['GET', 'POST'])
def new_training_resource():
    """Upload a new training resource"""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category_ids = request.form.getlist('categories')
        tags_str = request.form.get('tags', '')
        file = request.files.get('file')

        if not file or not file.filename:
            flash('Please select a file to upload.', 'danger')
            return redirect(request.url)

        # Process file
        original_filename = file.filename
        filename = secure_filename(original_filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"

        file_type, file_extension = get_file_type(original_filename)

        # Save to training subfolder
        upload_folder = os.path.join('app', 'static', 'uploads', 'training')
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)

        # Get file size
        file_size = os.path.getsize(file_path)

        # Create resource
        resource = TrainingResource(
            title=title or original_filename,
            description=description,
            filename=filename,
            original_filename=original_filename,
            file_path=f'uploads/training/{filename}',
            file_type=file_type,
            file_extension=file_extension,
            file_size=file_size
        )

        # Add categories
        for cat_id in category_ids:
            category = ResourceCategory.query.get(cat_id)
            if category:
                resource.categories.append(category)

        # Handle tags
        if tags_str:
            tag_names = [t.strip() for t in tags_str.split(',') if t.strip()]
            for tag_name in tag_names:
                tag = ResourceTag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = ResourceTag(name=tag_name)
                    db.session.add(tag)
                resource.tags.append(tag)

        db.session.add(resource)
        db.session.commit()

        flash('Training resource uploaded successfully!', 'success')
        return redirect(url_for('main.training_resources'))

    categories = ResourceCategory.query.order_by(ResourceCategory.name).all()
    return render_template('training/resource_form.html',
                           resource=None,
                           categories=categories)


@main.route('/training/resources/<int:resource_id>')
def view_training_resource(resource_id):
    """View a training resource's details"""
    resource = TrainingResource.query.get_or_404(resource_id)
    return render_template('training/resource_view.html', resource=resource)


@main.route('/training/resources/<int:resource_id>/edit', methods=['GET', 'POST'])
def edit_training_resource(resource_id):
    """Edit a training resource's metadata"""
    resource = TrainingResource.query.get_or_404(resource_id)

    if request.method == 'POST':
        resource.title = request.form.get('title')
        resource.description = request.form.get('description')

        # Update categories
        resource.categories = []
        for cat_id in request.form.getlist('categories'):
            category = ResourceCategory.query.get(cat_id)
            if category:
                resource.categories.append(category)

        # Update tags
        resource.tags = []
        tags_str = request.form.get('tags', '')
        if tags_str:
            tag_names = [t.strip() for t in tags_str.split(',') if t.strip()]
            for tag_name in tag_names:
                tag = ResourceTag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = ResourceTag(name=tag_name)
                    db.session.add(tag)
                resource.tags.append(tag)

        db.session.commit()
        flash('Resource updated successfully!', 'success')
        return redirect(url_for('main.view_training_resource', resource_id=resource.id))

    categories = ResourceCategory.query.order_by(ResourceCategory.name).all()
    return render_template('training/resource_form.html',
                           resource=resource,
                           categories=categories)


@main.route('/training/resources/<int:resource_id>/delete', methods=['POST'])
def delete_training_resource(resource_id):
    """Delete a training resource and its file"""
    resource = TrainingResource.query.get_or_404(resource_id)

    # Delete the file
    file_path = os.path.join('app', 'static', resource.file_path)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(resource)
    db.session.commit()
    flash('Resource deleted successfully!', 'success')
    return redirect(url_for('main.training_resources'))


@main.route('/training/resources/<int:resource_id>/download')
def download_training_resource(resource_id):
    """Download a training resource file"""
    resource = TrainingResource.query.get_or_404(resource_id)
    directory = os.path.join('app', 'static', 'uploads', 'training')
    return send_from_directory(directory, resource.filename,
                               as_attachment=True,
                               download_name=resource.original_filename)


# ============================================
# RESOURCE CATEGORIES
# ============================================

@main.route('/training/categories')
def training_categories():
    """List all categories"""
    categories = ResourceCategory.query.order_by(ResourceCategory.name).all()
    return render_template('training/categories.html', categories=categories)


@main.route('/training/categories/new', methods=['GET', 'POST'])
def new_training_category():
    """Create a new category"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        color = request.form.get('color', '#8B4513')

        if ResourceCategory.query.filter_by(name=name).first():
            flash('A category with this name already exists.', 'danger')
            return redirect(request.url)

        category = ResourceCategory(name=name, description=description, color=color)
        db.session.add(category)
        db.session.commit()

        flash('Category created successfully!', 'success')
        return redirect(url_for('main.training_categories'))

    return render_template('training/category_form.html', category=None)


@main.route('/training/categories/<int:category_id>/edit', methods=['GET', 'POST'])
def edit_training_category(category_id):
    """Edit a category"""
    category = ResourceCategory.query.get_or_404(category_id)

    if request.method == 'POST':
        category.name = request.form.get('name')
        category.description = request.form.get('description')
        category.color = request.form.get('color', '#8B4513')
        db.session.commit()
        flash('Category updated successfully!', 'success')
        return redirect(url_for('main.training_categories'))

    return render_template('training/category_form.html', category=category)


@main.route('/training/categories/<int:category_id>/delete', methods=['POST'])
def delete_training_category(category_id):
    """Delete a category"""
    category = ResourceCategory.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted successfully!', 'success')
    return redirect(url_for('main.training_categories'))


# ============================================
# TRAINING PROGRAMS
# ============================================

@main.route('/training/programs')
def training_programs():
    """List all training programs"""
    status_filter = request.args.get('status')

    programs = TrainingProgram.query.order_by(TrainingProgram.start_date.desc()).all()

    # Filter by status after fetching (since status is computed)
    if status_filter:
        programs = [p for p in programs if p.status_label.lower() == status_filter.lower()]

    return render_template('training/programs.html', programs=programs)


@main.route('/training/programs/new', methods=['GET', 'POST'])
def new_training_program():
    """Create a new training program"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        start_date_str = request.form.get('start_date')
        is_ongoing = request.form.get('is_ongoing') == 'on'
        end_date_str = request.form.get('end_date')

        from datetime import date
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else date.today()
        end_date = None
        if not is_ongoing and end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        program = TrainingProgram(
            name=name,
            description=description,
            start_date=start_date,
            end_date=end_date,
            is_ongoing=is_ongoing,
            is_active=True
        )

        db.session.add(program)
        db.session.commit()

        flash('Training program created! Now add weekly activities.', 'success')
        return redirect(url_for('main.view_training_program', program_id=program.id))

    return render_template('training/program_form.html', program=None)


@main.route('/training/programs/<int:program_id>')
def view_training_program(program_id):
    """View a training program with its weekly schedule"""
    program = TrainingProgram.query.get_or_404(program_id)

    # Organize activities by day for the weekly view
    activities_by_day = {i: [] for i in range(7)}
    for activity in program.weekly_activities:
        activities_by_day[activity.day_of_week].append(activity)

    # Sort activities within each day by time
    for day in activities_by_day:
        activities_by_day[day].sort(key=lambda a: (a.time or time(23, 59)))

    day_names = WeeklyActivity.DAY_NAMES

    return render_template('training/program_view.html',
                           program=program,
                           activities_by_day=activities_by_day,
                           day_names=day_names)


@main.route('/training/programs/<int:program_id>/edit', methods=['GET', 'POST'])
def edit_training_program(program_id):
    """Edit a training program's details"""
    program = TrainingProgram.query.get_or_404(program_id)

    if request.method == 'POST':
        program.name = request.form.get('name')
        program.description = request.form.get('description')
        start_date_str = request.form.get('start_date')
        program.is_ongoing = request.form.get('is_ongoing') == 'on'
        end_date_str = request.form.get('end_date')

        from datetime import date
        if start_date_str:
            program.start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()

        if program.is_ongoing:
            program.end_date = None
        elif end_date_str:
            program.end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        db.session.commit()
        flash('Program updated successfully!', 'success')
        return redirect(url_for('main.view_training_program', program_id=program.id))

    return render_template('training/program_form.html', program=program)


@main.route('/training/programs/<int:program_id>/delete', methods=['POST'])
def delete_training_program(program_id):
    """Delete a training program and all its activities"""
    program = TrainingProgram.query.get_or_404(program_id)
    db.session.delete(program)
    db.session.commit()
    flash('Training program deleted successfully!', 'success')
    return redirect(url_for('main.training_programs'))


@main.route('/training/programs/<int:program_id>/toggle', methods=['POST'])
def toggle_training_program(program_id):
    """Toggle a program's active status"""
    program = TrainingProgram.query.get_or_404(program_id)
    program.is_active = not program.is_active
    db.session.commit()
    status = 'activated' if program.is_active else 'deactivated'
    flash(f'Program {status} successfully!', 'success')
    return redirect(url_for('main.view_training_program', program_id=program.id))


# ============================================
# WEEKLY ACTIVITIES
# ============================================

@main.route('/training/programs/<int:program_id>/activities/new', methods=['GET', 'POST'])
def new_weekly_activity(program_id):
    """Add a new weekly activity to a program"""
    program = TrainingProgram.query.get_or_404(program_id)

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        time_str = request.form.get('time')
        duration = request.form.get('duration_minutes')
        resource_ids = request.form.getlist('resources')
        is_recurring = request.form.get('is_recurring') == 'on'
        recurring_days = request.form.getlist('recurring_days')

        activity_time = None
        if time_str:
            activity_time = datetime.strptime(time_str, '%H:%M').time()

        # Get resources to link
        resources_to_link = []
        for res_id in resource_ids:
            resource = TrainingResource.query.get(res_id)
            if resource:
                resources_to_link.append(resource)

        # Determine which days to create activities for
        if is_recurring and recurring_days:
            days_to_create = [int(d) for d in recurring_days]
        else:
            day_of_week = request.form.get('day_of_week')
            days_to_create = [int(day_of_week)] if day_of_week else []

        # Create activity for each selected day
        activities_created = 0
        for day in days_to_create:
            activity = WeeklyActivity(
                name=name,
                description=description,
                day_of_week=day,
                time=activity_time,
                duration_minutes=int(duration) if duration else None,
                program_id=program.id
            )

            # Add resource references
            for resource in resources_to_link:
                activity.resources.append(resource)

            db.session.add(activity)
            activities_created += 1

        db.session.commit()

        if activities_created > 1:
            flash(f'{activities_created} activities added successfully!', 'success')
        else:
            flash('Activity added successfully!', 'success')
        return redirect(url_for('main.view_training_program', program_id=program.id))

    resources = TrainingResource.query.order_by(TrainingResource.title).all()
    day_names = WeeklyActivity.DAY_NAMES

    return render_template('training/activity_form.html',
                           program=program,
                           activity=None,
                           resources=resources,
                           day_names=day_names)


@main.route('/training/programs/<int:program_id>/activities/<int:activity_id>/edit', methods=['GET', 'POST'])
def edit_weekly_activity(program_id, activity_id):
    """Edit a weekly activity"""
    program = TrainingProgram.query.get_or_404(program_id)
    activity = WeeklyActivity.query.get_or_404(activity_id)

    if activity.program_id != program.id:
        flash('Activity not found in this program.', 'danger')
        return redirect(url_for('main.view_training_program', program_id=program.id))

    if request.method == 'POST':
        activity.name = request.form.get('name')
        activity.description = request.form.get('description')
        activity.day_of_week = int(request.form.get('day_of_week'))
        time_str = request.form.get('time')
        duration = request.form.get('duration_minutes')
        resource_ids = request.form.getlist('resources')

        activity.time = None
        if time_str:
            activity.time = datetime.strptime(time_str, '%H:%M').time()

        activity.duration_minutes = int(duration) if duration else None

        # Update resource references
        activity.resources = []
        for res_id in resource_ids:
            resource = TrainingResource.query.get(res_id)
            if resource:
                activity.resources.append(resource)

        db.session.commit()
        flash('Activity updated successfully!', 'success')
        return redirect(url_for('main.view_training_program', program_id=program.id))

    resources = TrainingResource.query.order_by(TrainingResource.title).all()
    day_names = WeeklyActivity.DAY_NAMES

    return render_template('training/activity_form.html',
                           program=program,
                           activity=activity,
                           resources=resources,
                           day_names=day_names)


@main.route('/training/programs/<int:program_id>/activities/<int:activity_id>/delete', methods=['POST'])
def delete_weekly_activity(program_id, activity_id):
    """Delete a weekly activity"""
    activity = WeeklyActivity.query.get_or_404(activity_id)

    if activity.program_id != program_id:
        flash('Activity not found in this program.', 'danger')
        return redirect(url_for('main.view_training_program', program_id=program_id))

    db.session.delete(activity)
    db.session.commit()
    flash('Activity deleted successfully!', 'success')
    return redirect(url_for('main.view_training_program', program_id=program_id))


# ============================================
# TRAINING API ENDPOINTS
# ============================================

@main.route('/api/training/resources')
def api_training_resources():
    """JSON API for training resources"""
    resources = TrainingResource.query.order_by(TrainingResource.created_at.desc()).all()
    return jsonify([r.to_dict() for r in resources])


@main.route('/api/training/programs')
def api_training_programs():
    """JSON API for training programs"""
    programs = TrainingProgram.query.order_by(TrainingProgram.start_date.desc()).all()
    return jsonify([p.to_dict() for p in programs])


@main.route('/api/training/programs/<int:program_id>/week')
def api_program_week(program_id):
    """Get program activities organized by day of week"""
    program = TrainingProgram.query.get_or_404(program_id)

    week_data = {}
    for i, day_name in enumerate(WeeklyActivity.DAY_NAMES):
        activities = program.get_activities_for_day(i)
        week_data[day_name] = [a.to_dict() for a in activities]

    return jsonify({
        'program': program.to_dict(),
        'week': week_data
    })


# ============================================
# APPOINTMENTS
# ============================================

def generate_recurring_appointments(parent_appointment, frequency, end_date):
    """Generate recurring appointment instances from a parent appointment"""
    appointments = []
    current_date = parent_appointment.date_time

    # Map frequency to relativedelta
    delta_map = {
        RecurrenceFrequency.WEEKLY: relativedelta(weeks=1),
        RecurrenceFrequency.MONTHLY: relativedelta(months=1),
        RecurrenceFrequency.EVERY_2_MONTHS: relativedelta(months=2),
        RecurrenceFrequency.EVERY_3_MONTHS: relativedelta(months=3),
        RecurrenceFrequency.EVERY_6_MONTHS: relativedelta(months=6),
        RecurrenceFrequency.YEARLY: relativedelta(years=1),
    }

    delta = delta_map.get(frequency)
    if not delta:
        return appointments

    # Generate appointments until end date
    current_date = current_date + delta  # Skip the first one (parent is already created)
    while current_date.date() <= end_date:
        child = Appointment(
            title=parent_appointment.title,
            appointment_type=parent_appointment.appointment_type,
            date_time=current_date,
            duration_minutes=parent_appointment.duration_minutes,
            location=parent_appointment.location,
            notes=parent_appointment.notes,
            reminder_minutes=parent_appointment.reminder_minutes,
            parent_appointment_id=parent_appointment.id
        )
        appointments.append(child)
        current_date = current_date + delta

    return appointments


@main.route('/appointments')
def appointments_list():
    """List all appointments with optional filtering"""
    appointment_type = request.args.get('type')
    status = request.args.get('status')  # upcoming, past, all
    show_cancelled = request.args.get('show_cancelled', 'false') == 'true'

    query = Appointment.query

    if appointment_type:
        query = query.filter(Appointment.appointment_type == appointment_type)

    if not show_cancelled:
        query = query.filter(Appointment.is_cancelled == False)

    if status == 'upcoming':
        query = query.filter(Appointment.date_time >= datetime.now())
    elif status == 'past':
        query = query.filter(Appointment.date_time < datetime.now())

    appointments = query.order_by(Appointment.date_time.desc()).all()

    return render_template('appointments/list.html',
                           appointments=appointments,
                           appointment_types=AppointmentType.CHOICES,
                           selected_type=appointment_type,
                           selected_status=status or 'all',
                           show_cancelled=show_cancelled)


@main.route('/appointments/new', methods=['GET', 'POST'])
def new_appointment():
    """Create a new appointment with optional recurrence"""
    if request.method == 'POST':
        title = request.form.get('title')
        appointment_type = request.form.get('appointment_type')
        date_str = request.form.get('date')
        time_str = request.form.get('time')
        duration = request.form.get('duration_minutes')
        location = request.form.get('location')
        notes = request.form.get('notes')
        reminder = request.form.get('reminder_minutes')
        recurrence = request.form.get('recurrence_frequency')
        recurrence_end_str = request.form.get('recurrence_end_date')

        # Parse date and time
        if date_str and time_str:
            date_time = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
        elif date_str:
            date_time = datetime.strptime(date_str, '%Y-%m-%d')
        else:
            flash('Please provide a date for the appointment.', 'danger')
            return redirect(request.url)

        # Create the appointment
        appointment = Appointment(
            title=title,
            appointment_type=appointment_type,
            date_time=date_time,
            duration_minutes=int(duration) if duration else 60,
            location=location,
            notes=notes,
            reminder_minutes=int(reminder) if reminder else None,
            recurrence_frequency=recurrence if recurrence != RecurrenceFrequency.NONE else None
        )

        db.session.add(appointment)
        db.session.flush()  # Get the ID

        # Generate recurring appointments if needed
        if recurrence and recurrence != RecurrenceFrequency.NONE and recurrence_end_str:
            recurrence_end = datetime.strptime(recurrence_end_str, '%Y-%m-%d').date()
            appointment.recurrence_end_date = recurrence_end
            child_appointments = generate_recurring_appointments(
                appointment, recurrence, recurrence_end
            )
            for child in child_appointments:
                db.session.add(child)

        db.session.commit()

        count = 1 + (len(child_appointments) if 'child_appointments' in dir() else 0)
        if count > 1:
            flash(f'{count} appointments created successfully!', 'success')
        else:
            flash('Appointment created successfully!', 'success')

        return redirect(url_for('main.appointments_list'))

    return render_template('appointments/form.html',
                           appointment=None,
                           appointment_types=AppointmentType.CHOICES,
                           recurrence_options=RecurrenceFrequency.CHOICES)


@main.route('/appointments/<int:appointment_id>')
def view_appointment(appointment_id):
    """View appointment details"""
    appointment = Appointment.query.get_or_404(appointment_id)
    return render_template('appointments/view.html',
                           appointment=appointment,
                           appointment_types=AppointmentType.CHOICES)


@main.route('/appointments/<int:appointment_id>/edit', methods=['GET', 'POST'])
def edit_appointment(appointment_id):
    """Edit an appointment"""
    appointment = Appointment.query.get_or_404(appointment_id)

    if request.method == 'POST':
        appointment.title = request.form.get('title')
        appointment.appointment_type = request.form.get('appointment_type')
        date_str = request.form.get('date')
        time_str = request.form.get('time')

        if date_str and time_str:
            appointment.date_time = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
        elif date_str:
            appointment.date_time = datetime.strptime(date_str, '%Y-%m-%d')

        duration = request.form.get('duration_minutes')
        appointment.duration_minutes = int(duration) if duration else 60
        appointment.location = request.form.get('location')
        appointment.notes = request.form.get('notes')
        reminder = request.form.get('reminder_minutes')
        appointment.reminder_minutes = int(reminder) if reminder else None

        db.session.commit()
        flash('Appointment updated successfully!', 'success')
        return redirect(url_for('main.view_appointment', appointment_id=appointment.id))

    return render_template('appointments/form.html',
                           appointment=appointment,
                           appointment_types=AppointmentType.CHOICES,
                           recurrence_options=RecurrenceFrequency.CHOICES)


@main.route('/appointments/<int:appointment_id>/delete', methods=['POST'])
def delete_appointment(appointment_id):
    """Delete an appointment with options for recurring series"""
    appointment = Appointment.query.get_or_404(appointment_id)
    delete_option = request.form.get('delete_option', 'single')

    if delete_option == 'all' and appointment.parent_appointment_id:
        # Delete entire series (parent and all children)
        parent = Appointment.query.get(appointment.parent_appointment_id)
        if parent:
            db.session.delete(parent)
        flash('Entire appointment series deleted.', 'success')
    elif delete_option == 'future' and appointment.parent_appointment_id:
        # Delete this and all future appointments in the series
        Appointment.query.filter(
            Appointment.parent_appointment_id == appointment.parent_appointment_id,
            Appointment.date_time >= appointment.date_time
        ).delete()
        flash('This and all future appointments deleted.', 'success')
    else:
        # Delete just this appointment
        db.session.delete(appointment)
        flash('Appointment deleted.', 'success')

    db.session.commit()
    return redirect(url_for('main.appointments_list'))


@main.route('/appointments/<int:appointment_id>/toggle', methods=['POST'])
def toggle_appointment(appointment_id):
    """Toggle appointment completion status"""
    appointment = Appointment.query.get_or_404(appointment_id)
    appointment.is_completed = not appointment.is_completed
    db.session.commit()
    status = 'completed' if appointment.is_completed else 'reopened'
    flash(f'Appointment marked as {status}.', 'success')
    return redirect(url_for('main.view_appointment', appointment_id=appointment.id))


@main.route('/appointments/<int:appointment_id>/cancel', methods=['POST'])
def cancel_appointment(appointment_id):
    """Cancel an appointment"""
    appointment = Appointment.query.get_or_404(appointment_id)
    appointment.is_cancelled = True
    db.session.commit()
    flash('Appointment cancelled.', 'success')
    return redirect(url_for('main.view_appointment', appointment_id=appointment.id))


# ============================================
# CALENDAR
# ============================================

def generate_training_events(start_date, end_date):
    """Generate calendar events from training program weekly activities"""
    events = []
    programs = TrainingProgram.query.filter(TrainingProgram.is_active == True).all()

    for program in programs:
        # Determine the effective date range
        prog_start = max(program.start_date, start_date)
        if program.end_date:
            prog_end = min(program.end_date, end_date)
        else:
            prog_end = end_date

        if prog_start > prog_end:
            continue

        # Generate events for each day in range
        current = prog_start
        while current <= prog_end:
            day_of_week = current.weekday()
            activities = program.get_activities_for_day(day_of_week)

            for activity in activities:
                event_time = activity.time or time(9, 0)
                event_datetime = datetime.combine(current, event_time)

                events.append({
                    'id': f'training_{activity.id}_{current.isoformat()}',
                    'title': f'{activity.name}',
                    'start': event_datetime.isoformat(),
                    'end': (event_datetime + timedelta(minutes=activity.duration_minutes or 30)).isoformat() if activity.duration_minutes else None,
                    'color': '#007bff',  # Blue for training
                    'type': 'training',
                    'url': url_for('main.view_training_program', program_id=program.id),
                    'extendedProps': {
                        'program': program.name,
                        'description': activity.description
                    }
                })

            current += timedelta(days=1)

    return events


@main.route('/calendar')
def calendar_view():
    """Main calendar view"""
    return render_template('calendar/calendar.html',
                           appointment_types=AppointmentType.CHOICES)


@main.route('/api/calendar/events')
def api_calendar_events():
    """Get calendar events for FullCalendar"""
    start_str = request.args.get('start')
    end_str = request.args.get('end')

    if start_str:
        start_date = datetime.fromisoformat(start_str.replace('Z', '')).date()
    else:
        start_date = date.today() - timedelta(days=30)

    if end_str:
        end_date = datetime.fromisoformat(end_str.replace('Z', '')).date()
    else:
        end_date = date.today() + timedelta(days=60)

    events = []

    # 1. Diary entries (brown)
    diary_entries = DiaryEntry.query.filter(
        DiaryEntry.date >= datetime.combine(start_date, time.min),
        DiaryEntry.date <= datetime.combine(end_date, time.max)
    ).all()

    for entry in diary_entries:
        events.append({
            'id': f'diary_{entry.id}',
            'title': entry.title,
            'start': entry.date.isoformat(),
            'allDay': True,
            'color': '#8B4513',  # Brown for diary
            'type': 'diary',
            'url': url_for('main.view_entry', entry_id=entry.id)
        })

    # 2. Training activities (blue)
    training_events = generate_training_events(start_date, end_date)
    events.extend(training_events)

    # 3. Appointments (colored by type)
    appointments = Appointment.query.filter(
        Appointment.date_time >= datetime.combine(start_date, time.min),
        Appointment.date_time <= datetime.combine(end_date, time.max),
        Appointment.is_cancelled == False
    ).all()

    type_colors = {t[0]: t[2] for t in AppointmentType.CHOICES}

    for appt in appointments:
        end_time = None
        if appt.duration_minutes:
            end_time = (appt.date_time + timedelta(minutes=appt.duration_minutes)).isoformat()

        events.append({
            'id': f'appointment_{appt.id}',
            'title': appt.title,
            'start': appt.date_time.isoformat(),
            'end': end_time,
            'color': type_colors.get(appt.appointment_type, '#6c757d'),
            'type': 'appointment',
            'url': url_for('main.view_appointment', appointment_id=appt.id),
            'extendedProps': {
                'appointmentType': appt.appointment_type,
                'location': appt.location,
                'completed': appt.is_completed
            }
        })

    return jsonify(events)


@main.route('/api/calendar/day/<date_str>')
def api_calendar_day(date_str):
    """Get all events for a specific day"""
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    result = {
        'date': date_str,
        'diary_entries': [],
        'training_activities': [],
        'appointments': []
    }

    # Diary entries
    entries = DiaryEntry.query.filter(
        db.func.date(DiaryEntry.date) == target_date
    ).all()
    result['diary_entries'] = [e.to_dict() for e in entries]

    # Training activities (from active programs)
    day_of_week = target_date.weekday()
    programs = TrainingProgram.query.filter(
        TrainingProgram.is_active == True,
        TrainingProgram.start_date <= target_date,
        db.or_(
            TrainingProgram.end_date >= target_date,
            TrainingProgram.end_date.is_(None)
        )
    ).all()

    for program in programs:
        activities = program.get_activities_for_day(day_of_week)
        for activity in activities:
            result['training_activities'].append({
                **activity.to_dict(),
                'program_name': program.name
            })

    # Appointments
    appointments = Appointment.query.filter(
        db.func.date(Appointment.date_time) == target_date,
        Appointment.is_cancelled == False
    ).order_by(Appointment.date_time).all()
    result['appointments'] = [a.to_dict() for a in appointments]

    return jsonify(result)
